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

### Search Everything
```bash
poetry run azdo-harvest search "TODO" --organization myorg
```

### Search Specific Project
```bash
poetry run azdo-harvest search "config" --organization myorg --project MyProject
```

### Search Only Files
```bash
poetry run azdo-harvest search "function main" --organization myorg --file-only
```

### Search Only Repositories
```bash
poetry run azdo-harvest search "api" --organization myorg --repo-only
```

### Limit Results
```bash
poetry run azdo-harvest search "test" --organization myorg --limit 20
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
