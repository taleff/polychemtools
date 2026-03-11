"""
Gel Permeation Chromatography data processing

This module provides classes for parsing and analyzing GPC data from various instruments.
"""

import numpy as np
from .data_processor import UnsupportedInstrumentError


class GPCData:
    """
    Gel permeation chromatography data parser from instrumental data

    Attributes
    ----------
    retention_times: np.ndarray
        An array that contains the retention times at which the
        instrument measured intensities.
    intensities: np.ndarray
        A 2D array that contains the intensities corresponding to
        the retention times. The columns correspond to different
        traces
    """
    
    SUPPORTED_INSTRUMENTS = ['tosoh']

    INSTRUMENT_CONFIGS = {
          'tosoh': {
              'header': 2,
              'delimiter': None,
          }
      }

    def __init__(self, retention_times, intensities):
        """
        Initialize GPCDataProcessor with specified instrument type.

        Parameters
        ----------
        retention_times: np.ndarray
            An array that contains the retention times at which the
            instrument measured intensities.
        intensities: np.ndarray
            A 2D array that contains the intensities corresponding to
            the retention times. The columns correspond to different
            traces
        """
        self.retention_times = retention_times
        self.intensities = intensities

    @classmethod
    def from_file(cls, instrument, file_path):
        """
        Initialize GPCDataProcessor with specified instrument type.

        Parameters
        ----------
        instrument: str
            The GPC instrument type. Determines parsing strategy.
            Supported values: 'tosoh'
        file_path: str
            Path to the GPC data file.

        Raises
        ------
        UnsupportedInstrumentError
            If instrument type is not supported
        """
        if instrument not in cls.SUPPORTED_INSTRUMENTS:
            raise UnsupportedInstrumentError(
                f"Instrument '{instrument}' is not supported. "
                f"Supported instruments: {', '.join(cls.SUPPORTED_INSTRUMENTS)}"
            )

        config = cls.INSTRUMENT_CONFIGS[instrument]
        traces = np.genfromtxt(
            file_path, skip_header=config['header'],
            delimiter=config['delimiter']
        )

        # Validate data shape
        if traces.ndim != 2:
            raise ValueError(
                f'Expected 2D data from file, got {traces.ndim}D array'
            )
        if traces.shape[1] < 2:
            raise ValueError(
                f'Expected at least 2 columns (retention time + intensity), '
                f'got {traces.shape[1]} column(s)'
            )

        retention_times = traces[:, 0]
        intensities = np.atleast_2d(traces[:, 1::2])
        
        return GPCData(retention_times, intensities)

    def __len__(self):
        """
        Finds the number of GPC traces contained in the data

        Returns
        -------
        traces: int
            The number of individual GPC traces
        """
        # Return the number of columns in the intensities array
        return np.shape(self.intensities)[1]

