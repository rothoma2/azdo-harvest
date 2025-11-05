#!/usr/bin/env python3
"""Example script showing how to use the Azure DevOps Harvester library."""

import os
from azdo_harvest import AzureDevOpsSearcher


def main():
    """Run example searches."""
    # Get credentials from environment
    organization = os.environ.get('AZDO_ORG', 'your-org-name')
    project = os.environ.get('AZDO_PROJECT', 'your-project-name')
    pat = os.environ.get('AZDO_PAT')
    
    if not pat:
        print("Error: AZDO_PAT environment variable not set")
        print("Set it with: export AZDO_PAT='your-token'")
        return
    
    # Create searcher instance
    searcher = AzureDevOpsSearcher(organization, project, pat)
    
    # Example 1: Search for files with specific filename
    print("=" * 60)
    print("Example 1: Search for Dockerfile")
    print("=" * 60)
    results = searcher.search(
        search_term="file:Dockerfile",
        project=project,
        search_files=True,
        search_repos=False,
        max_results=10
    )
    
    print(f"\nFound {len(results['files'])} Dockerfile(s)")
    for file in results['files']:
        print(f"\n  File: {file}")
        print(f"  Repository: {file.repository}")
        print(f"  Project: {file.project}")
        print(f"  Path: {file.filepath}")
        print(f"  Branch: {file.branch}")
        print(f"  Download URL: {file.get_download_url()}")
    
    # Example 2: Download a file
    if results['files']:
        print("\n" + "=" * 60)
        print("Example 2: Download first file")
        print("=" * 60)
        file_to_download = results['files'][0]
        
        try:
            # Download to current directory
            output_path = searcher.downloader.download_file(
                file_to_download,
                output_dir="./downloads",
                preserve_structure=True
            )
            print(f"Downloaded to: {output_path}")
        except Exception as e:
            print(f"Error downloading: {e}")
    
    # Example 3: Get file content without downloading
    if results['files']:
        print("\n" + "=" * 60)
        print("Example 3: Get file content (first 500 chars)")
        print("=" * 60)
        file_to_read = results['files'][0]
        
        try:
            content = searcher.downloader.get_file_content(file_to_read)
            print(f"Content of {file_to_read.filepath}:")
            print("-" * 60)
            print(content[:500])
            if len(content) > 500:
                print("... (truncated)")
        except Exception as e:
            print(f"Error getting content: {e}")
    
    # Example 4: Search for TODO comments
    print("\n" + "=" * 60)
    print("Example 4: Search for TODO comments")
    print("=" * 60)
    results = searcher.search(
        search_term="TODO",
        project=project,
        search_files=True,
        search_repos=False,
        max_results=5
    )
    
    for file in results['files']:
        print(f"  - {file.repository}: {file.filepath}")


if __name__ == '__main__':
    main()
