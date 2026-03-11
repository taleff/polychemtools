import pytest
import os
import numpy as np
from polychemtools.processing.data_processor import UnsupportedInstrumentError
from polychemtools.processing.gpc_data_processor import GPCData
from polychemtools.processing.gc_data_processor import GCData, MultiplePeaksFoundError
from polychemtools.processing.dsc_data_processor import DSCData


class TestGPCDataInitialization:
    """Tests for GPCData initialization."""

    @pytest.fixture
    def example_file_path(self):
        """Get path to example GPC data file."""
        return os.path.join('examples', 'sample_gpc_data.txt')

    def test_unsupported_instrument_raises_error(self, example_file_path):
        """Test that unsupported instrument raises appropriate error."""
        with pytest.raises(UnsupportedInstrumentError) as exc_info:
            GPCData.from_file(instrument='fake_gpc', file_path=example_file_path)
        assert 'fake_gpc' in str(exc_info.value)
        assert 'not supported' in str(exc_info.value)

    def test_data_loaded_on_initialization(self, example_file_path):
        """Test that data is loaded during initialization."""
        gpc = GPCData.from_file(instrument='tosoh', file_path=example_file_path)
        assert hasattr(gpc, 'retention_times')
        assert hasattr(gpc, 'intensities')
        assert gpc.retention_times is not None
        assert gpc.intensities is not None

    def test_file_not_found_raises_error(self):
        """Test that missing file raises appropriate error."""
        with pytest.raises((FileNotFoundError, OSError)):
            GPCData.from_file(instrument='tosoh', file_path='nonexistent_file.txt')


class TestGPCDataParsing:
    """Tests for GPC data parsing functionality."""

    @pytest.fixture
    def gpc_data(self):
        """Create GPCData instance for testing."""
        file_path = os.path.join('examples', 'sample_gpc_data.txt')
        return GPCData.from_file(instrument='tosoh', file_path=file_path)

    def test_returns_numpy_arrays(self, gpc_data):
        """Test that parsed data are numpy arrays."""
        assert isinstance(gpc_data.retention_times, np.ndarray)
        assert isinstance(gpc_data.intensities, np.ndarray)

    def test_arrays_same_length(self, gpc_data):
        """Test that retention times and intensities have same length."""
        assert len(gpc_data.retention_times) == len(gpc_data.intensities)

    def test_correct_number_of_data_points(self, gpc_data):
        """Test that correct number of data points are loaded."""
        # File has 18003 lines - 2 header lines = 18001 data points
        assert len(gpc_data.retention_times) == 18001

    def test_retention_time_range(self, gpc_data):
        """Test that retention times span expected range."""
        assert gpc_data.retention_times[0] == pytest.approx(0.0, abs=1e-5)
        assert gpc_data.retention_times[-1] == pytest.approx(30.0, abs=1e-5)

    def test_retention_times_monotonically_increasing(self, gpc_data):
        """Test that retention times increase monotonically."""
        assert np.all(np.diff(gpc_data.retention_times) > 0)

    def test_data_types(self, gpc_data):
        """Test that arrays have numeric dtypes."""
        assert np.issubdtype(gpc_data.retention_times.dtype, np.number)
        assert np.issubdtype(gpc_data.intensities.dtype, np.number)

    def test_no_nan_values(self, gpc_data):
        """Test that parsed data contains no NaN values."""
        assert not np.any(np.isnan(gpc_data.retention_times))
        assert not np.any(np.isnan(gpc_data.intensities))

    def test_first_data_point_values(self, gpc_data):
        """Test first data point has expected values."""
        # From the file: 0.00000	-0.014
        assert gpc_data.retention_times[0] == pytest.approx(0.0, abs=1e-5)
        assert gpc_data.intensities[0] == pytest.approx(-0.014, abs=1e-3)

    def test_last_data_point_values(self, gpc_data):
        """Test last data point has expected values."""
        # From the file: 30.00000	0.306
        assert gpc_data.retention_times[-1] == pytest.approx(30.0, abs=1e-5)
        assert gpc_data.intensities[-1] == pytest.approx(0.306, abs=1e-3)


