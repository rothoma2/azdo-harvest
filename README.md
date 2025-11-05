# Azure DevOps Harvester

A CLI tool and Python library to search repositories and files in Azure DevOps organizations, with built-in support for downloading matched files.

## Features

- 🔍 Search across all repositories in an organization
- 📁 Search file contents using Azure DevOps Code Search API
- 🎯 Filter by specific projects
- 📥 Download matched files using Git Items API
- 📊 Beautiful formatted output with Rich
- ⚡ Fast and efficient API usage
- 🐍 Python library for programmatic access

## Installation

Install the package using Poetry:

```bash
poetry install
```

## Configuration

The tool requires a Personal Access Token (PAT) from Azure DevOps with at least **Code (Read)** permissions.

### Creating a PAT

1. Go to Azure DevOps: `https://dev.azure.com/{your-org}`
2. Click on User Settings (top right) → Personal Access Tokens
3. Create a new token with **Code (Read)** scope
4. Copy the token (you won't see it again!)

### Setting up authentication

You can provide the PAT in two ways:

1. **Environment variable** (recommended):
   ```bash
   export AZDO_PAT="your-personal-access-token"
   ```

2. **Command-line option**:
   ```bash
   azdo-harvest search "term" --organization myorg --project myproject
   ```

## Usage

### Basic Search (Summary Mode)

By default, the CLI shows only a summary of results:

```bash
azdo-harvest search "file:Dockerfile" --organization myorg --project myproject
```

Output:
```
Searching for: file:Dockerfile
Organization: myorg
Project: myproject

✓ Found 2 repositories and 2 files
```

### Verbose Mode

Use `--verbose` or `-v` to see detailed tables:

```bash
azdo-harvest search "TODO" --organization myorg --project myproject --verbose
```

### Download Files

Use `--download` or `-d` to automatically download all found files:

```bash
azdo-harvest search "file:Dockerfile" --organization myorg --project myproject --download
```

Files are downloaded with naming format: `{repository}__{filename}__{hash}`
- Example: `docker-test__Dockerfile__a4b3c5d7.txt`
- Hash is the first 8 characters of SHA256 hash of file content
- Ensures unique filenames even for files with same name

Specify custom output directory:

```bash
azdo-harvest search "file:*.py" -o myorg -p myproject --download --output-dir ./my-files
```

**Features:**
- ⚡ Parallel downloads with 5 concurrent workers
- 📊 Progress bar showing download status
- ✓ Success/failure summary
- 🎯 Unique file naming: `repo__filename__hash.ext`
- 🔐 SHA256 hash for file verification

### Search Options

Search in a specific project:

```bash
azdo-harvest search "configuration" --organization myorg --project MyProject
```

### Search only in file contents

```bash
azdo-harvest search "function" --organization myorg --project myproject --file-only
```

### Search only repository names

```bash
azdo-harvest search "api" --organization myorg --project myproject --repo-only
```

### Limit results

```bash
azdo-harvest search "test" --organization myorg --project myproject --limit 50
```

### Complete example with all options

```bash
export AZDO_PAT="your-personal-access-token"
azdo-harvest search "file:Dockerfile" \
  --organization myorg \
  --project MyProject \
  --download \
  --output-dir ./dockerfiles \
  --verbose
```

## Command Reference

```
azdo-harvest search SEARCH_TERM [OPTIONS]

Arguments:
  SEARCH_TERM  The term to search for in repositories and files

Options:
  -o, --organization TEXT  Azure DevOps organization name [required]
  -p, --project TEXT       Project name [required]
  --pat TEXT              Personal Access Token (or set AZDO_PAT env var) [required]
  --file-only             Search only in file contents
  --repo-only             Search only repository names
  -l, --limit INTEGER     Maximum number of results [default: 100]
  -d, --download          Download all found files
  --output-dir PATH       Directory to save downloaded files [default: ./downloads]
  -v, --verbose           Show detailed results tables
  --help                  Show this message and exit
```

## Python Library Usage

The package can also be used as a Python library:

```python
import os
from azdo_harvest import AzureDevOpsSearcher

# Initialize
organization = "your-org"
project = "your-project"
pat = os.environ['AZDO_PAT']
searcher = AzureDevOpsSearcher(organization, project, pat)

# Search for files
results = searcher.search(
    search_term="file:Dockerfile",
    project=project,
    search_files=True,
    search_repos=False,
    max_results=10
)

# Access file results (FileResult objects)
for file in results['files']:
    print(f"Found: {file.repository}:{file.filepath}")
    print(f"Branch: {file.branch}")
    print(f"Download URL: {file.get_download_url()}")
    
# Download files
output_path = searcher.downloader.download_file(
    results['files'][0],
    output_dir="./downloads",
    preserve_structure=True
)

# Or get file content without downloading
content = searcher.downloader.get_file_content(results['files'][0])
```

### FileResult Object

Each file search result is a `FileResult` object with the following attributes:

- `repository`: Repository name
- `repository_id`: Repository ID (for API calls)
- `project`: Project name
- `project_id`: Project ID
- `filepath`: Full path to the file
- `branch`: Branch name (e.g., "main")
- `commit_id`: Commit hash
- `organization`: Organization name
- `filename`: Just the filename

Methods:
- `get_download_url()`: Generate the Azure DevOps API URL for downloading
- `get_download_params()`: Get parameters dict for download API call

## Development

### Running locally

```bash
poetry run azdo-harvest search "term" --organization myorg --project myproject
```

### Running tests

```bash
poetry run pytest
```

### Examples

See the `examples/` directory for more usage examples:

- `basic_usage.py`: Basic search examples
- `download_files.py`: Download files from search results

Run examples:
```bash
export AZDO_PAT="your-token"
export AZDO_ORG="your-org"
export AZDO_PROJECT="your-project"
python examples/download_files.py
```

## Requirements

- Python >= 3.12
- Azure DevOps organization with Code Search enabled
- Personal Access Token with Code (Read) permissions

## License

MIT
