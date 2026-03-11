import numpy as np
from scipy import signal
from scipy.optimize import least_squares
from dataclasses import dataclass
from typing import List
from ..processing.gpc_data_processor import GPCData
from ..utils.log_normal import LogNormal
from ..utils.calibration_loader import resolve_calibration


class MissingCalibrationError(Exception):
    """Raised when operations that require a calibration are used without a calibration"""
    pass


class NoPeakError(Exception):
    """Raised when operations that require a peak are used with no peaks"""
    pass


class GPCTrace:
    """
    Object representing a single GPC trace with methods for analysis

    Attributes
    ----------
    retention_times : np.ndarray
        A 1D numpy array containing the retention times at which
        the intensities are measured
    molecular_weights : np.ndarray or None
        A 1D numpy array containing the molecular weights at which
        the intensities are measured according to calibration
        by polystyrene standards. If None, no calibration file
        was specified
    intensities: np.ndarray
        A 1D numpy array containing the measured intensities of the
        GPC
    """
    CALIBRATION_TYPES = {
        'linear': lambda x, a, b: 10**(a*x+b),
        'cubic': lambda x, a, b, c, d: 10**(a*x**3+b*x**2+c*x+d)
    }

    # Peak detection parameters
    # These constants control automatic peak detection in GPC traces

    # Minimum absolute intensity required for peak detection (a.u.)
    PEAK_HEIGHT_THRESHOLD = 0

    # Minimum prominence relative to surrounding baseline (0-1 scale)
    PEAK_PROMINENCE = 0.2

    # Minimum peak width in data points
    # Value of 5 prevents spurious single-point noise from being detected
    PEAK_WIDTH = 5

    # Minimum molecular weight threshold for valid polymer peaks (g/mol)
    # Filters out low-MW noise and solvent peaks below 500 g/mol
    MINIMUM_POLYMER_MW = 500

    # Relative height at which peak bounds are calculated (0-1 scale)
    # Value of 0.99 (99% of peak height) captures most of the peak
    # while avoiding baseline noise. Must be high enough to accurately
    # capture the peak area while staying below 1.0 to prevent including
    # large portions of baseline noise.
    BASELINE_THRESHOLD = 0.99

    def __init__(self, retention_times, intensities, calibration=None):
        """
        Initializes a single GPCTrace object

        Parameters
        ----------
        retention_times : np.ndarray
            A 1D numpy array containing the retention times at which
            the intensities are measured
        intensities: np.ndarray
            A 1D numpy array containing the measured intensities of the
            GPC
        calibration: dict, str, or None
            Calibration data used to generate molecular weights from the
            retention times. Can be either:
            - dict: Direct calibration with 'type' and 'params' keys
            - str: Path string in format 'filepath:calibration_name'
            - None: No calibration applied

        Raises
        ------
        ValueError
            If retention_times and intensities are not the same length
        ValueError
            If the retention times are not monotonically increasing
        """
        if len(retention_times) != len(intensities):
            raise ValueError(
                f'The retention time length ({len(retention_times)}) does not match '
                f'the intensities length ({len(intensities)})'
            )

        if not np.all(np.diff(retention_times) > 0):
            raise ValueError(
               'Retention times are not monotonically increasing'
            )

        self.retention_times = retention_times
        self.intensities = intensities

        if calibration is not None:
            resolved_calibration = resolve_calibration(calibration)
            self.input_calibration(resolved_calibration)
        else:
            self.molecular_weights = None

    @classmethod
    def from_file(cls, instrument, file_path, calibration=None,
                  bounds=None, correction=None):
        """
        Create GPCTrace objects from a data file.

        Parameters
        ----------
        instrument : str
            Instrument type (e.g., 'tosoh').
        file_path : str
            Path to GPC data file.
        calibration : dict, str, or None, optional
            Calibration parameters applied to all traces. Can be either:
            - dict: Direct calibration with 'type' and 'params' keys
            - str: Path string in format 'filepath:calibration_name'
            - None: No calibration applied
        bounds: Tuple[float, float], optional
            The molecular weight bounds to restrict the trace for
        correction: str, optional
            The baseline correction method

        Returns
        -------
        Tuple[GPCTrace, ...]
            Tuple of GPCTrace objects, one for each trace in the file.

        Examples
        --------
        >>> # Using dict calibration
        >>> cal = {'type': 'cubic', 'params': [1, 2, 3, 4]}
        >>> traces = GPCTrace.from_file('tosoh', 'data.txt', cal)

        >>> # Using filepath string
        >>> traces = GPCTrace.from_file('tosoh', 'data.txt',
        ...                             '../calibrations.json:sample_calibration')
        """
        processor = GPCData.from_file(instrument=instrument,
                                      file_path=file_path)
        traces = []

        for i in range(len(processor)):
            trace = cls(
                retention_times=processor.retention_times,
                intensities=processor.intensities[:, i],
                calibration=calibration
            )
            if bounds is not None:
                trace = trace.restrict_molecular_weights(bounds)
            trace.correct_baseline(correction)
            traces.append(trace)

        return tuple(traces)

    def input_calibration(self, calibration):
        """
        Uses a calibration to calculate molecular weights from retention times

        Parameters
        ----------
        calibration: dict
            Calibration data used to generate molecular weights from the
            retention times. The 'type' key corresponds to the calibration
            type while the 'params' key corresponds to the parameters for
            the calibration

        Raises
        ------
        ValueError
            If calibration type is not supported
        """
        calibration_type = calibration['type']
        if calibration_type not in self.CALIBRATION_TYPES:
            raise ValueError(
                f"Unsupported calibration type '{calibration_type}'. "
                f"Supported types: {list(self.CALIBRATION_TYPES.keys())}"
            )

        calibration_generator = self.CALIBRATION_TYPES[calibration_type]
        self.molecular_weights = calibration_generator(
            self.retention_times, *calibration['params']
        )

    def _validate_bounds(self, bounds):
        """
        Validate that bounds are monotonically increasing.

        Parameters
        ----------
        bounds : Tuple[float, float]
            Lower and upper bounds to validate.

        Raises
        ------
        ValueError
            If the second bound is not greater than the first.
        """
        if bounds[1] <= bounds[0]:
            raise ValueError(
                f'The second bound ({bounds[1]}) must be greater than the first ({bounds[0]})'
            )

    def _require_calibration(self):
        """
        Ensure calibration data exists.

        Raises
        ------
        MissingCalibrationError
            If no calibration information has been provided.
        """
        if self.molecular_weights is None:
            raise MissingCalibrationError('No calibration information provided')

    def _find_raw_peaks(self):
        """
        Find peaks in the intensity data using scipy.

        Returns
        -------
        peak_indices : np.ndarray
            Array of indices where peaks were detected
        peak_properties : dict
            Dictionary containing peak properties (heights, prominences, etc.)
        """
        peak_indices, peak_properties = signal.find_peaks(
            self.intensities,
            height=self.PEAK_HEIGHT_THRESHOLD,
            prominence=self.PEAK_PROMINENCE,
            width=self.PEAK_WIDTH
        )
        return peak_indices, peak_properties

    def _calculate_peak_bounds(self, peak_indices):
        """
        Calculate the left and right bounds for each detected peak.

        Parameters
        ----------
        peak_indices : np.ndarray
            Indices of detected peaks in the intensity array

        Returns
        -------
        lower_bounds : np.ndarray
            Array of lower bound indices (lower retention time, higher MW)
        upper_bounds : np.ndarray
            Array of upper bound indices (upper retention time, lower MW)
        """
        peak_widths = signal.peak_widths(
            self.intensities, peak_indices, rel_height=self.BASELINE_THRESHOLD
        )

        # Convert interpolated positions to integer indices
        # Note: lower_bounds corresponds to lower retention time (higher MW)
        # upper_bounds corresponds to upper retention time (lower MW)
        lower_bounds = peak_widths[2].astype(int)
        upper_bounds = peak_widths[3].astype(int)

        return lower_bounds, upper_bounds

    def _convert_peak_data_to_mw(self, peak_indices, peak_heights,
                                 lower_bounds, upper_bounds):
        """
        Convert peak data from retention time indices to molecular weights.

        Since GPC retention time decreases with molecular weight, this method
        also reverses all arrays to present data in decreasing MW order.

        Parameters
        ----------
        peak_indices : np.ndarray
            Indices of peaks in the intensity array
        peak_heights : np.ndarray
            Heights of each peak
q        lower_bounds : np.ndarray
            Lower bound indices (lower RT, higher MW)
        upper_bounds : np.ndarray
            Upper bound indices (upper RT, lower MW)

        Returns
        -------
        peak_mw : np.ndarray
            Molecular weights at peak positions (descending order)
        peak_heights : np.ndarray
            Peak heights (reordered to match MW order)
        left_mw_bounds : np.ndarray
            Molecular weights at left peak edges (descending order)
        right_mw_bounds : np.ndarray
            Molecular weights at right peak edges (descending order)

        Raises
        ------
        MissingCalibrationError
            If self.molecular_weights is None due to no calibration
        """
        self._require_calibration()
        
        # Convert indices to molecular weights
        peak_mw = self.molecular_weights[peak_indices]
        left_mw_bounds = self.molecular_weights[upper_bounds]
        right_mw_bounds = self.molecular_weights[lower_bounds]

        # Reverse arrays to present data in descending MW order
        # (GPC retention time increases as MW decreases)
        return (
            peak_mw[::-1],
            peak_heights[::-1],
            left_mw_bounds[::-1],
            right_mw_bounds[::-1]
        )

    def _filter_valid_peaks(self, peak_mw, peak_heights, left_bounds,
                            right_bounds):
        """
        Filter out peaks below the minimum molecular weight threshold.

        Parameters
        ----------
        peak_mw : np.ndarray
            Molecular weights at peak positions
        peak_heights : np.ndarray
            Heights of each peak
        left_bounds : np.ndarray
            Molecular weights at left peak edges
        right_bounds : np.ndarray
            Molecular weights at right peak edges

        Returns
        -------
        Filtered arrays containing only peaks above MINIMUM_POLYMER_MW

        Raises
        ------
        NoPeakError
            If no peaks remain after filtering
        """
        valid_peaks = peak_mw > self.MINIMUM_POLYMER_MW

        if not np.any(valid_peaks):
            raise NoPeakError('No peaks found in GPC trace')

        return (
            peak_mw[valid_peaks],
            peak_heights[valid_peaks],
            left_bounds[valid_peaks],
            right_bounds[valid_peaks]
        )

    @property
    def has_calibration(self):
        """
        Check if calibration data exists.

        Returns
        -------
        bool
            True if calibration data is available, False otherwise.
        """
        return self.molecular_weights is not None

    def retention_time_index(self, retention_time):
        """
        Finds the index of a particular retention_time

        Parameters
        ----------
        retention_time : float
            Molecular weight for which to find the index
        """
        return np.searchsorted(self.retention_times, retention_time)

    def molecular_weight_index(self, molecular_weight):
        """
        Finds the index of a particular molecular weight

        Parameters
        ----------
        molecular_weight : float
            Molecular weight for which to find the index

        Raises
        ------
        MissingCalibrationError
            If self.molecular_weights is None due to no calibration
        """
        self._require_calibration()

        # We must negate the molecular weight since the array will be
        # monotonically decreasing
        return np.searchsorted(
            -self.molecular_weights, -molecular_weight, side='right'
        )

    def moment(self, n, bounds):
        """
        Calculates the nth moment of the molecular weight distribution

        Parameters
        ----------
        n : int
            The degree of the moment to be calculated
        bounds : Tuple[float, float]
            A tuple (min, max) specifying the molecular weight range
            for the calculation

        Returns
        -------
        moment : float
            The nth moment of the molecular weight distribution

        Raises
        ------
        MissingCalibrationError
            If self.molecular_weights is None due to no calibration
        ValueError
            If bounds are not monotonically increasing
        """
        self._require_calibration()
        self._validate_bounds(bounds)

        left_index = self.molecular_weight_index(bounds[1])
        right_index = self.molecular_weight_index(bounds[0])

        # Calculate nth moment: integral of I(M) * M^(n-1) dM
        # (GPC intensity already includes one factor of M)
        moment = np.trapezoid(
            self.intensities[left_index:right_index] *
            self.molecular_weights[left_index:right_index] ** (n - 1),
            self.molecular_weights[left_index:right_index]
        )

        # The molecular weights monotonically decrease so we must take
        # the absolute value to get a positive number
        return abs(moment)

    def number_average_molecular_weight(self, bounds):
        """
        Finds the number average molecular weight of the trace

        Parameters
        ----------
        bounds : Tuple[float, float]
            A tuple (min, max) specifying the molecular weight range
            for the calculation

        Returns
        -------
        number_average : float
            The number average molecular weight

        Raises
        ------
        MissingCalibrationError
            If self.molecular_weights is None due to no calibration
        ValueError
            If bounds are not monotonically increasing or contain no signal
        """
        first_moment = self.moment(1, bounds)
        zeroeth_moment = self.moment(0, bounds)

        if zeroeth_moment < 1e-10:
            raise ValueError(
                f'No signal detected in the specified bounds {bounds}. '
                f'Zeroth moment: {zeroeth_moment}'
            )

        return first_moment / zeroeth_moment
    
    def weight_average_molecular_weight(self, bounds):
        """
        Finds the weight average molecular weight of the trace

        Parameters
        ----------
        bounds : Tuple[float, float]
            A tuple (min, max) specifying the molecular weight range
            for the calculation

        Returns
        -------
        weight_average : float
            The weight average molecular weight

        Raises
        ------
        MissingCalibrationError
            If self.molecular_weights is None due to no calibration
        ValueError
            If bounds are not monotonically increasing or contain no signal
        """
        second_moment = self.moment(2, bounds)
        first_moment = self.moment(1, bounds)

        if first_moment < 1e-10:
            raise ValueError(
                f'No signal detected in the specified bounds {bounds}. '
                f'First moment: {first_moment}'
            )

        return second_moment / first_moment

    def dispersity(self, bounds):
        """
        Finds the dispersity of the trace

        Parameters
        ----------
        bounds : Tuple[float, float]
            A tuple (min, max) specifying the molecular weight range
            for the calculation

        Returns
        -------
        dispersity : float
            The dispersity

        Raises
        ------
        MissingCalibrationError
            If self.molecular_weights is None due to no calibration
        ValueError
            If bounds are not monotonically increasing
        """
        mn = self.number_average_molecular_weight(bounds)
        mw = self.weight_average_molecular_weight(bounds)
        return mw / mn

    def correct_baseline(self, correction):
        """
        Corrects the baseline of the intensities trace according to
        the specified method

        Parameters
        ----------
        correction : str
            The baseline correction method (e.g. span)
        """
        if correction == 'span':
            slope = (
                (self.intensities[-1]-self.intensities[0])/
                (self.retention_times[-1]-self.retention_times[0])
            )
            self.intensities = self.intensities - (
                slope * (self.retention_times - self.retention_times[0]) +
                self.intensities[0]
            )
        elif correction is None:
            return None
        else:
            raise ValueError(f'{correction} is not a valid baseline correction technique')

    def restrict_retention_times(self, bounds):
        """
        Creates a new instance of GPCTrace with the retention time
        range restricted

        Parameters
        ----------
        bounds : Tuple[float, float]
            A tuple (min, max) specifying the retention time range

        Returns
        -------
        new_trace : GPCTrace
            A new GPCTrace object with the restricted retention time
            range

        Raises
        ------
        ValueError
            If bounds are not monotonically increasing
        """
        self._validate_bounds(bounds)

        left_index = self.retention_time_index(bounds[0])
        right_index = self.retention_time_index(bounds[1])

        new_trace = GPCTrace(
            retention_times=self.retention_times[left_index:right_index],
            intensities=self.intensities[left_index:right_index],
        )

        if self.molecular_weights is not None:
            new_trace.molecular_weights = self.molecular_weights[left_index:right_index]

        return new_trace

    def restrict_molecular_weights(self, bounds):
        """
        Creates a new instance of GPCTrace with the molecular weight
        range restricted

        Parameters
        ----------
        bounds : Tuple[float, float]
            A tuple (min, max) specifying the molecular weight range
            for the calculation

        Returns
        -------
        new_trace : GPCTrace
            A new GPCTrace object with the restricted molecular weight
            range

        Raises
        ------
        MissingCalibrationError
            If self.molecular_weights is None due to no calibration
        ValueError
            If bounds are not monotonically increasing
        """
        self._require_calibration()
        self._validate_bounds(bounds)

        left_index = self.molecular_weight_index(bounds[1])
        right_index = self.molecular_weight_index(bounds[0])

        new_trace = GPCTrace(
            retention_times=self.retention_times[left_index:right_index],
            intensities=self.intensities[left_index:right_index],
        )
        new_trace.molecular_weights = self.molecular_weights[left_index:right_index]

        return new_trace

    def peak_area(self, bounds, mw=False):
        """
        Finds the area of a peak in the chromatogram.

        Parameters
        ----------
        bounds : Tuple[float, float]
            A tuple (min, max) specifying the retention time range
            for the calculation

        Returns
        -------
        peak_area : float
            The area of the peak. This has whatever units retention times
            are in. This is useful for comparing the mass ratio of different
            peaks
        mw : bool
            Whether the bounds are given in retention time or
            molecular_weight

        Raises
        ------
        ValueError
            If bounds are not monotonically increasing
        """
        self._validate_bounds(bounds)

        if mw:
            left_index = self.molecular_weight_index(bounds[1])
            right_index = self.molecular_weight_index(bounds[0])
        else: 
            left_index = self.retention_time_index(bounds[0])
            right_index = self.retention_time_index(bounds[1])

        return np.trapezoid(
            self.intensities[left_index:right_index],
            self.retention_times[left_index:right_index]
        )

    def peak_finder(self):
        """
        Finds the location of peaks and their widths in the GPC trace

        Returns
        -------
        peak_list : np.ndarray
            A list of peaks present in the GPC trace
        peak_heights : np.ndarray
            The heights of each of the found peaks
        left_bounds : np.ndarray
            The molecular weights of the left edges of the peaks
        right_bounds : np.ndarray
            The molecular weights of the right edges of the peaks

        Raises
        ------
        MissingCalibrationError
            If self.molecular_weights is None due to no calibration
        NoPeakError
            If there are no valid peaks in the GPC trace
        """
        self._require_calibration()

        # Find peaks in the chromatogram
        peak_indices, peak_properties = self._find_raw_peaks()

        # Calculate bounds for each peak
        lower_peak_ips, upper_peak_ips = self._calculate_peak_bounds(peak_indices)

        # Resolve overlapping peak bounds by ensuring non-overlapping regions
        # Peaks are ordered by increasing retention time (decreasing MW)
        # lower_peak_ips[i] = left edge (lower RT), upper_peak_ips[i] = right edge (higher RT)
        #
        # Process left-to-right: each peak's left bound must not extend past
        # the previous peak's right bound. This handles cases where a large peak
        # might otherwise encompass multiple earlier peaks.
        for i in range(len(peak_indices)-1):
            if upper_peak_ips[i] > peak_indices[i + 1]:
                upper_peak_ips[i+1] = upper_peak_ips[i]
                upper_peak_ips[i] = lower_peak_ips[i + 1]

        # Process right-to-left: each peak's right bound must not extend past
        # the next peak's left bound.
        for i in range(len(peak_indices)-1, 0, -1):
            if lower_peak_ips[i] < peak_indices[i - 1]:
                lower_peak_ips[i-1] = lower_peak_ips[i]
                lower_peak_ips[i] = upper_peak_ips[i - 1]

        # Convert indices to molecular weights and reverse for descending MW order
        peak_mw, peak_heights, left_mw, right_mw = self._convert_peak_data_to_mw(
            peak_indices,
            peak_properties['peak_heights'],
            lower_peak_ips,
            upper_peak_ips
        )

        # Filter out peaks below minimum molecular weight threshold
        return self._filter_valid_peaks(peak_mw, peak_heights, left_mw, right_mw)

    @property
    def peaks(self) -> np.ndarray:
        """
        Finds the location of peaks in the GPC trace

        Returns
        -------
        peak_list : np.ndarray
            A list of peaks present in the GPC trace

        Raises
        ------
        MissingCalibrationError
            If self.molecular_weights is None due to no calibration
        NoPeakError
            If there are no valid peaks in the GPC trace
        """
        return self.peak_finder()[0]

    def analyze_peaks(self):
        """
        Finds peaks in the GPC and analyzes them

        Returns
        -------
        PolymerSample
            A PolymerSample object containing analyzed polymer data
            for each peak (Mn, Mw, and dispersity)

        Raises
        ------
        MissingCalibrationError
            If self.molecular_weights is None due to no calibration
        NoPeakError
            If there are no valid peaks in the GPC trace
        """
        peaks = self.peak_finder()
        polymers = []

        for i in range(len(peaks[0])):
            polymer = Polymer(
                self.number_average_molecular_weight((peaks[2][i], peaks[3][i])),
                self.weight_average_molecular_weight((peaks[2][i], peaks[3][i])),
                self.dispersity((peaks[2][i], peaks[3][i]))
            )
            polymers.append(polymer)

        return PolymerSample(polymers)

    @property
    def tight_bounds(self):
        """
        Finds tight bounds that show most of the peaks in the trace

        Returns
        -------
        bounds : tuple
            A tuple (min, max) that contains the molecular weights that
            mostly encompass all relevant peaks

        Raises
        ------
        MissingCalibrationError
            If self.molecular_weights is None due to no calibration
        NoPeakError
            If there are no valid peaks in the GPC trace
        """
        return (
            float(np.min(self.peak_finder()[2])),
            float(np.max(self.peak_finder()[3]))
        )

    def deconvolute(self, parts, bounds):
        """
        Deconvolutes a region of the trace into the specified number
        of log normal Gaussians

        Parameters
        ----------
        parts : int
            The number of Gaussians to deconvolute the region into
        bounds : Tuple[float, float]
            A tuple (min, max) specifying the retention time range
            for the calculation

        Returns
        -------
        gaussians : List[LogNormal]
            A list containing the log normal Gaussians the trace was
            deconvoluted into

        Raises
        ------
        ValueError
            If bounds are not monotonically increasing
        """
        self._validate_bounds(bounds)

        left_index = self.molecular_weight_index(bounds[1])
        right_index = self.molecular_weight_index(bounds[0])
        mws = self.molecular_weights[left_index:right_index]

        # Each gaussian gets a sigma, mu, and scale
        init_guess = np.ones(3*parts)
        init_guess[::3] = 0.3
        init_guess[1::3] = np.linspace(
            np.log(bounds[0]), np.log(bounds[1]), parts
        )

        def residual(x):
            trace = self.intensities[left_index:right_index]
            fit = np.zeros(len(trace))
            for i in range(parts):
                fit += LogNormal(x[3*i], x[3*i+1], x[3*i+2]).pdf(mws)
            return fit - trace

        # Set bounds: sigma > 0, mu within log(bounds), scale > 0
        lower_bounds = np.zeros(3 * parts)
        lower_bounds[::3] = 1e-6  # sigma > 0
        lower_bounds[1::3] = np.log(bounds[0])  # mu >= log(min_mw)
        lower_bounds[2::3] = 1e-6  # scale > 0

        upper_bounds = np.full(3 * parts, np.inf)
        upper_bounds[1::3] = np.log(bounds[1])  # mu <= log(max_mw)

        res = least_squares(residual, init_guess, bounds=(lower_bounds, upper_bounds))

        # Sorting from the smallest mn to the largest
        sort = res.x[1::3].argsort()
        sigma = res.x[::3][sort]
        mu = res.x[1::3][sort]
        scale = res.x[2::3][sort]
        
        return [LogNormal(sigma[i], mu[i], scale[i]) for i in range(parts)]

    def get_normalized_intensities(self):
        """
        Get normalized intensities

        Returns
        -------
        intensities : np.ndarray
            An ndarray that is the intensities normalized to one
        """
        return self.intensities / np.max(self.intensities)

    def get_mole_fractions(self):
        """
        Get the mole fraction distribution for this GPC trace

        Returns
        -------
        intensities : np.ndarray
            An ndarray that is the mole fractions
        """
        mole_fracs = self.intensities / self.molecular_weights
        area = np.trapezoid(mole_fracs[::-1], self.molecular_weights[::-1])
        return mole_fracs / area

    def __len__(self):
        """
        Returns the number of data points that form the trace

        Returns
        -------
        length : int
            The length of self.retention_times
        """
        return len(self.retention_times)

    def __repr__(self):
        """
        Return a string representation of the GPCTrace.

        Returns
        -------
        str
            String representation showing key attributes.
        """
        calib_status = "with calibration" if self.has_calibration else "without calibration"
        return f"GPCTrace({len(self)} points, {calib_status})"


@dataclass
class Polymer:
    """
    Object representing a single polymer and its parameters

    Attributes
    ----------
    mn : float
        The number average molecular weight of the polymer
    mw : float
        The weight average molecular weight of the polymer
    dispersity : float
        The dispersity of the polymer
    """
    mn: float
    mw: float
    dispersity: float

    def __repr__(self):
        return f'Mn: {self.mn:.0f} g/mol; Mw: {self.mw:.0f} g/mol; D: {self.dispersity:.2f}'


@dataclass
class PolymerSample:
    """
    Object representing a sample of multiple polymers and their parameters

    Attributes
    ----------
    polymers: list
        A list of all the polymers in the sample
    """
    polymers: List[Polymer]

    def __repr__(self):
        """String showing each polymer on a separate line"""
        if not self.polymers:
            return "PolymerSample(no polymers)"

        lines = [f"PolymerSample({len(self.polymers)} polymer{'s' if len(self.polymers) > 1 else ''}):"]
        for i, polymer in enumerate(self.polymers, start=1):
            lines.append(f"  Peak {i}: {polymer}")

        return '\n'.join(lines)

    def __len__(self):
        """Return the number of polymers in the sample"""
        return len(self.polymers)