class TestGCDataInitialization:
    """Tests for GCData initialization."""

    @pytest.fixture
    def example_file_path(self):
        """Get path to example GC data file."""
        return os.path.join('examples', 'sample_gc_data.TXT')

    def test_shimadzu_instrument(self, example_file_path):
        """Test shimadzu instrument specification."""
        gc = GCData(instrument='shimadzu', file_path=example_file_path)
        assert gc.instrument == 'shimadzu'

    def test_data_loaded_on_initialization(self, example_file_path):
        """Test that data is loaded during initialization."""
        gc = GCData(instrument='shimadzu', file_path=example_file_path)
        assert hasattr(gc, 'peak_retention_times')
        assert hasattr(gc, 'peak_areas')
        assert hasattr(gc, 'chromatogram_times')
        assert hasattr(gc, 'chromatogram_intensities')

    def test_unsupported_instrument_raises_error(self, example_file_path):
        """Test that unsupported instrument raises appropriate error."""
        with pytest.raises(UnsupportedInstrumentError) as exc_info:
            GCData(instrument='agilent', file_path=example_file_path)
        assert 'agilent' in str(exc_info.value)
        assert 'not supported' in str(exc_info.value)

    def test_file_not_found_raises_error(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises((FileNotFoundError, OSError)):
            GCData(instrument='shimadzu', file_path='nonexistent_file.txt')


class TestGetPeakAreas:
    """Tests for get_peak_areas method."""

    @pytest.fixture
    def gc_data(self):
        """Create GCData instance for testing."""
        file_path = os.path.join('examples', 'sample_gc_data.TXT')
        return GCData(instrument='shimadzu', file_path=file_path)

    def test_single_peak_exact_match(self, gc_data):
        """Test finding a single peak with exact retention time match."""
        retention_times = [3.521]
        areas = gc_data.get_peak_areas(retention_times)
        assert len(areas) == 1
        assert areas[0] == 5166

    def test_single_peak_within_tolerance(self, gc_data):
        """Test finding a peak within default tolerance."""
        # Peak at 3.521, searching at 3.53 (within 0.10 tolerance)
        retention_times = [3.53]
        areas = gc_data.get_peak_areas(retention_times)
        assert len(areas) == 1
        assert areas[0] == 5166

    def test_multiple_retention_times(self, gc_data):
        """Test finding multiple peaks at different retention times."""
        retention_times = [3.521, 5.337, 10.054]
        areas = gc_data.get_peak_areas(retention_times)
        assert len(areas) == 3
        assert areas[0] == 5166
        assert areas[1] == 1667463702
        assert areas[2] == 1120832

    def test_no_peak_found_returns_none(self, gc_data):
        """Test that None is returned when no peak within tolerance."""
        retention_times = [1.0]  # No peak near 1.0 minutes
        areas = gc_data.get_peak_areas(retention_times)
        assert len(areas) == 1
        assert areas[0] is None

    def test_mixed_found_and_not_found(self, gc_data):
        """Test mixture of found peaks and missing peaks."""
        retention_times = [3.521, 1.0, 10.054, 100.0]
        areas = gc_data.get_peak_areas(retention_times)
        assert len(areas) == 4
        assert areas[0] == 5166
        assert areas[1] is None
        assert areas[2] == 1120832
        assert areas[3] is None

    def test_custom_tolerance(self, gc_data):
        """Test using custom tolerance value."""
        # Peak at 3.521, searching at 3.6 (outside 0.10 but within 0.15)
        retention_times = [3.6]
        areas = gc_data.get_peak_areas(retention_times, tolerance=0.15)
        assert len(areas) == 1
        assert areas[0] == 5166

    def test_tight_tolerance_misses_peak(self, gc_data):
        """Test that tight tolerance misses nearby peaks."""
        # Peak at 3.521, searching at 3.53 (outside 0.005 tolerance)
        retention_times = [3.53]
        areas = gc_data.get_peak_areas(retention_times, tolerance=0.005)
        assert len(areas) == 1
        assert areas[0] is None

    def test_multiple_peaks_within_tolerance_raises_error(self, gc_data):
        """Test that multiple peaks within tolerance raises error."""
        # Peaks at 3.521 and 3.861, searching with large tolerance
        retention_times = [3.7]
        with pytest.raises(MultiplePeaksFoundError) as exc_info:
            gc_data.get_peak_areas(retention_times, tolerance=0.2)

        error_msg = str(exc_info.value)
        assert '2 peaks' in error_msg or 'multiple' in error_msg.lower()
        assert '3.7' in error_msg

    def test_empty_retention_times_list(self, gc_data):
        """Test with empty retention times list."""
        retention_times = []
        areas = gc_data.get_peak_areas(retention_times)
        assert areas == []

    def test_large_peak_area_value(self, gc_data):
        """Test handling of very large peak area values."""
        # Peak at 5.337 has area 1667463702
        retention_times = [5.337]
        areas = gc_data.get_peak_areas(retention_times)
        assert len(areas) == 1
        assert areas[0] == 1667463702
        assert isinstance(areas[0], float)
