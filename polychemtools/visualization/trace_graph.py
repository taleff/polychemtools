"""
Line plot visualization for trace data

This module provides classes for visualizing experimental trace data
including GPC chromatograms.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from .base_graph import BaseGraph
from ..analysis.gpc_trace import GPCTrace, PolymerSample, MissingCalibrationError


class TraceGraph(BaseGraph):
    """
    Object representing a graph showing a line plot visualizing experimental data

    Attributes
    ----------
    x_values : np.ndarray
        A 1D numpy array containing the independent variable for the
        visualized data
    y_values: np.ndarray
        A 2D numpy array containing the dependent variables to be
        plotted where each column is a trace
    xtitle : str
        The x-axis label
    ytitle : str
        The y-axis label
    xscale : str
        Scale for the x-axis ('linear' or 'log')
    legend : list or None
        List of legend labels for each trace
    legend_loc : str
        Location of the legend (default: 'upper left')
    colors: list
        A list of colors corresponding to each trace
    xbounds : tuple or None
        Optional (min, max) bounds for x-axis
    ybounds : tuple or None
        Optional (min, max) bounds for y-axis
    stylesheet : str
        Path to matplotlib stylesheet file used for plot styling
    """

    def __init__(self, x_values, y_values, xtitle, ytitle,
                 xscale='linear', legend=None, legend_loc='upper left',
                 color_scheme='black', stylesheet=None):
        """
        Initializes a single TraceGraph object

        Parameters
        ----------
        x_values : np.ndarray
            A 1D numpy array containing the independent variable for the
            visualized data
        y_values: np.ndarray
            A 2D numpy array containing the dependent variables to be
            plot where each column is a trace
        xtitle: str
            The axis title for the x-axis
        ytitle: str
            The axis title for the y-axis
        xscale: str, optional
            Scale for the x-axis: 'linear' or 'log' (default: 'linear')
        legend: list, optional
            A list containing strings corresponding to the names of
            each of the traces
        legend_loc: str, optional
            The location of the legend
        color_scheme: str, optional
            The name of the color scheme to be used
        stylesheet: str, optional
            Path to a matplotlib stylesheet file. If None, uses the default
            stylesheet located at tools/visualization/default.mplstyle

        Raises
        ------
        ValueError
            If x_values and y_values second dimension are not the same length
        ValueError
            If y_values has a dimension other than one or two
        ValueError
            If color_scheme is not one of the valid color schemes
        ValueError
            If xscale is not 'linear' or 'log'
        """
        # Validate TraceGraph-specific parameters
        if color_scheme not in self.COLOR_SCHEME.keys():
            raise ValueError(
                f'{color_scheme} is not a valid color scheme'
            )

        if xscale not in ('linear', 'log'):
            raise ValueError(
                f"xscale must be 'linear' or 'log', got '{xscale}'"
            )

        # Transform y_values to 2D if needed
        if y_values.ndim == 1:
            y_values = np.atleast_2d(y_values).T
        elif y_values.ndim == 2:
            pass  # Already correct dimension
        else:
            raise ValueError(
                f'y_values dimension of {y_values.ndim} is invalid'
            )

        # Initialize base class
        super().__init__(x_values, y_values, xtitle, ytitle, stylesheet)

        # Store TraceGraph-specific configuration
        self.xscale = xscale
        self.legend = legend
        self.legend_loc = legend_loc

        # Calculate colors based on number of traces
        num_traces = self.y_values.shape[1]
        self.colors = self.COLOR_SCHEME[color_scheme](num_traces)

    def _create_plot(self, post_process_callback=None):
        """
        Creates the matplotlib figure with all traces and configuration

        Parameters
        ----------
        post_process_callback : callable, optional
            Optional callback function that takes (fig, ax) as parameters
            for additional customization after the base plot is created

        Returns
        -------
        fig : mpl.figure.Figure
            The created figure object
        """
        plt.style.use(self.stylesheet)
        fig, ax = plt.subplots()

        # Set x-axis scale
        ax.set_xscale(self.xscale)

        # Plot all traces
        num_traces = len(self)
        for i in range(num_traces):
            legend_label = '' if self.legend is None else self.legend[i]
            ax.plot(
                self.x_values,
                self.y_values[:, i],
                label=legend_label,
                color=self.colors[i]
            )

        # Set axis labels
        ax.set_xlabel(self.xtitle)
        ax.set_ylabel(self.ytitle)

        # Add legend if provided
        if self.legend is not None:
            ax.legend(loc=self.legend_loc)

        # Apply bounds using base class method
        self._apply_bounds(ax)

        # Apply post-processing callback if provided
        if post_process_callback is not None:
            post_process_callback(fig, ax)

        return fig

    def __len__(self):
        """
        Returns the number of traces in the TraceGraph object

        Returns
        -------
        traces : int
            The number of traces, i.e. the number of columns in the
            y_values attribute
        """
        return self.y_values.shape[1]


class GPCTraceGraph(TraceGraph):
    """
    Object representing a graph showing a line plot visualizing GPC data

    The class provides a number of classmethods to automatically generate
    plots from raw data

    Holds the same attributes as TraceGraph. See parent class
    documentation for attribute details.
    """
    # Constants for automatic bound calculation
    BOUND_EDGE_SCALE = 5  # Multiplier for extending bounds beyond peaks
    LOWER_BOUND_THRESHOLD = 0.2  # Round down min bound if within 0.2 of decade
    UPPER_BOUND_THRESHOLD = 0.8  # Round up max bound if within 0.8 of decade
    DEFAULT_Y_MIN = -0.1  # Default lower y-axis limit
    DEFAULT_Y_MAX = 1.1  # Default upper y-axis limit

    def __init__(self, x_values, y_values, xtitle, ytitle,
                 xscale='linear', legend=None, legend_loc='upper left',
                 color_scheme='black', stylesheet=None):
        """
        Initializes a GPCTraceGraph object

        Accepts the same parameters as TraceGraph. See parent class
        documentation for parameter details.
        """
        super().__init__(
            x_values, y_values, xtitle, ytitle, xscale, legend,
            legend_loc, color_scheme, stylesheet
        )

    @staticmethod
    def _prepare_trace_data(traces):
        """
        Normalize traces input to a tuple and validate.

        Parameters
        ----------
        traces : GPCTrace or Tuple[GPCTrace, ...]
            One or more GPCTrace objects.

        Returns
        -------
        Tuple[GPCTrace, ...]
            Normalized tuple of traces.
        """
        if isinstance(traces, GPCTrace):
            return (traces,)
        return traces

    @classmethod
    def _calculate_mw_bounds(cls, traces):
        """
        Calculate automatic molecular weight bounds based on peak positions.

        Parameters
        ----------
        traces : Tuple[GPCTrace, ...]
            Tuple of GPCTrace objects with calibration data.

        Returns
        -------
        Tuple[float, float]
            Calculated (min_bound, max_bound) for x-axis.
        """
        min_bound, max_bound = 1e10, 0
        for trace in traces:
            if min_bound > trace.tight_bounds[0]:
                min_bound = trace.tight_bounds[0]
            if max_bound < trace.tight_bounds[1]:
                max_bound = trace.tight_bounds[1]

        # Round bounds to nice logarithmic values if near decade boundaries
        if (np.log10(min_bound) % 1) < cls.LOWER_BOUND_THRESHOLD:
            min_bound = 10**int(np.log10(min_bound))
        if (np.log10(max_bound) % 1) > cls.UPPER_BOUND_THRESHOLD:
            max_bound = 10**(int(np.log10(max_bound))+1)

        return (min_bound / cls.BOUND_EDGE_SCALE, max_bound * cls.BOUND_EDGE_SCALE)

    @classmethod
    def _create_and_save_graph(cls, x_values, intensities, graph_file,
                               xtitle, ytitle, xscale, xbounds,
                               legend=None, post_process_callback=None):
        """
        Create a GPCTraceGraph and save it to file.

        This is a shared helper method used by all graph creation classmethods.

        Parameters
        ----------
        x_values : np.ndarray
            The x-axis values (retention times or molecular weights).
        intensities : np.ndarray
            Stacked 2D array of normalized intensities.
        graph_file : str
            Path where the graph should be saved.
        xtitle : str
            Label for the x-axis.
        ytitle : str
            Label for the y-axis.
        xscale : str
            Scale for x-axis ('linear' or 'log').
        xbounds : Tuple[float, float] or None
            Optional bounds for x-axis.
        legend : list of str, optional
            Legend labels for the traces.
        post_process_callback : callable, optional
            Optional callback for additional customization.
        """
        if intensities.ndim > 1:
            scheme='viridis'
        else:
            scheme = 'black'
        
        graph = cls(
            x_values=x_values,
            y_values=intensities,
            xtitle=xtitle,
            ytitle=ytitle,
            xscale=xscale,
            legend=legend,
            color_scheme=scheme
        )

        if xbounds is not None:
            graph.set_xbounds(xbounds)
        graph.set_ybounds((cls.DEFAULT_Y_MIN, cls.DEFAULT_Y_MAX))

        if post_process_callback is not None:
            fig = graph._create_plot(post_process_callback=post_process_callback)
            fig.tight_layout()
            fig.savefig(graph_file)
            plt.close(fig)
        else:
            graph.save_graph(graph_file)

    @classmethod
    def rt_graph_from_data(cls, instrument, data_file, graph_file,
                           legend=None, set_bounds=None):
        """
        Creates and saves a retention time graph from raw GPC data

        This is a convenience method for the common task of creating a
        normalized retention time plot from GPC data files.

        Parameters
        ----------
        instrument : str
            Instrument type (e.g., 'tosoh').
        data_file : str
            Path to GPC data file.
        graph_file : str
            Path where the graph should be saved.
        legend : list of str, optional
            Legend labels for the traces, if any.
        set_bounds: str or tuple, optional
            If None, uses the default picked bounds, if a tuple, sets
            the bounds to the specified tuple

        Returns
        -------
        None
        """
        data_traces = GPCTrace.from_file(
            instrument, data_file, correction='span'
        )

        traces = []
        
        for trace in data_traces:
            traces.append(trace.restrict_retention_times(set_bounds))
            traces[-1].correct_baseline('span')

        # Stack all trace intensities into a 2D array
        retention_times = traces[0].retention_times
        intensities_list = [
            trace.get_normalized_intensities() for trace in traces
        ]
        intensities = np.column_stack(intensities_list)

        # Create and save graph using shared helper
        cls._create_and_save_graph(
            x_values=retention_times,
            intensities=intensities,
            graph_file=graph_file,
            xtitle='Retention Time (min)',
            ytitle='Intensity (A.U.)',
            xscale='linear',
            xbounds=set_bounds,
            legend=legend
        )

    @classmethod
    def mw_graph_from_data(cls, instrument, data_file, calibration,
                           graph_file, legend=None, show_bounds=False,
                           set_bounds=None):
        """
        Creates and saves a molecular weight graph from raw GPC data

        This is a convenience method for the common task of creating a
        normalized molecular weight plot from GPC data files.

        Parameters
        ----------
        instrument : str
            Instrument type (e.g., 'tosoh').
        data_file : str
            Path to GPC data file.
        calibration: dict or str
            Calibration data used to generate molecular weights from the
            retention times. Can be either:
            - dict: Direct calibration with 'type' and 'params' keys
            - str: Path string in format 'filepath:calibration_name'
        graph_file : str
            Path where the graph should be saved.
        legend : list of str, optional
            Legend labels for the traces, if any.
        show_bounds : bool, optional
            Whether to show integration bounds for the auto-picked peaks
        set_bounds: str or tuple, optional
            If None, uses the default picked bounds, if a tuple, sets
            the bounds to the specified tuple

        Returns
        -------
        PolymerSample
            Information about the polymer sample

        Examples
        --------
        >>> # Using dict calibration (backward compatible)
        >>> cal = {'type': 'cubic', 'params': [-0.0017, 0.064, -1.197, 14.035]}
        >>> sample = GPCTraceGraph.mw_graph_from_data('tosoh', 'data.txt',
        ...                                            cal, 'output.png')

        >>> # Using filepath string (new method)
        >>> sample = GPCTraceGraph.mw_graph_from_data('tosoh', 'data.txt',
        ...                                            '../data/calibrations.json:sample_calibration',
        ...                                            'output.png')
        """
        traces = GPCTrace.from_file(
            instrument, data_file, calibration, bounds=set_bounds,
            correction='span'
        )

        # Validate calibration was applied
        if traces[0].molecular_weights is None:
            raise ValueError(
                'Calibration failed - molecular weights could not be calculated. '
                'Check calibration parameters.'
            )

        # Stack all trace intensities into a 2D array
        molecular_weights = traces[0].molecular_weights
        intensities_list = [
            trace.get_normalized_intensities() for trace in traces
        ]
        intensities = np.column_stack(intensities_list)

        # Calculate bounds
        xbounds = set_bounds if set_bounds is not None else cls._calculate_mw_bounds(traces)

        # Define callback to add integration bounds if requested
        def add_integration_bounds(fig, ax):
            """Add shaded rectangles showing peak integration bounds"""
            _, _, left_bounds, right_bounds = traces[0].peak_finder()
            for left, right in zip(left_bounds, right_bounds):
                bounds_rect = patches.Rectangle(
                    (left, -1), right-left, 3, alpha=0.10,
                    facecolor='#13294b', linewidth=0
                )
                edge_rect = patches.Rectangle(
                    (left, -1), right-left, 3, fill=False,
                    color='#13294b', linewidth=2, linestyle='--'
                )
                ax.add_patch(bounds_rect)
                ax.add_patch(edge_rect)

        # Save graph with optional bounds visualization
        if show_bounds:
            if len(traces) > 1:
                raise ValueError(
                    f'Peak calculation only supported for one trace, but {len(traces)} found'
                )
            cls._create_and_save_graph(
                x_values=molecular_weights,
                intensities=intensities,
                graph_file=graph_file,
                xtitle='Molecular Weight (g/mol)',
                ytitle='Intensity (A.U.)',
                xscale='log',
                xbounds=xbounds,
                legend=legend,
                post_process_callback=add_integration_bounds
            )
            return traces[0].analyze_peaks()
        else:
            cls._create_and_save_graph(
                x_values=molecular_weights,
                intensities=intensities,
                graph_file=graph_file,
                xtitle='Molecular Weight (g/mol)',
                ytitle='Intensity (A.U.)',
                xscale='log',
                xbounds=xbounds,
                legend=legend
            )
            # Return polymer analysis if single trace, empty PolymerSample if multiple
            if len(traces) == 1:
                return traces[0].analyze_peaks()
            else:
                return PolymerSample([])

    @classmethod
    def mw_graph_from_trace(cls, traces, graph_file, legend=None,
                            set_bounds=None):
        """
        Creates and saves a molecular weight graph from GPCTrace objects

        This is a convenience method for creating a normalized molecular weight
        plot from pre-processed GPCTrace objects.

        Parameters
        ----------
        traces : GPCTrace or Tuple[GPCTrace, ...]
            One or more GPCTrace objects to plot. All traces must have
            calibration data (molecular weights).
        graph_file : str
            Path where the graph should be saved.
        legend : list of str, optional
            Legend labels for the traces, if any.
        set_bounds : tuple, optional
            If provided, sets the x-axis bounds to the specified tuple (min, max).
            If None, uses automatically calculated bounds based on peak positions.

        Returns
        -------
        None

        Raises
        ------
        MissingCalibrationError
            If any trace does not have calibration data (molecular weights).

        Examples
        --------
        >>> # Create traces from file with calibration
        >>> traces = GPCTrace.from_file('tosoh', 'data.txt', calibration)
        >>> GPCTraceGraph.mw_graph_from_trace(traces[0], 'output.png')

        >>> # Multiple traces with legend
        >>> GPCTraceGraph.mw_graph_from_trace(traces, 'output.png', legend=['Sample 1'])
        """
        # Convert single trace to tuple for uniform handling
        traces = cls._prepare_trace_data(traces)

        # Validate all traces have calibration
        for i, trace in enumerate(traces):
            if not trace.has_calibration:
                raise MissingCalibrationError(
                    f'Trace {i} does not have calibration data. '
                    'All traces must have molecular weights calculated.'
                )

        # Stack all trace intensities into a 2D array
        molecular_weights = traces[0].molecular_weights
        intensities_list = [
            trace.get_normalized_intensities() for trace in traces
        ]
        intensities = np.column_stack(intensities_list)

        # Calculate bounds
        xbounds = set_bounds if set_bounds is not None else cls._calculate_mw_bounds(traces)

        # Create and save graph using shared helper
        cls._create_and_save_graph(
            x_values=molecular_weights,
            intensities=intensities,
            graph_file=graph_file,
            xtitle='Molecular Weight (g/mol)',
            ytitle='Intensity (A.U.)',
            xscale='log',
            xbounds=xbounds,
            legend=legend
        )

    @classmethod
    def rt_graph_from_trace(cls, traces, graph_file, legend=None,
                            set_bounds=None):
        """
        Creates and saves a retention time graph from GPCTrace objects

        This is a convenience method for creating a normalized retention time
        plot from pre-processed GPCTrace objects.

        Parameters
        ----------
        traces : GPCTrace or Tuple[GPCTrace, ...]
            One or more GPCTrace objects to plot. Calibration is not required.
        graph_file : str
            Path where the graph should be saved.
        legend : list of str, optional
            Legend labels for the traces, if any.
        set_bounds : tuple, optional
            If provided, sets the x-axis bounds to the specified tuple (min, max).
a            If None, no bounds are applied.

        Returns
        -------
        None

        Examples
        --------
        >>> # Create traces from file
        >>> traces = GPCTrace.from_file('tosoh', 'data.txt')
        >>> GPCTraceGraph.rt_graph_from_trace(traces[0], 'output.png')

        >>> # Multiple traces with legend
        >>> GPCTraceGraph.rt_graph_from_trace(traces, 'output.png', legend=['Sample 1'])
        """
        # Convert single trace to tuple for uniform handling
        traces = cls._prepare_trace_data(traces)

        # Stack all trace intensities into a 2D array
        retention_times = traces[0].retention_times
        intensities_list = [
            trace.get_normalized_intensities() for trace in traces
        ]
        intensities = np.column_stack(intensities_list)

        # Create and save graph using shared helper
        cls._create_and_save_graph(
            x_values=retention_times,
            intensities=intensities,
            graph_file=graph_file,
            xtitle='Retention Time (min)',
            ytitle='Intensity (A.U.)',
            xscale='linear',
            xbounds=set_bounds,
            legend=legend
        )

