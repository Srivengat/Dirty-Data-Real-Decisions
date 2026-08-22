"""Unit tests for Module 1 Project Setup."""

import subprocess
import sys
from pathlib import Path

from src.utils.logger import get_logger, setup_logging


def test_directory_structure() -> None:
    """Verify that all required project directories exist."""
    required_dirs = [
        Path("data/raw"),
        Path("data/cleaned"),
        Path("data/logs"),
        Path("reports/figures"),
        Path("reports/exports"),
        Path("notebooks"),
        Path("src/analysis"),
        Path("src/cleaning"),
        Path("src/data"),
        Path("src/profiling"),
        Path("src/quality"),
        Path("src/visualization"),
        Path("src/utils"),
        Path("tests"),
    ]
    for directory in required_dirs:
        assert directory.exists(), f"Missing required directory: {directory}"
        assert directory.is_dir(), f"Expected a directory: {directory}"


def test_required_metadata_files() -> None:
    """Verify required top-level documentation and configuration files exist."""
    required_files = [
        Path("requirements.txt"),
        Path(".gitignore"),
        Path("PRD.md"),
        Path("AGENTS.md"),
        Path("main.py"),
        Path("data/raw/case_management_raw.csv"),
    ]
    for file_path in required_files:
        assert file_path.exists(), f"Missing required file: {file_path}"
        assert file_path.is_file(), f"Expected a file: {file_path}"


def test_logger_initialization() -> None:
    """Verify centralized logger configuration and retrieval."""
    setup_logging()
    logger = get_logger("test_module")
    assert logger is not None
    assert logger.name == "test_module"


def test_cli_help_execution() -> None:
    """Verify that main.py executes cleanly with --help."""
    result = subprocess.run(
        [sys.executable, "main.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"main.py --help failed: {result.stderr}"
    assert "dirty-data-pipeline" in result.stdout
