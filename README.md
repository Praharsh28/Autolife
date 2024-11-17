# AutoLife Media Processing Application

## Continuous Integration Status
[![AutoLife Tests](https://github.com/{YOUR_USERNAME}/autolife/actions/workflows/test.yml/badge.svg)](https://github.com/{YOUR_USERNAME}/autolife/actions)
[![codecov](https://codecov.io/gh/{YOUR_USERNAME}/autolife/branch/main/graph/badge.svg)](https://codecov.io/gh/{YOUR_USERNAME}/autolife)

## Automated Testing

This project uses GitHub Actions for continuous integration and automated testing. Tests are run:
- On every push to `main` and `develop` branches
- On every pull request to these branches
- Every 6 hours automatically

### Test Reports
After each test run, you can find:
1. HTML test reports
2. Code coverage reports
3. Detailed test logs

These are available in the "Actions" tab of the GitHub repository under each workflow run.

### Local Development
To run tests locally:
```bash
pytest -v -n auto --dist=loadscope -m "not gpu"
```

## Setup Instructions
[Previous README content...]
