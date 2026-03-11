"""
Graphing DSC traces for experimental data

This module provides classes for visualizing DSC data including heating/cooling
curves and stacked normalized plots.
"""

from __future__ import annotations

import numpy as np
from typing import Optional, List
from .trace_graph import TraceGraph
from ..analysis.dsc_trace import DSCTrace
from ..processing.dsc_data_processor import DSCData


class DSCTraceGraph(TraceGraph):
    """
    Object representing a graph showing DSC heating/cooling curves

    Inherits from TraceGraph, adding DSC-specific defaults and convenience
    methods. The plot is created lazily when save_graph() is called.

    Attributes
    ----------
    x_values : np.ndarray
        Temperature values
    y_values : np.ndarray
        Heat flow values (2D array, each column is a ramp)
    xtitle : str
        X-axis label
    ytitle : str
        Y-axis label
    legend : list or None
        List of legend labels for each ramp
    legend_loc : str
        Location of the legend
    colors : list
        List of colors for each trace
    xbounds : tuple or None
        Optional (min, max) bounds for x-axis
    ybounds : tuple or None
        Optional (min, max) bounds for y-axis
    stylesheet : str
        Path to matplotlib stylesheet file
    """

    # Default ramp labels for typical DSC experiments
    DEFAULT_RAMP_LABELS = ['First Heating', 'Cooling', 'Second Heating']

    def __init__(
        self,
        x_values: np.ndarray,
        y_values: np.ndarray,
        xtitle: str = 'Temperature (°C)',
        ytitle: str = 'Heat Flow (W/g)',
        legend: Optional[List[str]] = None,
        legend_loc: str = 'upper left',
        color_scheme: str = 'viridis',
        stylesheet: Optional[str] = None
    ):
        """
        Initialize a DSCTraceGraph object

        Parameters
        ----------
        x_values : np.ndarray
            1D array of temperature values
        y_values : np.ndarray
            2D array of heat flow values (each column is a ramp)
        xtitle : str, optional
            X-axis label (default: 'Temperature (°C)')
        ytitle : str, optional
            Y-axis label (default: 'Heat Flow (W/g)')
        legend : list of str, optional
            Legend labels for each ramp. If None and viridis color scheme,
            uses default labels
        legend_loc : str, optional
            Legend location (default: 'upper left')
        color_scheme : str, optional
            Color scheme: 'viridis' or 'black' (default: 'viridis')
        stylesheet : str, optional
            Path to matplotlib stylesheet. If None, uses default

        Raises
        ------
        ValueError
            If color scheme is not valid
        ValueError
            If x and y arrays have mismatched dimensions
        """
        # Determine legend with DSC-specific defaults
        # If no legend provided and using viridis, use default ramp labels
        effective_legend = legend
        if legend is None and color_scheme == 'viridis':
            # Calculate number of traces to determine default legend length
            if y_values.ndim == 1:
                num_traces = 1
            else:
                num_traces = y_values.shape[1]
            effective_legend = self.DEFAULT_RAMP_LABELS[:num_traces]

        # Initialize parent TraceGraph with DSC defaults
        super().__init__(
            x_values=x_values,
            y_values=y_values,
            xtitle=xtitle,
            ytitle=ytitle,
            xscale='linear',
            legend=effective_legend,
            legend_loc=legend_loc,
            color_scheme=color_scheme,
            stylesheet=stylesheet
        )

    @classmethod
    def from_file(
        cls,
        instrument: str,
        file_path: str,
        graph_file: str,
        ramp_indices: Optional[List[int]] = None,
        legend: Optional[List[str]] = None,
        color_scheme: str = 'viridis',
        xlim: Optional[tuple] = None,
        ylim: Optional[tuple] = None
    ) -> DSCTraceGraph:
        """
        Create and save a DSC plot directly from a data file

        This is a convenience method for quickly creating plots from raw data.

        Parameters
        ----------
        instrument : str
            DSC instrument type (e.g., 'trios')
        file_path : str
            Path to the DSC data file
        graph_file : str
            Path where the graph should be saved
        ramp_indices : list of int, optional
            Indices of ramps to plot. If None, plots all ramps
        legend : list of str, optional
            Legend labels. If None, uses default labels
        color_scheme : str, optional
            Color scheme: 'viridis' or 'black' (default: 'viridis')
        xlim : tuple, optional
            (min, max) for x-axis limits
        ylim : tuple, optional
            (min, max) for y-axis limits

        Returns
        -------
        DSCTraceGraph
            The created graph object

        Examples
        --------
        >>> # Plot all ramps with default settings
        >>> graph = DSCTraceGraph.from_file('trios', 'experiment.csv', 'output.png')

        >>> # Plot only second heating curve
        >>> graph = DSCTraceGraph.from_file(
        ...     'trios', 'experiment.csv', 'output.png',
        ...     ramp_indices=[-1],
        ...     legend=['Second Heating']
        ... )
        """
        processor = DSCData(instrument, file_path)

        # Determine which ramps to plot
        if ramp_indices is None:
            ramp_indices = list(range(len(processor)))

        # Extract data for each ramp
        ramp_data = []
        for idx in ramp_indices:
            temps, flows = processor.get_ramp_data(idx)
            ramp_data.append((temps, flows))

        # Find common temperature range
        all_temps = np.concatenate([temps for temps, _ in ramp_data])
        min_temp = np.min(all_temps)
        max_temp = np.max(all_temps)

        # Create common temperature grid
        common_temps = np.linspace(min_temp, max_temp, 1000)

        # Interpolate all ramps onto common grid
        interpolated_flows = []
        for temps, flows in ramp_data:
            interpolated = np.interp(common_temps, temps, flows)
            interpolated_flows.append(interpolated)

        # Stack into 2D array
        flows_array = np.column_stack(interpolated_flows)

        # Create graph
        graph = cls(
            common_temps,
            flows_array,
            legend=legend,
            color_scheme=color_scheme
        )

        # Set bounds if provided
        if xlim is not None:
            graph.set_xbounds(xlim)
        if ylim is not None:
            graph.set_ybounds(ylim)

        # Save
        graph.save_graph(graph_file)

        return graph

    @classmethod
    def create_stacked_plot(
        cls,
        instrument: str,
        file_paths: List[str],
        graph_file: str,
        ramp_index: int = -1,
        normalize: bool = True,
        legend: Optional[List[str]] = None,
        color_scheme: str = 'viridis',
        xlim: Optional[tuple] = None,
        ylim: Optional[tuple] = None
    ) -> DSCTraceGraph:
        """
        Create a stacked plot comparing the same ramp from multiple experiments

        This method is useful for comparing different samples or conditions.

        Parameters
        ----------
        instrument : str
            DSC instrument type (e.g., 'trios')
        file_paths : list of str
            Paths to DSC data files to compare
        graph_file : str
            Path where the graph should be saved
        ramp_index : int, optional
            Index of the ramp to extract from each file (default: -1, last ramp)
        normalize : bool, optional
            If True, normalize each trace by subtracting its endpoint value
            (default: True)
        legend : list of str, optional
            Legend labels for each file
        color_scheme : str, optional
            Color scheme: 'viridis' or 'black' (default: 'viridis')
        xlim : tuple, optional
            (min, max) for x-axis limits
        ylim : tuple, optional
            (min, max) for y-axis limits

        Returns
        -------
        DSCTraceGraph
            The created graph object

        Examples
        --------
        >>> # Compare second heating curves from three experiments
        >>> files = ['sample1.csv', 'sample2.csv', 'sample3.csv']
        >>> graph = DSCTraceGraph.create_stacked_plot(
        ...     'trios', files, 'comparison.png',
        ...     legend=['Sample 1', 'Sample 2', 'Sample 3']
        ... )
        """
        traces = []
        for file_path in file_paths:
            trace = DSCTrace.from_file(instrument, file_path, ramp_index, reverse=True)
            if normalize:
                normalized_flows = trace.normalize_to_baseline()
                traces.append((trace.temperatures, normalized_flows))
            else:
                traces.append((trace.temperatures, trace.heat_flows))

        # Find common temperature range
        all_temps = np.concatenate([temps for temps, _ in traces])
        min_temp = np.min(all_temps)
        max_temp = np.max(all_temps)

        # Create common temperature grid
        common_temps = np.linspace(min_temp, max_temp, 1000)

        # Interpolate all traces onto common grid
        interpolated_flows = []
        for temps, flows in traces:
            interpolated = np.interp(common_temps, temps, flows)
            interpolated_flows.append(interpolated)

        # Stack into 2D array
        flows_array = np.column_stack(interpolated_flows)

        # Create graph with normalized ylabel if applicable
        ytitle = 'Normalized Heat Flow (W/g)' if normalize else 'Heat Flow (W/g)'
        graph = cls(
            common_temps,
            flows_array,
            ytitle=ytitle,
            legend=legend,
            color_scheme=color_scheme
        )

        # Set bounds if provided
        if xlim is not None:
            graph.set_xbounds(xlim)
        if ylim is not None:
            graph.set_ybounds(ylim)

        # Save
        graph.save_graph(graph_file)

        return graph
