# Contributing to Paint Robot

Thank you for your interest in contributing to the Paint Robot project!

## How to Contribute

1. **Fork the repository** on GitHub
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** with clear, descriptive commits
4. **Write or update tests** for your changes
5. **Run tests locally**: `pytest`
6. **Submit a pull request** with a clear description of the changes

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/paint-bot.git
   cd paint-bot
   ```

2. Install in development mode:
   ```bash
   pip install -e ".[dev,docs]"
   ```

3. Run tests:
   ```bash
   pytest
   ```

4. Check code style:
   ```bash
   black --check .
   flake8 paintbot tests
   isort --check-only .
   ```

5. Format code:
   ```bash
   black .
   isort .
   ```

## Code Standards

- Follow PEP 8 style guide
- Use type hints where possible
- Add docstrings to all functions and classes
- Write tests for new features
- Update documentation as needed

## Reporting Issues

When reporting an issue, please include:
- Python version
- OS and version
- Steps to reproduce
- Expected vs. actual behavior
- Any relevant error messages

## Documentation

To build documentation locally:

```bash
cd docs
make html
```

Then open `_build/html/index.html` in your browser.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
