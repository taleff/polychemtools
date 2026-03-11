#!/usr/bin/env python3
"""
Migration script to convert Python calibration files to JSON format

This script helps migrate from the old Python dictionary format to the new
JSON format for storing GPC calibrations.

Usage
-----
python migrate_calibrations.py input.py output.json

The script will:
1. Import all calibration dictionaries from the Python file
2. Validate their structure
3. Write them to a JSON file in the new format

Example
-------
If your calibrations.py file contains:

    sample_calibration = {
        'type': 'cubic',
        'params': [-0.001701334, 0.064349247, -1.197289570, 14.035147838]
    }

    old_calibration = {
        'type': 'linear',
        'params': [1.5, 2.3]
    }

The output JSON will be:

    {
        "sample_calibration": {
            "type": "cubic",
            "params": [-0.001701334, 0.064349247, -1.197289570, 14.035147838]
        },
        "old_calibration": {
            "type": "linear",
            "params": [1.5, 2.3]
        }
    }
"""

import sys
import json
import importlib.util
from pathlib import Path
from typing import Dict, Any


def validate_calibration(name: str, calibration: Any) -> None:
    """
    Validate that a calibration has the correct structure

    Parameters
    ----------
    name : str
        Name of the calibration (for error messages)
    calibration : Any
        The calibration object to validate

    Raises
    ------
    ValueError
        If the calibration structure is invalid
    """
    if not isinstance(calibration, dict):
        raise ValueError(
            f"Calibration '{name}' must be a dictionary, "
            f"got {type(calibration).__name__}"
        )

    if 'type' not in calibration:
        raise ValueError(
            f"Calibration '{name}' missing required 'type' key"
        )

    if 'params' not in calibration:
        raise ValueError(
            f"Calibration '{name}' missing required 'params' key"
        )

    if not isinstance(calibration['params'], (list, tuple)):
        raise ValueError(
            f"Calibration '{name}' params must be a list or tuple, "
            f"got {type(calibration['params']).__name__}"
        )

    # Convert params to list if it's a tuple
    if isinstance(calibration['params'], tuple):
        calibration['params'] = list(calibration['params'])


def extract_calibrations_from_module(module_path: Path) -> Dict[str, Dict]:
    """
    Import a Python module and extract all calibration dictionaries

    Parameters
    ----------
    module_path : Path
        Path to the Python file containing calibrations

    Returns
    -------
    calibrations : dict
        Dictionary mapping calibration names to calibration dictionaries

    Raises
    ------
    ImportError
        If the module cannot be imported
    ValueError
        If no calibrations are found or if calibrations are invalid
    """
    # Import the module dynamically
    spec = importlib.util.spec_from_file_location("calibrations_module", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Extract all calibration dictionaries
    calibrations = {}
    for name in dir(module):
        # Skip private/special attributes
        if name.startswith('_'):
            continue

        # Get the attribute
        obj = getattr(module, name)

        # Check if it looks like a calibration (dict with 'type' and 'params')
        if isinstance(obj, dict) and 'type' in obj and 'params' in obj:
            validate_calibration(name, obj)
            calibrations[name] = obj

    if not calibrations:
        raise ValueError(
            f"No calibrations found in {module_path}. "
            "Calibrations must be dictionaries with 'type' and 'params' keys."
        )

    return calibrations


def migrate_calibrations(input_file: str, output_file: str) -> None:
    """
    Migrate calibrations from Python file to JSON file

    Parameters
    ----------
    input_file : str
        Path to the Python file containing calibrations
    output_file : str
        Path where the JSON file should be written

    Raises
    ------
    FileNotFoundError
        If the input file doesn't exist
    ImportError
        If the Python file cannot be imported
    ValueError
        If no valid calibrations are found
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    # Check input file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Extract calibrations from Python file
    print(f"Reading calibrations from {input_file}...")
    calibrations = extract_calibrations_from_module(input_path)
    print(f"Found {len(calibrations)} calibration(s):")
    for name in calibrations.keys():
        print(f"  - {name}")

    # Write to JSON file
    print(f"\nWriting to {output_file}...")
    with output_path.open('w') as f:
        json.dump(calibrations, f, indent=2)

    print(f"✓ Migration complete!")
    print(f"\nYou can now use calibrations like this:")
    first_cal_name = list(calibrations.keys())[0]
    print(f"  calibration='{output_file}:{first_cal_name}'")


def main():
    """Main entry point for the migration script"""
    if len(sys.argv) != 3:
        print("Usage: python migrate_calibrations.py INPUT.py OUTPUT.json")
        print("\nExample:")
        print("  python migrate_calibrations.py calibrations.py calibrations.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        migrate_calibrations(input_file, output_file)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
