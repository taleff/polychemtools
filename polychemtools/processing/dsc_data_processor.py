from __future__ import annotations

import numpy as np
from typing import Tuple
from .data_processor import UnsupportedInstrumentError


class DSCData:
    """
    Represents differential scanning calorimetry data with instrument-specific parsing.

    This class handles parsing of DSC CSV files and extraction of temperature
    and heat flow data. The data typically contains multiple heating/cooling
    ramps that can be analyzed separately.

    Attributes
    ----------
    instrument : str
        The DSC instrument type (e.g., 'trios')
    file_path : str
        Path to the DSC data file
    temperatures : np.ndarray
        1D array of temperature values (°C)
    heat_flows : np.ndarray
        1D array of heat flow values (W/g)
    ramp_indices : np.ndarray
        Array of indices indicating where heating/cooling ramps start
    """

    SUPPORTED_INSTRUMENTS = ['trios']

    INSTRUMENT_CONFIGS = {
        'trios': {
            'header': 130,  # Number of header rows to skip
            'delimiter': ',',
            'temp_column': 1,  # Column index for temperature data
            'flow_column': 2,  # Column index for heat flow data
            'comment_markers': ['[step]', 'Ramp', 'Time', 'min']
        }
    }

    def __init__(self, instrument, file_path):
        """
        Initialize DSCDataProcessor with specified instrument type

        Parameters
        ----------
        instrument : str
            The DSC instrument type. Determines parsing strategy.
            Supported values: 'trios'
        file_path : str
            Path to the DSC CSV file

        Raises
        ------
        UnsupportedInstrumentError
            If the instrument type is not supported
        FileNotFoundError
            If the specified file does not exist
        ValueError
            If the file format is invalid or contains no data
        """
        if instrument not in self.SUPPORTED_INSTRUMENTS:
            raise UnsupportedInstrumentError(
                f"Instrument '{instrument}' is not supported. "
                f"Supported instruments: {self.SUPPORTED_INSTRUMENTS}"
            )

        self.instrument = instrument
        self.file_path = file_path
        self._parse_dsc_data()

    def _count_valid_data_points(self) -> int:
        """
        Count the number of valid (non-empty) data points in the file

        The heat flow column typically has the most empty strings, making
        it the limiting factor for valid rows.

        Returns
        -------
        int
            Number of valid data points in the file

        Raises
        ------
        FileNotFoundError
            If the file cannot be found
        """
        config = self.INSTRUMENT_CONFIGS[self.instrument]

        # Load heat flow column as strings to count non-empty entries
        heat_flow_column = np.loadtxt(
            self.file_path,
            dtype=str,
            skiprows=config['header'],
            delimiter=config['delimiter'],
            usecols=config['flow_column'],
            comments=config['comment_markers']
        )

        # Count non-empty strings
        valid_count = len(heat_flow_column[heat_flow_column != ''])

        if valid_count == 0:
            raise ValueError(f'No valid data points found in {self.file_path}')

        return valid_count

    def _find_ramp_indices(self) -> np.ndarray:
        """
        Find the indices where heating/cooling ramps begin

        DSC experiments typically consist of multiple ramps (e.g., first heating,
        cooling, second heating). These are marked by lines containing 'Ramp' in
        the raw data file.

        Returns
        -------
        np.ndarray
            Array of indices indicating ramp start positions. The first element
            is always 0, and the last is always -1 (indicating end of data).

        Notes
        -----
        The delimiter '@' is used to force single-column reading since '@' does
        not appear in the data files.
        """
        config = self.INSTRUMENT_CONFIGS[self.instrument]

        # Read entire lines as single column
        lines = np.loadtxt(
            self.file_path,
            dtype=str,
            skiprows=config['header'],
            delimiter='@',  # Force single column
            comments=config['comment_markers']
        )

        # Find rows containing 'Ramp'
        ramp_rows = np.where(np.char.find(lines, 'Ramp') != -1)[0]

        # Adjust indices because data arrays don't include 'Ramp' rows
        ramp_rows = ramp_rows - np.arange(len(ramp_rows))

        # Create full ramp index array with 0 at start and -1 at end
        ramp_indices = np.zeros(len(ramp_rows) + 2, dtype=int)
        ramp_indices[0] = 0
        ramp_indices[1:-1] = ramp_rows
        ramp_indices[-1] = -1

        return ramp_indices

    def _parse_dsc_data(self) -> None:
        """
        Parse DSC data from the CSV file

        Extracts temperature and heat flow data, and identifies ramp locations.
        Data is stored in instance attributes.

        Raises
        ------
        FileNotFoundError
            If the specified file does not exist
        ValueError
            If the file format is invalid
        """
        config = self.INSTRUMENT_CONFIGS[self.instrument]

        # Count valid data points
        data_points = self._count_valid_data_points()

        # Load the raw data
        # Column 0: Time (unused)
        # Column 1: Temperature (°C)
        # Column 2: Heat Flow (W/g)
        raw_data = np.loadtxt(
            self.file_path,
            skiprows=config['header'],
            delimiter=config['delimiter'],
            max_rows=data_points,
            comments=config['comment_markers']
        )

        # Validate data shape
        if raw_data.ndim != 2:
            raise ValueError(
                f'Expected 2D data from file, got {raw_data.ndim}D array'
            )
        if raw_data.shape[1] < 3:
            raise ValueError(
                f'Expected at least 3 columns (time, temperature, heat flow), '
                f'got {raw_data.shape[1]} column(s)'
            )

        # Extract temperature and heat flow using configured column indices
        self.temperatures = raw_data[:, config['temp_column']]
        self.heat_flows = raw_data[:, config['flow_column']]

        # Find ramp locations
        self.ramp_indices = self._find_ramp_indices()

    def get_ramp_data(
        self, ramp_index: int, reverse: bool = False
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get temperature and heat flow data for a specific ramp

        Parameters
        ----------
        ramp_index : int
            Index of the ramp to extract (0-based). Negative indices count
            from the end (-1 is the last ramp, -2 is second-to-last, etc.)
        reverse : bool, optional
            If True, reverse the data arrays (useful for cooling ramps or
            when analyzing from high to low temperature)

        Returns
        -------
        temperatures : np.ndarray
            Temperature values for the specified ramp
        heat_flows : np.ndarray
            Heat flow values for the specified ramp

        Raises
        ------
        IndexError
            If ramp_index is out of range

        Examples
        --------
        >>> dsc = DSCDataProcessor('experiment.csv')
        >>> temps, flows = dsc.get_ramp_data(-1, reverse=True)  # Last ramp, reversed
        """
        num_ramps = len(self.ramp_indices) - 1

        # Handle negative indices
        if ramp_index < 0:
            ramp_index = num_ramps + ramp_index

        if ramp_index < 0 or ramp_index >= num_ramps:
            raise IndexError(
                f'Ramp index {ramp_index} out of range for {num_ramps} ramps'
            )

        # Get slice bounds
        start = self.ramp_indices[ramp_index]
        end = self.ramp_indices[ramp_index + 1]

        # Extract data
        temps = self.temperatures[start:end]
        flows = self.heat_flows[start:end]

        # Reverse if requested
        if reverse:
            temps = temps[::-1]
            flows = flows[::-1]

        return temps, flows

    def __len__(self) -> int:
        """
        Return the number of ramps in the DSC data

        Returns
        -------
        int
            Number of heating/cooling ramps
        """
        return len(self.ramp_indices) - 1

    def __repr__(self) -> str:
        """String representation of the DSC data"""
        return (
            f'DSCDataProcessor({len(self)} ramps, '
            f'{len(self.temperatures)} data points)'
        )
