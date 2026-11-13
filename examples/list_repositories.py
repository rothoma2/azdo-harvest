"""List Azure DevOps repositories using the current Azure CLI login."""

import argparse

from azdo_harvest.repositories import list_repositories, write_repository_names


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List Azure DevOps Git repositories and save their names."
    )
    parser.add_argument("--organization", "-o", required=True)
    parser.add_argument(
        "--project", "-p",
        help="Limit the list to one project; omit for the whole organization.",
    )
    parser.add_argument(
        "--output", "-f", default="repositories.txt",
        help="Text file to write (default: repositories.txt).",
    )
    args = parser.parse_args()

    repositories = list_repositories(args.organization, args.project)
    write_repository_names(repositories, args.output)
    scope = f" project {args.project!r}" if args.project else " organization-wide"
    print(f"Found {len(repositories)} repositories{scope}.")
    print(f"Repository names written to {args.output}")


if __name__ == "__main__":
    main()
