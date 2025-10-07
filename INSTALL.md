# fnerd-falconpy Installation Guide

## Prerequisites

- Python 3.10 or higher (tested up to 3.13)
- pip package manager
- CrowdStrike Falcon API credentials

## Installation Steps

### 1. Clone or Download the Package

```bash
# If you have the package directory
cd /path/to/falcon_client
```

### 2. Create a Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install the Package

#### For Development (Editable Install)
```bash
pip install -e .
```

#### For Production
```bash
pip install .
```

### 4. Verify Installation

```bash
# Run the test script
python test_installation.py

# Or check CLI
falcon-client --help
```

## Configuration

### 1. Set Environment Variables

Create a `.env` file in your working directory:

```env
# Required
CLIENT_ID=your-falcon-client-id
CLIENT_SECRET=your-falcon-client-secret

# Optional for S3 uploads
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
```

### 2. Test Connection

```bash
# Test with a simple command
falcon-client browser_history -n 1 -d YOUR_HOSTNAME -u YOUR_USERNAME
```

## Common Installation Issues

### ImportError: No module named 'falconpy'

```bash
pip install crowdstrike-falconpy
```

### ImportError: No module named 'pkg_resources'

```bash
pip install setuptools
```

### falcon-client: command not found

The command may not be in your PATH. Try:

```bash
# Use Python module directly
python -m falcon_client.cli --help

# Or reinstall with pip
pip install -e .
```

### KAPE Resources Not Found

Ensure the KAPE directory was copied correctly:

```bash
ls falcon_client/resources/kape/
```

If missing, copy the Kape directory from the original project.

## Testing the Installation

### 1. Import Test

```python
python -c "from falcon_client import FalconForensicOrchestrator; print('Import successful')"
```

### 2. CLI Test

```bash
# Should show help message
falcon-client --help

# Should list subcommands
falcon-client kape --help
falcon-client browser_history --help
```

### 3. Example Usage

```python
# Run the example script
python example_usage.py
```

## Next Steps

1. Review the main [README.md](README.md) for usage examples
2. Check module-specific README files in each directory
3. Set up your environment variables
4. Try collecting from a test host

## Package Structure

After installation, you should have:

```
falcon_client/
├── __init__.py
├── orchestrator.py
├── orchestrator_optimized.py
├── core/
├── api/
├── managers/
├── collectors/
├── utils/
├── cli/
└── resources/
    ├── kape/
    └── deploy_kape.ps1
```

## Development Setup

For contributing or modifying the package:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests (when available)
pytest

# Format code
black falcon_client/

# Check code quality
flake8 falcon_client/
pylint falcon_client/
```

## Troubleshooting

If you encounter issues:

1. Check Python version: `python --version` (must be 3.10+)
2. Update pip: `pip install --upgrade pip`
3. Clear pip cache: `pip cache purge`
4. Check all dependencies: `pip list`
5. Review error messages in debug mode: `--log-level DEBUG`

For additional help, see the main documentation or submit an issue.