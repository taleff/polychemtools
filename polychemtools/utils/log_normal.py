"""
Wrapper method for scipy log normal distribution

This module provides extra methods for log normal
"""

from __future__ import annotations

import numpy as np
from typing import Union
from dataclasses import dataclass


@dataclass
class LogNormal:
    """
    Object representing a log normal distribution

    Attributes
    ----------
    sigma : float
        The shape parameter of the log normal Gaussian (must be > 0)
    mu : float
        The shift of the log normal Gaussian
    scale: float
        A scaling factor for the log normal distribution
    """

    sigma: float
    mu: float = 0
    scale: float = 1

    def __post_init__(self):
        """Validate parameters after initialization."""
        if self.sigma <= 0:
            raise ValueError(f"sigma must be positive, got {self.sigma}")

    def pdf(self, x) -> Union[float, np.ndarray]:
        """
        The probability density function

        Parameters
        ----------
        x : float or np.ndarray
            The values at which to evaluate the probability density
            function. Must be positive.

        Returns
        -------
        y : float or np.ndarray
            The values of the probability density function at each
            specified value

        Raises
        ------
        ValueError
            If any x values are <= 0
        """
        # Validate that all x values are positive
        if np.any(np.asarray(x) <= 0):
            raise ValueError("All x values must be positive for log-normal PDF")

        # We multiply by x since this represents an SEC measurement,
        # which usually measures the chain distribution multiplied by
        # chain molecular weight
        coeff = self.scale * (1 / self.sigma / np.sqrt(2 * np.pi))
        return coeff * np.exp(-(np.log(x) - self.mu) ** 2 / (2 * self.sigma ** 2))

    @property
    def mn(self) -> float:
        """
        The number average molecular weight

        Returns
        -------
        mn : float
            The number average molecular weight of the log normal
            Gaussian distribution
        """
        return np.exp(self.mu+self.sigma**2/2)

    @property
    def mw(self) -> float:
        """
        The weight average molecular weight

        Returns
        -------
        mw : float
            The weight average molecular weight of the log normal
            Gaussian distribution
        """
        return np.exp(self.sigma**2) * self.mn

    @property
    def dispersity(self) -> float:
        """
        The dispersity

        Returns
        -------
        dispersity : float
            The dispersity of the log normal Gaussian distribution
        """
        return np.exp(self.sigma**2)

