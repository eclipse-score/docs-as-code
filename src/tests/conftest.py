def pytest_addoption(parser):
    """Add custom command line options to pytest"""
    parser.addoption(
        "--repo-tests",
        action="store",
        default=None,
        help="Comma separated string of ConsumerRepo's name tests to run",
    )
    parser.addoption(
        "--keep-temp",
        action="store_true",
        default=False,
        help="Keep temporary files in cache directory",
    )
