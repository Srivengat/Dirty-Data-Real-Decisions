"""Robust data loading and schema validation module."""

import csv
from pathlib import Path
from typing import List, Optional, Sequence, Union

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Canonical required schema columns for case management exports
DEFAULT_REQUIRED_COLUMNS: List[str] = [
    "case_id",
    "client_name",
    "category",
    "priority",
    "intake_date",
    "closure_date",
    "status",
]

# Supported encodings attempted in fallback order
SUPPORTED_ENCODINGS: Sequence[str] = (
    "utf-8",
    "utf-8-sig",
    "latin1",
    "cp1252",
    "iso-8859-1",
)


class DataLoadingError(Exception):
    """Base exception for data loading failures."""


class SchemaValidationError(DataLoadingError):
    """Raised when the dataset fails schema or column contract validation."""


class EncodingDetectionError(DataLoadingError):
    """Raised when file cannot be decoded using any supported encoding."""


class DataLoader:
    """Production-grade CSV data loader supporting dynamic encoding and delimiter detection."""

    def __init__(
        self,
        required_columns: Optional[Sequence[str]] = None,
        encodings: Sequence[str] = SUPPORTED_ENCODINGS,
    ) -> None:
        """Initialize DataLoader with schema rules and encoding list.

        Args:
            required_columns: Column names required to be present in the loaded dataset.
            encodings: Sequence of character encodings to attempt in priority order.
        """
        self.required_columns = (
            list(required_columns) if required_columns is not None else DEFAULT_REQUIRED_COLUMNS
        )
        self.encodings = encodings

    def detect_encoding(self, file_path: Union[str, Path]) -> str:
        """Detect a working encoding by sequentially decoding a binary sample.

        Args:
            file_path: Path to the target CSV file.

        Returns:
            str: The first compatible encoding name.

        Raises:
            FileNotFoundError: If file_path does not exist.
            EncodingDetectionError: If no supported encoding successfully decodes the file.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Source file not found: {path.resolve()}")

        with open(path, "rb") as f:
            raw_bytes = f.read(65536)  # Read 64KB sample

        for encoding in self.encodings:
            try:
                raw_bytes.decode(encoding)
                logger.debug(f"Detected valid encoding '{encoding}' for {path.name}")
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue

        raise EncodingDetectionError(
            f"Failed to decode '{path.name}' using supported encodings: {self.encodings}"
        )

    def detect_delimiter(self, file_path: Union[str, Path], encoding: str) -> str:
        """Detect the CSV delimiter character using csv.Sniffer with heuristic fallback.

        Args:
            file_path: Path to the target CSV file.
            encoding: Character encoding to read the file sample with.

        Returns:
            str: Detected delimiter character (e.g. ',', ';', '\t', '|').
        """
        path = Path(file_path)
        with open(path, "r", encoding=encoding, errors="replace") as f:
            sample_lines = [f.readline() for _ in range(10)]
            sample_text = "".join([line for line in sample_lines if line.strip()])

        if not sample_text:
            logger.warning(f"File {path.name} is empty; defaulting delimiter to ','")
            return ","

        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample_text, delimiters=[",", ";", "\t", "|"])
            delimiter = dialect.delimiter
            logger.debug(f"csv.Sniffer detected delimiter '{delimiter}' for {path.name}")
            return delimiter
        except csv.Error:
            # Fallback heuristic: count candidates in the header line
            header = sample_lines[0] if sample_lines else ""
            counts = {sep: header.count(sep) for sep in [",", ";", "\t", "|"]}
            best_sep = max(counts, key=counts.get) if max(counts.values(), default=0) > 0 else ","
            logger.warning(
                f"Sniffer failed on {path.name}; heuristic fallback selected delimiter '{best_sep}'"
            )
            return best_sep

    def validate_schema(
        self, df: pd.DataFrame, file_name: str = "dataset"
    ) -> None:
        """Validate that all required columns are present in the DataFrame.

        Args:
            df: Loaded pandas DataFrame.
            file_name: Identifier of the source dataset for log messaging.

        Raises:
            SchemaValidationError: If one or more required columns are missing.
        """
        existing_columns = set(df.columns.str.strip())
        missing_columns = [col for col in self.required_columns if col not in existing_columns]

        if missing_columns:
            msg = (
                f"Schema validation failed for '{file_name}'. Missing required columns: "
                f"{missing_columns}. Existing columns: {list(df.columns)}"
            )
            logger.error(msg)
            raise SchemaValidationError(msg)

        logger.info(
            f"Schema validation passed for '{file_name}' ({len(self.required_columns)} required columns verified)."
        )

    def load(
        self,
        file_path: Union[str, Path],
        validate: bool = True,
    ) -> pd.DataFrame:
        """Load, decode, parse, and validate a CSV dataset into a pandas DataFrame.

        Args:
            file_path: Path to the target CSV file.
            validate: Whether to run schema validation on the loaded DataFrame.

        Returns:
            pd.DataFrame: Cleanly loaded DataFrame.

        Raises:
            FileNotFoundError: If the file does not exist.
            DataLoadingError: If parsing fails or data is corrupt.
            SchemaValidationError: If required columns are missing and validate is True.
        """
        path = Path(file_path)
        logger.info(f"Initiating data load for: {path.resolve()}")

        encoding = self.detect_encoding(path)
        delimiter = self.detect_delimiter(path, encoding)

        try:
            # Read CSV with determined encoding and delimiter
            df = pd.read_csv(
                path,
                encoding=encoding,
                sep=delimiter,
                dtype=str,  # Read raw as strings to preserve fidelity for audit pipeline
                keep_default_na=False,  # Retain raw empty strings so profiling detects exact missingness
            )
            logger.info(
                f"Successfully parsed '{path.name}' [Encoding: {encoding}, Delimiter: '{delimiter}'] "
                f"— Shape: {df.shape[0]} rows, {df.shape[1]} columns."
            )
        except Exception as exc:
            msg = f"Failed to parse CSV file '{path.name}': {str(exc)}"
            logger.error(msg, exc_info=True)
            raise DataLoadingError(msg) from exc

        if validate:
            self.validate_schema(df, file_name=path.name)

        return df


def load_raw_data(
    file_path: Union[str, Path] = "data/raw/case_management_raw.csv",
    required_columns: Optional[Sequence[str]] = None,
    validate: bool = True,
) -> pd.DataFrame:
    """Convenience function to load raw dataset with standard configuration.

    Args:
        file_path: Path to the raw CSV file.
        required_columns: Optional custom list of required columns.
        validate: Whether to validate required schema columns.

    Returns:
        pd.DataFrame: Loaded raw DataFrame.
    """
    loader = DataLoader(required_columns=required_columns)
    return loader.load(file_path=file_path, validate=validate)
