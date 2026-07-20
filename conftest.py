# conftest.py — root-level pytest configuration
#
# Placing conftest.py at the project root ensures that pytest adds this
# directory to sys.path automatically.  This allows all test modules to use
# absolute imports like `from backend.app.services.xxx import yyy` without
# any additional path manipulation.
#
# Works in conjunction with the [tool.pytest.ini_options] section in
# pyproject.toml which sets pythonpath = ["."].
