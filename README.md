# Azure DevOps Harvester

[![PyPI version](https://badge.fury.io/py/azdo-harvest.svg)](https://badge.fury.io/py/azdo-harvest)
[![Python Version](https://img.shields.io/pypi/pyversions/azdo-harvest.svg)](https://pypi.org/project/azdo-harvest/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A CLI tool and Python library to search across Azure Devops repositories, with built-in support for downloading matched files.
It utilizes Azure Devops APIs for Search, and Retrieval. 

## Features

- 🔍 Search across all repositories in an organization
- 📁 Search file contents using Azure DevOps Code Search API
- 🎯 Filter by specific projects
- 📥 Download matched files using Git Items API with hash-based naming
- 📊 Beautiful formatted output with Rich
- ⚡ Parallel downloads with 5 concurrent workers
- 🔐 SHA256 hash verification for downloaded files
- 🐍 Python library for programmatic access

## Installation

### From PyPI (Recommended)

```bash
pip install azdo-harvest
```

### From Source

```bash
git clone https://github.com/rothoma2/azdo-harvest.git
cd azdo-harvest
poetry install
```

## Configuration

The tool supports either a Personal Access Token (PAT) or a short-lived
Microsoft Entra token obtained from Azure CLI. The Azure CLI option is useful
for tenants where PAT creation is disabled.

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

#### Azure CLI authentication

Install the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli),
sign in with an account that can access the Azure DevOps organization, and use
the `az-cli` authentication method:

```bash
az login
azdo-harvest search "file:Dockerfile" \
  --organization myorg \
  --project myproject \
  --auth-method az-cli
```

The application runs `az account get-access-token` for the Azure DevOps
resource and sends the resulting token as a Bearer token. Tokens are cached
until one minute before expiry and then refreshed automatically. No PAT is
stored or required in this mode.

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

### Verbose Mode

Use `--verbose` or `-v` to see detailed tables:

```bash
azdo-harvest search "TODO" --organization myorg --project myproject --verbose
```


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

When the limit is greater than 1,000, searches are requested in 1,000-result
pages using Azure DevOps' `$skip` parameter. For example:

```bash
azdo-harvest search "TODO" \
  --organization myorg \
  --project myproject \
  --limit 9000 \
  --download
```

Azure DevOps may enforce a hard 1,000-result boundary for Code Search and
reject pages beyond it. In that case, repeat the search with repository or
path filters to split the result set into smaller searches.

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

**Features:**
- ⚡ Parallel downloads with 5 concurrent workers
- 📊 Progress bar showing download status
- ✓ Success/failure summary
- 🎯 Unique file naming: `repo__filename__hash.ext`
- 🔐 SHA256 hash for file verification


## Command Reference

```
azdo-harvest search SEARCH_TERM [OPTIONS]

Arguments:
  SEARCH_TERM  The term to search for in repositories and files

Options:
  -o, --organization TEXT  Azure DevOps organization name [required]
  -p, --project TEXT       Project name [required]
  --pat TEXT              Personal Access Token (or set AZDO_PAT env var)
  --auth-method [pat|az-cli]  Authentication method (or AZDO_AUTH_METHOD) [default: pat]
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

To use Azure CLI authentication from Python:

```python
from azdo_harvest import AzureDevOpsSearcher

searcher = AzureDevOpsSearcher(
    "your-org", "your-project", use_azure_cli=True
)
results = searcher.search("file:Dockerfile", project="your-project")
```

### List repositories

After running `az login`, list repositories visible to the current account and
write their names to a text file:

```bash
python -m examples.list_repositories \
  --organization myorg \
  --output repositories.txt
```

Use `--project MyProject` to limit the inventory to one project. The utility
prints the total count and writes one repository name per line.

## Requirements

- Python >= 3.12
- Azure DevOps organization with Code Search enabled
- Personal Access Token with Code (Read) permissions, or Azure CLI access to
  the organization

## License

MIT - See [LICENSE](LICENSE) file for details

## Author

**rothoma2** - [GitHub](https://github.com/rothoma2)

## Acknowledgments

- Built with [Poetry](https://python-poetry.org/)
- CLI built with [Click](https://click.palletsprojects.com/)
- Beautiful output with [Rich](https://rich.readthedocs.io/)
- Published to [PyPI](https://pypi.org/project/azdo-harvest/)
