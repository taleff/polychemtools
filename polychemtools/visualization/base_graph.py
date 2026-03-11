"""
Base graph visualization classes

This module provides abstract base classes for creating matplotlib graphs.
"""

import os
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod


class BaseGraph(ABC):
    """
    Abstract base class for graph visualization

    Provides common functionality for creating, configuring, and saving
    matplotlib graphs. Subclasses must implement the _create_plot method
    to define specific plot types.

    Attributes
    ----------
    x_values : np.ndarray
        A 1D numpy array containing the independent variable for the
        visualized data
    y_values : np.ndarray
        A numpy array containing the dependent variables to be plotted
    xtitle : str
        The x-axis label
    ytitle : str
        The y-axis label
    xbounds : tuple or None
        Optional (min, max) bounds for x-axis
    ybounds : tuple or None
        Optional (min, max) bounds for y-axis
    stylesheet : str
        Path to matplotlib stylesheet file used for plot styling
    """

    COLOR_SCHEME = {
        'viridis': lambda x: mpl.colormaps['viridis'](np.linspace(0.8, 0, x)),
        'black': lambda x: ['#000000' for _ in range(x)],
    }

    def __init__(self, x_values: np.ndarray, y_values: np.ndarray,
                 xtitle, ytitle, stylesheet = None):
        """
        Initialize a BaseGraph object

        Parameters
        ----------
        x_values : np.ndarray
            A 1D numpy array containing the independent variable for the
            visualized data
        y_values : np.ndarray
            A numpy array containing the dependent variables to be plotted
        xtitle : str
            The axis title for the x-axis
        ytitle : str
            The axis title for the y-axis
        stylesheet : str, optional
            Path to a matplotlib stylesheet file. If None, uses the default
            stylesheet located at tools/visualization/default.mplstyle

        Raises
        ------
        ValueError
            If x_values and y_values lengths don't match
        """
        # Set default stylesheet if not provided
        if stylesheet is None:
            stylesheet = os.path.join(
                os.path.dirname(__file__),
                'default.mplstyle'
            )
        self.stylesheet = stylesheet

        # Validate data dimensions
        self._validate_data(x_values, y_values)

        # Store data and configuration
        self.x_values = x_values
        self.y_values = y_values
        self.xtitle = xtitle
        self.ytitle = ytitle

        # Optional bounds to apply when plot is created
        self.xbounds = None
        self.ybounds = None

    def _validate_data(self, x_values, y_values):
        """
        Validate that x and y data have compatible dimensions

        Parameters
        ----------
        x_values : np.ndarray
            The x-axis data
        y_values : np.ndarray
            The y-axis data

        Raises
        ------
        ValueError
            If dimensions are incompatible
        """
        if len(x_values) != len(y_values):
            raise ValueError(
                f'The x_values length ({len(x_values)}) does not match '
                f'the y_values length ({len(y_values)})'
            )

    def set_xbounds(self, xbounds):
        """
        Set the x-axis limits to be applied when the graph is saved

        Parameters
        ----------
        xbounds : tuple
            A tuple of (min, max) for the x-axis bounds

        Raises
        ------
        ValueError
            If max bound is not greater than min bound
        """
        if xbounds[1] <= xbounds[0]:
            raise ValueError(
                f'Max x-bound ({xbounds[1]}) must be greater than '
                f'min x-bound ({xbounds[0]})'
            )
        self.xbounds = xbounds

    def set_ybounds(self, ybounds):
        """
        Set the y-axis limits to be applied when the graph is saved

        Parameters
        ----------
        ybounds : tuple
            A tuple of (min, max) for the y-axis bounds

        Raises
        ------
        ValueError
            If max bound is not greater than min bound
        """
        if ybounds[1] <= ybounds[0]:
            raise ValueError(
                f'Max y-bound ({ybounds[1]}) must be greater than '
                f'min y-bound ({ybounds[0]})'
            )
        self.ybounds = ybounds

    @abstractmethod
    def _create_plot(self):
        """
        Create the matplotlib figure with all configuration

        This method must be implemented by subclasses to define
        the specific plot type (line, scatter, bar, etc.)

        Returns
        -------
        fig : plt.Figure
            The created figure object
        """
        pass

    def _apply_bounds(self, ax):
        """
        Apply x and y bounds to the axes if they are set

        Parameters
        ----------
        ax : plt.Axes
            The axes object to apply bounds to
        """
        if self.xbounds is not None:
            ax.set_xlim(self.xbounds)

        if self.ybounds is not None:
            ax.set_ylim(self.ybounds)

    def save_graph(self, filename):
        """
        Save a graph of the data at the specified file location

        Creates the plot, saves it to the file, and automatically closes
        the figure to free resources.

        Parameters
        ----------
        filename : str
            The name the file should be saved as
        """
        fig = self._create_plot()
        fig.tight_layout()
        fig.savefig(filename)
        plt.close(fig)
        
