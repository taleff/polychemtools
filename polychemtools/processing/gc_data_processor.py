"""
Gas Chromatography data analysis tools.

This module provides classes for parsing and analyzing GC data from various instruments.
"""

import logging
import pandas as pd
import numpy as np
from typing import List, Optional
from .data_processor import UnsupportedInstrumentError

logger = logging.getLogger(__name__)


class MultiplePeaksFoundError(Exception):
    """Raised when multiple peaks are found within the specified tolerance."""
    pass


class GCData:
    """
    Represents gas chromatography data with instrument-specific parsing.

    Attributes
    ----------
    instrument : str
        The GC instrument type (e.g., 'shimadzu')
    peak_retention_times : np.ndarray
        1D array of retention times for detected peaks
    peak_areas : np.ndarray
        1D array of areas for detected peaks
    chromatogram_times : np.ndarray
        1D array of retention times for the full chromatogram
    chromatogram_intensities : np.ndarray
        1D array of intensities for the full chromatogram
    """

    SUPPORTED_INSTRUMENTS = ['shimadzu']

    def __init__(self, instrument: str, file_path: str):
        """
        Initialize GCDataProcessor with specified instrument type and data file.

        Parameters
        ----------
        instrument : str
            The GC instrument type. Determines parsing strategy.
            Supported values: 'shimadzu'
        file_path : str
            Path to the GC data file.

        Raises
        ------
        UnsupportedInstrumentError
            If instrument type is not supported.
        FileNotFoundError
            If the specified file does not exist.
        """
        if instrument not in self.SUPPORTED_INSTRUMENTS:
            raise UnsupportedInstrumentError(
                f"Instrument '{instrument}' is not supported. "
                f"Supported instruments: {', '.join(self.SUPPORTED_INSTRUMENTS)}"
            )
        self.instrument = instrument

        # Parse and store peak table data as numpy arrays
        self.peak_retention_times, self.peak_areas = self._parse_peak_table(file_path)

        # Parse and store chromatogram data as numpy arrays
        self.chromatogram_times, self.chromatogram_intensities = self._parse_chromatogram(file_path)

    def get_peak_areas(
        self,
        retention_times: List[float],
        tolerance: float = 0.10
    ) -> List[Optional[float]]:
        """
        Extract peak areas at specified retention times from stored GC data.

        Parameters
        ----------
        retention_times : List[float]
            List of target retention times (in minutes).
        tolerance : float, optional
            Tolerance for matching retention times (±tolerance minutes).
            Default is 0.10 minutes.

        Returns
        -------
        List[Optional[float]]
            List of peak areas corresponding to each retention time.
            Returns None for retention times where no peak was found.

        Raises
        ------
        MultiplePeaksFoundError
            If multiple peaks found within tolerance.
        """
        areas = []
        for rt in retention_times:
            area = self._find_matching_peak(rt, tolerance)
            areas.append(area)

        return areas

    def get_chromatogram(
        self,
        time_range: Optional[tuple[float, float]] = None
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Extract chromatogram data from stored GC data.

        Parameters
        ----------
        time_range : Optional[tuple[float, float]], optional
            Optional tuple of (min_time, max_time) in minutes to filter data.
            If None, returns all data points.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            Tuple of (retention_times, intensities) as numpy arrays.

        Raises
        ------
        ValueError
            If time_range is invalid (min >= max or negative values).
        """
        if time_range is not None:
            min_time, max_time = time_range
            if min_time < 0 or max_time < 0:
                raise ValueError("Time range values must be non-negative")
            if min_time >= max_time:
                raise ValueError("min_time must be less than max_time")

        # Use stored chromatogram data
        retention_times = self.chromatogram_times
        intensities = self.chromatogram_intensities

        # Apply time range filtering if specified
        if time_range is not None:
            min_time, max_time = time_range
            mask = (retention_times >= min_time) & (retention_times <= max_time)
            retention_times = retention_times[mask]
            intensities = intensities[mask]

        return retention_times, intensities

    def _read_file_lines(self, file_path: str) -> list[str]:
        """
        Read file contents with encoding error handling.

        Parameters
        ----------
        file_path : str
            Path to the file to read.

        Returns
        -------
        list[str]
            List of lines from the file.
        """
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            if '\ufffd' in content:
                logger.warning(
                    f"File '{file_path}' contains invalid UTF-8 sequences that were "
                    "replaced. Some data may be corrupted."
                )
            return content.splitlines(keepends=True)

    def _parse_shimadzu_section(
        self,
        lines: list[str],
        section_marker: str,
        header_offset: int,
        columns: list[str],
        file_path: str
    ) -> pd.DataFrame:
        """
        Parse a section from Shimadzu GC data file.

        Parameters
        ----------
        lines : list[str]
            Lines from the file.
        section_marker : str
            Marker string to find the section (e.g., '[Peak Table (Ch1)]').
        header_offset : int
            Number of lines after section marker where header is located.
            Use -1 to search for header containing 'R.Time'.
        columns : list[str]
            Column names for the resulting DataFrame.
        file_path : str
            Original file path for error messages.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the parsed section data.
        """
        # Find the section start
        section_start = None
        for i, line in enumerate(lines):
            if section_marker in line:
                section_start = i
                break

        if section_start is None:
            raise ValueError(f"Could not find '{section_marker}' in {file_path}")

        # Find header line
        if header_offset >= 0:
            header_line_idx = section_start + header_offset
        else:
            # Search for header containing 'R.Time'
            header_line_idx = None
            for i in range(section_start + 1, len(lines)):
                if 'R.Time' in lines[i]:
                    header_line_idx = i
                    break
            if header_line_idx is None:
                raise ValueError(f"Could not find header in section '{section_marker}' in {file_path}")

        # Parse data lines until we hit another section marker or empty line
        data_lines = []
        for i in range(header_line_idx + 1, len(lines)):
            line = lines[i].strip()
            if not line or line.startswith('['):
                break
            data_lines.append(line.split('\t'))

        return pd.DataFrame(data_lines, columns=columns)

    def _parse_peak_table(self, file_path: str) -> tuple[np.ndarray, np.ndarray]:
        """
        Parse the peak table from the data file based on instrument type.

        Parameters
        ----------
        file_path : str
            Path to the GC data file.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            A tuple containing (retention_times, areas) as numpy arrays.
        """
        if self.instrument == 'shimadzu':
            return self._parse_shimadzu_peak_table(file_path)
        else:
            raise UnsupportedInstrumentError(f"No parser for instrument: {self.instrument}")

    def _parse_shimadzu_peak_table(self, file_path: str) -> tuple[np.ndarray, np.ndarray]:
        """
        Parse peak table from Shimadzu GC data file.

        The peak table is located after the line '[Peak Table (Ch1)]'.

        Parameters
        ----------
        file_path : str
            Path to the Shimadzu data file.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            A tuple containing (retention_times, areas) as numpy arrays.
        """
        lines = self._read_file_lines(file_path)

        # Parse header to get column names
        # Line structure: [Peak Table (Ch1)], # of Peaks, Header, Data...
        section_start = None
        for i, line in enumerate(lines):
            if '[Peak Table (Ch1)]' in line:
                section_start = i
                break

        if section_start is None:
            raise ValueError(f"Could not find '[Peak Table (Ch1)]' in {file_path}")

        header = lines[section_start + 2].strip().split('\t')

        df = self._parse_shimadzu_section(
            lines=lines,
            section_marker='[Peak Table (Ch1)]',
            header_offset=2,
            columns=header,
            file_path=file_path
        )

        # Convert numeric columns
        df['R.Time'] = pd.to_numeric(df['R.Time'], errors='coerce')
        df['Area'] = pd.to_numeric(df['Area'], errors='coerce')

        return df['R.Time'].to_numpy(), df['Area'].to_numpy()

    def _parse_chromatogram(self, file_path: str) -> tuple[np.ndarray, np.ndarray]:
        """
        Parse the chromatogram data from the data file based on instrument type.

        Parameters
        ----------
        file_path : str
            Path to the GC data file.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            A tuple containing (retention_times, intensities) as numpy arrays.
        """
        if self.instrument == 'shimadzu':
            return self._parse_shimadzu_chromatogram(file_path)
        else:
            raise UnsupportedInstrumentError(f"No chromatogram parser for instrument: {self.instrument}")

    def _parse_shimadzu_chromatogram(self, file_path: str) -> tuple[np.ndarray, np.ndarray]:
        """
        Parse chromatogram data from Shimadzu GC data file.

        The chromatogram data is located after the line '[Chromatogram (Ch1)]'.

        Parameters
        ----------
        file_path : str
            Path to the Shimadzu data file.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            A tuple containing (retention_times, intensities) as numpy arrays.
        """
        lines = self._read_file_lines(file_path)

        df = self._parse_shimadzu_section(
            lines=lines,
            section_marker='[Chromatogram (Ch1)]',
            header_offset=-1,  # Search for header containing 'R.Time'
            columns=['R.Time', 'Intensity'],
            file_path=file_path
        )

        # Convert to numeric
        df['R.Time'] = pd.to_numeric(df['R.Time'], errors='coerce')
        df['Intensity'] = pd.to_numeric(df['Intensity'], errors='coerce')

        return df['R.Time'].to_numpy(), df['Intensity'].to_numpy()

    def _find_matching_peak(
        self,
        retention_time: float,
        tolerance: float
    ) -> Optional[float]:
        """
        Find the peak area for a given retention time within tolerance.

        Parameters
        ----------
        retention_time : float
            Target retention time.
        tolerance : float
            Tolerance for matching (±tolerance).

        Returns
        -------
        Optional[float]
            Peak area if exactly one peak found, None if no peak found.

        Raises
        ------
        MultiplePeaksFoundError
            If multiple peaks found within tolerance.
        """
        min_rt = retention_time - tolerance
        max_rt = retention_time + tolerance

        # Find matching peaks using stored numpy arrays
        mask = (self.peak_retention_times >= min_rt) & (self.peak_retention_times <= max_rt)
        matching_retention_times = self.peak_retention_times[mask]
        matching_areas = self.peak_areas[mask]

        if len(matching_areas) == 0:
            return None
        elif len(matching_areas) == 1:
            return float(matching_areas[0])
        else:
            rt_values = matching_retention_times.tolist()
            raise MultiplePeaksFoundError(
                f"Found {len(matching_areas)} peaks within tolerance of {retention_time} "
                f"(±{tolerance}): {rt_values}"
            )
        
