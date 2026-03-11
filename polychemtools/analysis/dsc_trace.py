"""
Differential Scanning Calorimetry data analysis

This module provides classes for analyzing DSC traces including slope measurements
and thermal transitions.
"""

from __future__ import annotations

import logging
import numpy as np
from scipy import stats
from typing import Tuple, Optional, Union
from ..processing.dsc_data_processor import DSCData

logger = logging.getLogger(__name__)


class DSCTrace:
    """
    Object representing a single DSC ramp with methods for analysis

    This class handles analysis of a single heating or cooling ramp from
    a DSC experiment, including baseline slope measurements and thermal
    transition identification.

    Attributes
    ----------
    temperatures : np.ndarray
        1D array of temperature values (°C)
    heat_flows : np.ndarray
        1D array of heat flow values (W/g)
    """

    def __init__(
        self,
        temperatures: np.ndarray,
        heat_flows: np.ndarray
    ):
        """
        Initialize a DSCTrace object

        Parameters
        ----------
        temperatures : np.ndarray
            1D array of temperature values
        heat_flows : np.ndarray
            1D array of heat flow values

        Raises
        ------
        ValueError
            If arrays have different lengths or invalid dimensions
        """
        if len(temperatures) != len(heat_flows):
            raise ValueError(
                f'Temperature length ({len(temperatures)}) does not match '
                f'heat flow length ({len(heat_flows)})'
            )

        if temperatures.ndim != 1:
            raise ValueError(
                f'Temperatures must be 1D array, got {temperatures.ndim}D'
            )

        if heat_flows.ndim != 1:
            raise ValueError(
                f'Heat flows must be 1D array, got {heat_flows.ndim}D'
            )

        # Ensure arrays are sorted by temperature
        if not np.all(np.diff(temperatures) >= 0):
            logger.warning(
                "Temperature data was not monotonically increasing and has been "
                "automatically sorted. This may indicate data issues or a cooling ramp."
            )
            sort_indices = np.argsort(temperatures)
            temperatures = temperatures[sort_indices]
            heat_flows = heat_flows[sort_indices]

        self.temperatures = temperatures
        self.heat_flows = heat_flows

    @classmethod
    def from_file(
        cls,
        instrument: str,
        file_path: str,
        ramp_index: int = -1,
        reverse: bool = True
    ) -> DSCTrace:
        """
        Create a DSCTrace from a data file

        Parameters
        ----------
        instrument : str
            DSC instrument type (e.g., 'trios')
        file_path : str
            Path to the DSC data file
        ramp_index : int, optional
            Index of the ramp to extract (default: -1, last ramp).
            Negative indices count from end (-1 is last, -2 is second-to-last)
        reverse : bool, optional
            If True, reverse the data (default: True, useful for second heating curve)

        Returns
        -------
        DSCTrace
            A new DSCTrace object for the specified ramp

        Examples
        --------
        >>> # Get second heating curve (last ramp, reversed)
        >>> trace = DSCTrace.from_file('trios', 'experiment.csv', ramp_index=-1, reverse=True)

        >>> # Get first heating curve
        >>> trace = DSCTrace.from_file('trios', 'experiment.csv', ramp_index=0, reverse=False)
        """
        processor = DSCData(instrument, file_path)
        temperatures, heat_flows = processor.get_ramp_data(ramp_index, reverse)
        return cls(temperatures, heat_flows)

    def measure_slope(
        self,
        temperature_range: Tuple[float, float],
        return_fit_data: bool = False
    ) -> Union[float, Tuple[float, float, np.ndarray, np.ndarray]]:
        """
        Measure the slope (baseline) in a specified temperature range

        This method performs linear regression on the heat flow vs temperature
        data within the specified range, typically used to measure the baseline
        slope or heat capacity.

        Parameters
        ----------
        temperature_range : Tuple[float, float]
            (min_temp, max_temp) defining the region for slope measurement
        return_fit_data : bool, optional
            If True, return additional fit parameters and data for plotting
            (default: False)

        Returns
        -------
        slope : float
            Slope of the linear fit (W/g/°C)
        intercept : float
            Y-intercept of the linear fit (W/g), only if return_fit_data=True
        fit_temps : np.ndarray
            Temperature values used in fit, only if return_fit_data=True
        fit_flows : np.ndarray
            Heat flow values used in fit, only if return_fit_data=True

        Raises
        ------
        ValueError
            If temperature range is invalid or contains no data points

        Examples
        --------
        >>> trace = DSCTrace.from_file('experiment.csv')
        >>> slope = trace.measure_slope((55, 60))  # Baseline slope
        >>> print(f'Heat capacity slope: {slope:.4f} W/g/°C')

        >>> # Get full fit data for plotting
        >>> slope, intercept, temps, flows = trace.measure_slope((55, 60), True)
        """
        min_temp, max_temp = temperature_range

        if max_temp <= min_temp:
            raise ValueError(
                f'Max temperature ({max_temp}) must be greater than '
                f'min temperature ({min_temp})'
            )

        # Find indices for the temperature range
        start_idx = np.searchsorted(self.temperatures, min_temp)
        end_idx = np.searchsorted(self.temperatures, max_temp)

        if end_idx <= start_idx:
            raise ValueError(
                f'No data points found in temperature range '
                f'({min_temp}, {max_temp})'
            )

        # Extract data in range
        temps_in_range = self.temperatures[start_idx:end_idx]
        flows_in_range = self.heat_flows[start_idx:end_idx]

        # Perform linear regression
        fit_result = stats.linregress(temps_in_range, flows_in_range)

        if return_fit_data:
            return (
                fit_result.slope,
                fit_result.intercept,
                temps_in_range,
                flows_in_range
            )
        else:
            return fit_result.slope

    def normalize_to_baseline(
        self,
        baseline_value: Optional[float] = None
    ) -> np.ndarray:
        """
        Normalize heat flows by subtracting a baseline value

        Parameters
        ----------
        baseline_value : float, optional
            Value to subtract from all heat flows. If None, uses the last
            value in the trace (common for DSC normalization)

        Returns
        -------
        np.ndarray
            Normalized heat flow values

        Examples
        --------
        >>> trace = DSCTrace.from_file('experiment.csv')
        >>> normalized = trace.normalize_to_baseline()  # Subtract endpoint
        >>> normalized = trace.normalize_to_baseline(0.5)  # Subtract 0.5 W/g
        """
        if baseline_value is None:
            baseline_value = self.heat_flows[-1]

        return self.heat_flows - baseline_value

    def get_temperature_index(self, temperature: float) -> int:
        """
        Find the index closest to a given temperature

        Parameters
        ----------
        temperature : float
            Temperature value to find

        Returns
        -------
        int
            Index of the closest temperature value
        """
        return np.searchsorted(self.temperatures, temperature)

    def __len__(self) -> int:
        """Return the number of data points in the trace"""
        return len(self.temperatures)

    def __repr__(self) -> str:
        """String representation of the DSC trace"""
        temp_range = f'{self.temperatures[0]:.1f} to {self.temperatures[-1]:.1f}°C'
        return f'DSCTrace({len(self)} points, {temp_range})'
