"""
Graphing scatter plots for kinetic data

This module provides a class for visualizing kinetics data
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional
from .base_graph import BaseGraph


class KineticsGraph(BaseGraph):
    """
    Object representing a scatter plot showing kinetics data

    The plot is created lazily when save_graph() is called, allowing bounds
    to be set before rendering. After saving, the plot is automatically closed
    to free resources.

    Attributes
    ----------
    x_values : np.ndarray
        A 1D numpy array containing the independent variable for the
        visualized data
    y_values: np.ndarray
        A 1D numpy array containing the dependent variable to be
        plotted as a scatter plot
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

    def __init__(
            self,
            x_values: np.ndarray,
            y_values: np.ndarray,
            xtitle: str,
            ytitle: str,
            stylesheet: Optional[str] = None
    ):
        """
        Initializes a single KineticsGraph object

        Parameters
        ----------
        x_values : np.ndarray
            A 1D numpy array containing the independent variable for the
            visualized data
        y_values: np.ndarray
            A 1D numpy array containing the dependent variable to be
            plotted as a scatter plot
        xtitle: str
            The axis title for the x-axis
        ytitle: str
            The axis title for the y-axis
        stylesheet: str, optional
            Path to a matplotlib stylesheet file. If None, uses the default
            stylesheet located at tools/visualization/default.mplstyle

        Raises
        ------
        ValueError
            If x_values and y_values lengths don't match
        """
        # Initialize base class
        super().__init__(x_values, y_values, xtitle, ytitle, stylesheet)

    def _create_plot(self) -> plt.Figure:
        """
        Creates the matplotlib figure with scatter plot and configuration

        Returns
        -------
        fig : plt.Figure
            The created figure object
        """
        plt.style.use(self.stylesheet)
        fig, ax = plt.subplots()

        # Create scatter plot
        ax.scatter(self.x_values, self.y_values)

        # Set axis labels
        ax.set_xlabel(self.xtitle)
        ax.set_ylabel(self.ytitle)

        # Apply bounds using base class method
        self._apply_bounds(ax)

        return fig

