"""CLI interface for Azure DevOps Harvester."""
import click
from rich.console import Console
from rich.table import Table
from azdo_harvest.search import AzureDevOpsSearcher

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Azure DevOps Harvester - Search repositories and files in Azure DevOps."""
    pass


@main.command()
@click.argument('search_term')
@click.option('--organization', '-o', required=True, help='Azure DevOps organization name')
@click.option('--project', '-p', required=True, help='Specific project to search (optional)')
@click.option('--pat', '--token', envvar='AZDO_PAT', required=True, 
              help='Personal Access Token (can also use AZDO_PAT env var)')
@click.option('--file-only', is_flag=True, help='Search only in file contents')
@click.option('--repo-only', is_flag=True, help='Search only repository names')
@click.option('--limit', '-l', default=100, type=int, help='Maximum number of results')
def search(search_term, organization, project, pat, file_only, repo_only, limit):
    """Search for repositories and files in Azure DevOps.
    
    SEARCH_TERM: The term to search for in repositories and files.
    
    Example:
        azdo-harvest search "TODO" --organization myorg --pat xxxxx
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
        
        display_results(results)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise click.Abort()


def display_results(results):
    """Display search results in a formatted table."""
    
    # Display repository results
    if results.get('repositories'):
        console.print("\n[bold cyan]═══ Repository Results ═══[/bold cyan]\n")
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
        console.print(f"\n[bold]Found {len(results['repositories'])} repositories[/bold]\n")
    
    # Display file results
    if results.get('files'):
        console.print("\n[bold cyan]═══ File Results ═══[/bold cyan]\n")
        file_table = Table(show_header=True, header_style="bold magenta")
        file_table.add_column("Repository", style="cyan")
        file_table.add_column("File Path", style="yellow")
        file_table.add_column("Branch", style="green")
        
        for file_result in results['files']:
            file_table.add_row(
                file_result.get('repository', 'N/A'),
                file_result.get('path', 'N/A'),
                file_result.get('branch', 'N/A')
            )
        
        console.print(file_table)
        console.print(f"\n[bold]Found {len(results['files'])} file matches[/bold]\n")
    
    if not results.get('repositories') and not results.get('files'):
        console.print("[yellow]No results found.[/yellow]")


if __name__ == '__main__':
    main()
