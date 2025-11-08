"""CLI interface for Azure DevOps Harvester."""
import click
import hashlib
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
)
from azdo_harvest.search import AzureDevOpsSearcher
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Azure DevOps Harvester - Search repos and files in Azure DevOps."""
    pass


@main.command()
@click.argument('search_term')
@click.option(
    '--organization', '-o', required=True,
    help='Azure DevOps organization name'
)
@click.option(
    '--project', '-p', required=True,
    help='Specific project to search (optional)'
)
@click.option(
    '--pat', '--token', envvar='AZDO_PAT', required=True,
    help='Personal Access Token (can also use AZDO_PAT env var)'
)
@click.option(
    '--file-only', is_flag=True, help='Search only in file contents'
)
@click.option(
    '--repo-only', is_flag=True, help='Search only repository names'
)
@click.option(
    '--limit', '-l', default=100, type=int,
    help='Maximum number of results'
)
@click.option(
    '--download', '-d', is_flag=True, help='Download all found files'
)
@click.option(
    '--output-dir', default='./downloads',
    help='Directory to save downloaded files'
)
@click.option('--verbose', '-v', is_flag=True, help='Show detailed results')
def search(search_term, organization, project, pat, file_only, repo_only,
           limit, download, output_dir, verbose):
    """Search for repositories and files in Azure DevOps.

    SEARCH_TERM: The term to search for in repositories and files.

    Example:
        azdo-harvest search "TODO" --organization myorg --pat xxxxx
        azdo-harvest search "file:Dockerfile" -o myorg -p myproject --download
    """
    console.print(f"[bold blue]Searching for:[/bold blue] {search_term}")
    console.print(f"[bold blue]Organization:[/bold blue] {organization}")
    if project:
        console.print(f"[bold blue]Project:[/bold blue] {project}")

    searcher = AzureDevOpsSearcher(organization, project, pat)

    try:
        with console.status("[bold green]Searching Azure DevOps..."):
            results = searcher.search(
                search_term=search_term,
                project=project,
                search_files=not repo_only,
                search_repos=not file_only,
                max_results=limit
            )

        display_results(results, verbose=verbose)

        # Download files if requested
        if download and results.get('files'):
            download_files_parallel(searcher, results['files'], output_dir)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


def display_results(results, verbose=False):
    """Display search results in a formatted table."""

    # Summary counts
    repo_count = len(results.get('repositories', []))
    file_count = len(results.get('files', []))

    console.print()
    console.print(
        f"[bold green]✓[/bold green] Found [bold]{repo_count}[/bold] "
        f"repositories and [bold]{file_count}[/bold] files"
    )
    console.print()

    # Only show detailed tables if verbose mode is enabled
    if verbose:
        # Display repository results
        if results.get('repositories'):
            console.print(
                "\n[bold cyan]═══ Repository Results ═══[/bold cyan]\n"
            )
            repo_table = Table(show_header=True, header_style="bold magenta")
            repo_table.add_column("Repository", style="cyan")
            repo_table.add_column("Project", style="green")
            repo_table.add_column("URL", style="blue")

            for repo in results['repositories']:
                repo_table.add_row(
                    repo.get('name', 'N/A'),
                    repo.get('project', 'N/A'),
                    repo.get('url', 'N/A')
                )

            console.print(repo_table)
            console.print(
                f"\n[bold]Found {len(results['repositories'])} "
                f"repositories[/bold]\n"
            )

        # Display file results (now FileResult objects)
        if results.get('files'):
            console.print("\n[bold cyan]═══ File Results ═══[/bold cyan]\n")
            file_table = Table(show_header=True, header_style="bold magenta")
            file_table.add_column("Repository", style="cyan")
            file_table.add_column("File Path", style="yellow")
            file_table.add_column("Branch", style="green")

            for file_result in results['files']:
                # FileResult objects have attributes, not dict keys
                file_table.add_row(
                    file_result.repository,
                    file_result.filepath,
                    file_result.branch
                )

            console.print(file_table)
            console.print(
                f"\n[bold]Found {len(results['files'])} "
                f"file matches[/bold]\n"
            )

    if repo_count == 0 and file_count == 0:
        console.print("[yellow]No results found.[/yellow]")


def download_files_parallel(searcher, file_results, output_dir):
    """Download files in parallel using ThreadPoolExecutor.

    Args:
        searcher: AzureDevOpsSearcher instance with downloader
        file_results: List of FileResult objects
        output_dir: Directory to save files
    """
    console.print(
        f"\n[bold cyan]Downloading {len(file_results)} files to "
        f"{output_dir}...[/bold cyan]\n"
    )

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    downloaded = []
    failed = []

    def download_single_file(file_result):
        """Download a single file with custom naming including hash."""
        try:
            # Download to temporary location first
            url = file_result.get_download_url()

            import requests
            response = requests.get(
                url,
                headers=searcher.downloader.headers,
                timeout=30
            )
            response.raise_for_status()

            content = response.text
            file_hash = hashlib.sha256(
                content.encode('utf-8')
            ).hexdigest()
            hash_prefix = file_hash[:8]
            safe_repo = file_result.repository.replace('/', '_')
            filename = file_result.filename.replace('/', '_')

            if '.' in filename:
                name_part, ext_part = filename.rsplit('.', 1)
                custom_filename = (
                    f"{safe_repo}__{name_part}__"
                    f"{hash_prefix}.{ext_part}"
                )
            else:
                custom_filename = (
                    f"{safe_repo}__{filename}__{hash_prefix}"
                )

            file_path = Path(output_dir) / custom_filename
            file_path.write_text(content, encoding='utf-8')

            return (file_result, str(file_path), hash_prefix, None)
        except Exception as e:
            return (file_result, None, None, str(e))

    # Use progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Downloading...", total=len(file_results))

        # Download with 5 parallel workers
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(download_single_file, fr): fr
                for fr in file_results
            }

            for future in as_completed(futures):
                file_result, output_path, file_hash, error = future.result()

                if error:
                    failed.append((file_result, error))
                else:
                    downloaded.append((file_result, output_path, file_hash))

                progress.update(task, advance=1)

    # Display summary
    console.print()
    console.print(
        f"[bold green]✓[/bold green] Successfully downloaded: "
        f"[bold]{len(downloaded)}[/bold] files"
    )
    if failed:
        console.print(
            f"[bold red]✗[/bold red] Failed: "
            f"[bold]{len(failed)}[/bold] files"
        )

    # Show downloaded files
    if downloaded:
        console.print("\n[bold cyan]Downloaded files:[/bold cyan]")
        for file_result, path, file_hash in downloaded:
            console.print(
                f"  [green]✓[/green] {Path(path).name} "
                f"[dim](hash: {file_hash})[/dim]"
            )

    # Show errors if any
    if failed:
        console.print("\n[bold red]Failed downloads:[/bold red]")
        for file_result, error in failed[:5]:  # Show first 5 errors
            console.print(
                f"  [red]✗[/red] {file_result.filename}: {error}"
            )
        if len(failed) > 5:
            console.print(
                f"  ... and {len(failed) - 5} more errors"
            )

    console.print()


if __name__ == '__main__':
    main()
