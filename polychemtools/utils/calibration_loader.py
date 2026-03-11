"""
Calibration loading utilities for GPC analysis

This module provides functions to load calibration data from JSON files,
enabling clean access to stored calibrations without sys.path manipulation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Union, Any


class CalibrationError(Exception):
    """Base exception for calibration-related errors"""
    pass


class CalibrationNotFoundError(CalibrationError):
    """Raised when a requested calibration name is not found in the file"""
    pass


class CalibrationFileError(CalibrationError):
    """Raised when the calibration file cannot be read or parsed"""
    pass


class InvalidCalibrationError(CalibrationError):
    """Raised when calibration data has invalid structure"""
    pass


def load_calibration(filepath: str, calibration_name: str) -> Dict[str, Any]:
    """
    Load a calibration by name from a JSON file

    Parameters
    ----------
    filepath : str
        Path to the JSON file containing calibration data
    calibration_name : str
        Name of the calibration to load from the file

    Returns
    -------
    calibration : dict
        Dictionary containing 'type' and 'params' keys for the calibration

    Raises
    ------
    CalibrationFileError
        If the file cannot be read or is not valid JSON
    CalibrationNotFoundError
        If the specified calibration name is not found in the file
    InvalidCalibrationError
        If the calibration data structure is invalid

    Examples
    --------
    >>> calibration = load_calibration('calibrations.json', 'sample_calibration')
    >>> print(calibration)
    {'type': 'cubic', 'params': [-0.001701334, 0.064349247, -1.197289570, 14.035147838]}
    """
    # Convert to Path object for better path handling
    calibration_file = Path(filepath)

    # Check if file exists
    if not calibration_file.exists():
        raise CalibrationFileError(
            f"Calibration file not found: {filepath}"
        )

    # Load JSON file
    try:
        with calibration_file.open('r') as f:
            calibrations = json.load(f)
    except json.JSONDecodeError as e:
        raise CalibrationFileError(
            f"Failed to parse JSON from {filepath}: {e}"
        )
    except Exception as e:
        raise CalibrationFileError(
            f"Failed to read calibration file {filepath}: {e}"
        )

    # Check if calibration name exists
    if calibration_name not in calibrations:
        available = ', '.join(calibrations.keys())
        raise CalibrationNotFoundError(
            f"Calibration '{calibration_name}' not found in {filepath}. "
            f"Available calibrations: {available}"
        )

    calibration = calibrations[calibration_name]

    # Validate calibration structure
    if not isinstance(calibration, dict):
        raise InvalidCalibrationError(
            f"Calibration '{calibration_name}' must be a dictionary, "
            f"got {type(calibration).__name__}"
        )

    if 'type' not in calibration:
        raise InvalidCalibrationError(
            f"Calibration '{calibration_name}' missing required 'type' key"
        )

    if 'params' not in calibration:
        raise InvalidCalibrationError(
            f"Calibration '{calibration_name}' missing required 'params' key"
        )

    if not isinstance(calibration['params'], list):
        raise InvalidCalibrationError(
            f"Calibration '{calibration_name}' params must be a list, "
            f"got {type(calibration['params']).__name__}"
        )

    return calibration


def parse_calibration_string(calibration_string: str) -> tuple[str, str]:
    """
    Parse a calibration string in format 'filepath:calibration_name'

    Parameters
    ----------
    calibration_string : str
        String in format 'filepath:calibration_name'

    Returns
    -------
    filepath : str
        Path to the calibration file
    calibration_name : str
        Name of the calibration to load

    Raises
    ------
    ValueError
        If the string is not in the correct format

    Examples
    --------
    >>> filepath, name = parse_calibration_string('../data/calibrations.json:sample_calibration')
    >>> print(filepath, name)
    ../data/calibrations.json sample_calibration
    """
    if ':' not in calibration_string:
        raise ValueError(
            f"Calibration string must be in format 'filepath:calibration_name', "
            f"got '{calibration_string}'"
        )

    parts = calibration_string.split(':', 1)
    if len(parts) != 2:
        raise ValueError(
            f"Calibration string must have exactly one ':' separator, "
            f"got '{calibration_string}'"
        )

    filepath, calibration_name = parts

    if not filepath.strip():
        raise ValueError("Filepath cannot be empty")

    if not calibration_name.strip():
        raise ValueError("Calibration name cannot be empty")

    return filepath.strip(), calibration_name.strip()


def resolve_calibration(
    calibration: Union[dict, str]
) -> Dict[str, Any]:
    """
    Resolve a calibration from either a dict or a filepath string

    This is a convenience function that handles both formats:
    - dict: Returns as-is (backward compatibility)
    - str: Parses as 'filepath:calibration_name' and loads from JSON

    Parameters
    ----------
    calibration : dict or str
        Either a calibration dict with 'type' and 'params' keys,
        or a string in format 'filepath:calibration_name'

    Returns
    -------
    calibration : dict
        Dictionary containing 'type' and 'params' keys

    Raises
    ------
    ValueError
        If calibration is neither dict nor str
    CalibrationFileError
        If loading from file fails
    CalibrationNotFoundError
        If calibration name not found in file
    InvalidCalibrationError
        If calibration structure is invalid

    Examples
    --------
    >>> # Dict format (backward compatible)
    >>> cal = resolve_calibration({'type': 'cubic', 'params': [1, 2, 3, 4]})

    >>> # String format (new)
    >>> cal = resolve_calibration('../data/calibrations.json:sample_calibration')
    """
    if isinstance(calibration, dict):
        # Backward compatibility: dict passed directly
        return calibration
    elif isinstance(calibration, str):
        # New format: parse and load from file
        filepath, calibration_name = parse_calibration_string(calibration)
        return load_calibration(filepath, calibration_name)
    else:
        raise ValueError(
            f"Calibration must be either a dict or a string, "
            f"got {type(calibration).__name__}"
        )
