## Python Code Standards (Priority: High)

- **Type annotations**: All parameters and return types (use `-> None` for no return)
- **Logging**:
  - Import `logging` and create `logger = logging.getLogger(__name__)` at module top
- **Formatting**: Run `ruff format` after editing files
- **Test structure**: Add empty `__init__.py` to new test subdirectories
- **Docstrings**:
  - Add docstrings in accordance with PEP-0257 (https://peps.python.org/pep-0257/)
  - Packages, modules, classes, methods, and functions MUST have docstrings
  - Business-specific, complex, or otherwise non-obvious code SHOULD have docstrings
