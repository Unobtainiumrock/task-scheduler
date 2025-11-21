# Code Coverage Setup Guide

## Local Testing

Run tests with coverage:

```bash
# Run tests and generate coverage report
pytest --cov=scheduler --cov=timer --cov-report=term-missing --cov-report=html

# View HTML coverage report
# Open htmlcov/index.html in your browser
```

## Codecov Integration

### Step 1: Sign up for Codecov

1. Go to [codecov.io](https://codecov.io)
2. Sign in with your GitHub account
3. Authorize Codecov to access your repositories
4. Add your repository: `Unobtainiumrock/task-scheduler`

### Step 2: Get Your Codecov Token

1. In Codecov dashboard, go to Settings → General
2. Copy your repository upload token (you'll need this for manual uploads)

### Step 3: Upload Coverage Reports

#### Option A: Using Codecov Uploader (Recommended)

Install the codecov uploader:

```bash
pip install codecov
```

After running tests, upload coverage:

```bash
# Run tests with coverage
pytest --cov=scheduler --cov=timer --cov-report=xml

# Upload to codecov
codecov -t YOUR_CODECOV_TOKEN
```

#### Option B: Using curl (Alternative)

```bash
# After running pytest with --cov-report=xml
curl -s https://codecov.io/bash | bash -s - -t YOUR_CODECOV_TOKEN
```

### Step 4: GitHub Actions (Automatic Upload)

Create `.github/workflows/coverage.yml`:

```yaml
name: Coverage

on:
  push:
    branches: [ nicholas, main, master ]
  pull_request:
    branches: [ nicholas, main, master ]

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests with coverage
        run: |
          pytest --cov=scheduler --cov=timer --cov-report=xml --cov-report=term
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
```

Then add `CODECOV_TOKEN` to your GitHub repository secrets:
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `CODECOV_TOKEN`
4. Value: Your Codecov token from Step 2

## Current Coverage

- **scheduler.py**: 72% coverage
- **timer.py**: 29% coverage
- **Overall**: 34% coverage

## Improving Coverage

To increase coverage, add more tests for:
- Error handling paths
- Edge cases
- Integration scenarios
- Notification interactions
- File I/O operations

