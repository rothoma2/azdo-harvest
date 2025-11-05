# Azure DevOps Harvester

A CLI tool to search repositories and files in Azure DevOps organizations.

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
   azdo-harvest search "term" --organization myorg --pat "your-token"
   ```

## Usage

### Basic Search

Search for a term across all repositories and files:

```bash
azdo-harvest search "TODO" --organization myorg
```

### Search in a specific project

```bash
azdo-harvest search "configuration" --organization myorg --project MyProject
```

### Search only in file contents

```bash
azdo-harvest search "function" --organization myorg --file-only
```

### Search only repository names

```bash
azdo-harvest search "api" --organization myorg --repo-only
```

### Limit results

```bash
azdo-harvest search "test" --organization myorg --limit 50
```

### Complete example with all options

```bash
export AZDO_PAT="your-personal-access-token"
azdo-harvest search "database" \
  --organization myorg \
  --project MyProject \
  --limit 100
```

## Command Reference

```
azdo-harvest search SEARCH_TERM [OPTIONS]

Arguments:
  SEARCH_TERM  The term to search for in repositories and files

Options:
  -o, --organization TEXT  Azure DevOps organization name [required]
  -p, --project TEXT       Specific project to search (optional)
  --pat TEXT              Personal Access Token (or set AZDO_PAT env var) [required]
  --file-only             Search only in file contents
  --repo-only             Search only repository names
  -l, --limit INTEGER     Maximum number of results [default: 100]
  --help                  Show this message and exit
```

## Development

### Running locally

```bash
poetry run azdo-harvest search "term" --organization myorg
```

### Running tests

```bash
poetry run pytest
```

## Features

- 🔍 Search across all repositories in an organization
- 📁 Search file contents using Azure DevOps Code Search API
- 🎯 Filter by specific projects
- 📊 Beautiful formatted output with Rich
- 🔐 Secure authentication with Personal Access Tokens
- ⚡ Fast and efficient API usage

## Requirements

- Python >= 3.12
- Azure DevOps organization with Code Search enabled
- Personal Access Token with Code (Read) permissions

## License

MIT
