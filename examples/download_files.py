#!/usr/bin/env python3
"""Example: Download files from Azure DevOps search results."""

import os
from azdo_harvest import AzureDevOpsSearcher


def main():
    """Search for Dockerfiles and download them."""
    # Setup
    organization = os.environ.get('AZDO_ORG', 'rothoma2-sandbox')
    project = os.environ.get('AZDO_PROJECT', 'NotOne')
    pat = os.environ.get('AZDO_PAT')
    
    if not pat:
        print("Error: AZDO_PAT environment variable not set")
        return
    
    # Initialize searcher
    searcher = AzureDevOpsSearcher(organization, project, pat)
    
    # Search for Dockerfiles
    print("Searching for Dockerfiles...")
    results = searcher.search(
        search_term="file:Dockerfile",
        project=project,
        search_files=True,
        search_repos=False,
        max_results=10
    )
    
    if not results['files']:
        print("No Dockerfiles found.")
        return
    
    print(f"\nFound {len(results['files'])} Dockerfile(s):\n")
    
    # Display all results with download information
    for i, file_result in enumerate(results['files'], 1):
        print(f"{i}. {file_result}")
        print(f"   Repository: {file_result.repository}")
        print(f"   Repository ID: {file_result.repository_id}")
        print(f"   Project: {file_result.project}")
        print(f"   Project ID: {file_result.project_id}")
        print(f"   Path: {file_result.filepath}")
        print(f"   Branch: {file_result.branch}")
        print(f"   Commit: {file_result.commit_id}")
        print(f"   Organization: {file_result.organization}")
        print(f"   Filename: {file_result.filename}")
        print(f"   Download URL: {file_result.get_download_url()}")
        print()
    
    # Download all files
    print("\nDownloading files...")
    downloaded = searcher.downloader.download_files(
        results['files'],
        output_dir="./downloads",
        preserve_structure=True
    )
    
    print("\nDownload Summary:")
    for source, dest in downloaded.items():
        if dest:
            print(f"✓ {source} → {dest}")
        else:
            print(f"✗ {source} → Failed")
    
    # Show file contents
    print("\n" + "=" * 70)
    print("First Dockerfile content:")
    print("=" * 70)
    try:
        content = searcher.downloader.get_file_content(results['files'][0])
        print(content)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
