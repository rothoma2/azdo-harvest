# Quick Start Guide

## Installation & Setup

1. **Install dependencies**:
   ```bash
   poetry install
   ```

2. **Set up authentication**:
   ```bash
   # Create a .env file from the example
   cp .env.example .env
   
   # Edit .env and add your credentials
   # Or export directly:
   export AZDO_PAT="your-personal-access-token"
   ```

3. **Verify installation**:
   ```bash
   poetry run azdo-harvest --help
   ```

## Usage Examples

### Search Everything (Summary)
```bash
poetry run azdo-harvest search "TODO" --organization myorg --project myproject
```

Output:
```
✓ Found 5 repositories and 23 files
```

### Search with Verbose Output
```bash
poetry run azdo-harvest search "config" --organization myorg --project MyProject --verbose
```

### Download Files
```bash
poetry run azdo-harvest search "file:Dockerfile" \
  --organization myorg \
  --project myproject \
  --download \
  --output-dir ./dockerfiles
```

This will:
- Search for all Dockerfiles
- Download them in parallel (5 workers)
- Save as `{repo}__{filename}__{hash}.{ext}` format
  - Example: `docker-test__Dockerfile__a4b3c5d7`
  - Hash is first 8 chars of SHA256
- Show progress bar

### Search Specific Project
```bash
poetry run azdo-harvest search "config" --organization myorg --project MyProject
```

### Search Only Files
```bash
poetry run azdo-harvest search "function main" --organization myorg --project myproject --file-only
```

### Search Only Repositories
```bash
poetry run azdo-harvest search "api" --organization myorg --project myproject --repo-only
```

### Limit Results
```bash
poetry run azdo-harvest search "test" --organization myorg --project myproject --limit 20
```

## Testing

Run the test suite:
```bash
poetry install --with dev
poetry run pytest
```

Run with coverage:
```bash
poetry run pytest --cov=azdo_harvest --cov-report=html
```

## Building

Build the package:
```bash
poetry build
```

This creates distributable files in the `dist/` directory.

## Installing the CLI Globally

After building, you can install it globally:
```bash
pip install dist/azdo_harvest-0.1.0-py3-none-any.whl
```

Then use it without `poetry run`:
```bash
azdo-harvest search "term" --organization myorg
```
