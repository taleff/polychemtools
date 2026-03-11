import pytest
import numpy as np
import os
from polychemtools.visualization.trace_graph import TraceGraph


class TestTraceGraphInitialization:
    """Tests for TraceGraph initialization."""

    @pytest.fixture
    def sample_data_2d(self):
        """Create sample 2D data for testing."""
        x = np.linspace(0, 10, 100)
        y1 = np.sin(x)
        y2 = np.cos(x)
        y = np.column_stack([y1, y2])
        return x, y

    @pytest.fixture
    def sample_data_1d(self):
        """Create sample 1D data for testing."""
        x = np.linspace(0, 5, 50)
        y = x**2
        return x, y

    def test_basic_initialization(self, sample_data_2d):
        """Test basic TraceGraph initialization with 2D data."""
        x, y = sample_data_2d
        graph = TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="Time",
            ytitle="Signal"
        )
        assert hasattr(graph, 'x_values')
        assert hasattr(graph, 'y_values')
        assert hasattr(graph, 'xtitle')
        assert hasattr(graph, 'ytitle')
        assert len(graph) == 2

    def test_1d_data_conversion(self, sample_data_1d):
        """Test that 1D y_values are converted to 2D."""
        x, y = sample_data_1d
        graph = TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="X",
            ytitle="Y"
        )
        assert graph.y_values.ndim == 2
        assert len(graph) == 1

    def test_legend_storage(self, sample_data_2d):
        """Test that legend and legend_loc are stored correctly."""
        x, y = sample_data_2d
        legend = ["Sine", "Cosine"]
        legend_loc = "upper right"
        graph = TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="Time",
            ytitle="Signal",
            legend=legend,
            legend_loc=legend_loc
        )
        assert graph.legend == legend
        assert graph.legend_loc == legend_loc

    def test_color_scheme_viridis(self, sample_data_2d):
        """Test viridis color scheme generates correct number of colors."""
        x, y = sample_data_2d
        graph = TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="Time",
            ytitle="Signal",
            color_scheme="viridis"
        )
        assert len(graph.colors) == 2

    def test_color_scheme_black(self, sample_data_2d):
        """Test black color scheme generates correct colors."""
        x, y = sample_data_2d
        graph = TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="Time",
            ytitle="Signal",
            color_scheme="black"
        )
        assert len(graph.colors) == 2
        assert all(color == '#000000' for color in graph.colors)

    def test_invalid_color_scheme_raises_error(self, sample_data_2d):
        """Test that invalid color scheme raises ValueError."""
        x, y = sample_data_2d
        with pytest.raises(ValueError) as exc_info:
            TraceGraph(
                x_values=x,
                y_values=y,
                xtitle="Time",
                ytitle="Signal",
                color_scheme="invalid_scheme"
            )
        assert 'not a valid color scheme' in str(exc_info.value)

    def test_mismatched_dimensions_raises_error(self):
        """Test that mismatched x and y dimensions raise ValueError."""
        x = np.linspace(0, 10, 100)
        y = np.linspace(0, 10, 50)
        with pytest.raises(ValueError) as exc_info:
            TraceGraph(
                x_values=x,
                y_values=y,
                xtitle="Time",
                ytitle="Signal"
            )
        assert 'does not match' in str(exc_info.value)

    def test_invalid_y_dimension_raises_error(self, sample_data_1d):
        """Test that y_values with > 2 dimensions raise ValueError."""
        x, _ = sample_data_1d
        y_3d = np.zeros((50, 2, 2))
        with pytest.raises(ValueError) as exc_info:
            TraceGraph(
                x_values=x,
                y_values=y_3d,
                xtitle="Time",
                ytitle="Signal"
            )
        assert 'invalid' in str(exc_info.value)


class TestBoundsSetting:
    """Tests for set_xbounds and set_ybounds methods."""

    @pytest.fixture
    def graph(self):
        """Create a TraceGraph for testing."""
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        return TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="Time",
            ytitle="Signal"
        )

    def test_set_xbounds(self, graph):
        """Test setting x-axis bounds."""
        bounds = (2, 8)
        graph.set_xbounds(bounds)
        assert graph.xbounds == bounds

    def test_set_ybounds(self, graph):
        """Test setting y-axis bounds."""
        bounds = (-1, 1)
        graph.set_ybounds(bounds)
        assert graph.ybounds == bounds

    def test_bounds_initially_none(self, graph):
        """Test that bounds are initially None."""
        assert graph.xbounds is None
        assert graph.ybounds is None
    

class TestLen:
    """Tests for __len__ method."""

    def test_len_with_multiple_traces(self):
        """Test __len__ with multiple traces."""
        x = np.linspace(0, 10, 100)
        y = np.column_stack([np.sin(x), np.cos(x), np.tan(x)])
        graph = TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="X",
            ytitle="Y"
        )
        assert len(graph) == 3

    def test_len_with_single_trace(self):
        """Test __len__ with single trace (1D input)."""
        x = np.linspace(0, 5, 50)
        y = x**2
        graph = TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="X",
            ytitle="Y"
        )
        assert len(graph) == 1


class TestGPCTraceGraph:
    """Tests for GPCTraceGraph subclass."""

    @pytest.fixture
    def gpc_data_file(self):
        """Get path to example GPC data file."""
        return os.path.join('examples', 'sample_gpc_data.txt')

    def test_gpc_trace_graph_initialization(self):
        """Test that GPCTraceGraph can be instantiated."""
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        from polychemtools.visualization.trace_graph import GPCTraceGraph

        graph = GPCTraceGraph(
            x_values=x,
            y_values=y,
            xtitle='Retention Time',
            ytitle='Intensity'
        )
        assert len(graph) == 1
        assert hasattr(graph, 'stylesheet')

    def test_rt_graph_from_data(self, gpc_data_file, tmp_path):
        """Test the rt_graph_from_data classmethod."""
        from polychemtools.visualization.trace_graph import GPCTraceGraph

        output_file = tmp_path / "test_gpc_rt_graph.png"
        GPCTraceGraph.rt_graph_from_data(
            instrument='tosoh',
            data_file=gpc_data_file,
            graph_file=str(output_file)
        )

        assert output_file.exists()

    def test_mw_graph_from_data(self, gpc_data_file, tmp_path):
        """Test the mw_graph_from_data classmethod."""
        from polychemtools.visualization.trace_graph import GPCTraceGraph
        from polychemtools.analysis.gpc_trace import PolymerSample

        calibration = 'examples/sample_calibrations.json:sample_calibration'

        output_file = tmp_path / "test_gpc_mw_graph.png"
        result = GPCTraceGraph.mw_graph_from_data(
            instrument='tosoh',
            data_file=gpc_data_file,
            calibration=calibration,
            graph_file=str(output_file)
        )

        assert output_file.exists()
        assert result is not None
        assert isinstance(result, PolymerSample)
        assert len(result) > 0  # Should have at least one polymer peak

    def test_mw_graph_without_calibration_raises_error(self, gpc_data_file, tmp_path):
        """Test that mw_graph_from_data raises error without valid calibration."""
        from polychemtools.visualization.trace_graph import GPCTraceGraph

        output_file = tmp_path / "test_gpc_mw_no_cal.png"

        # Passing None for calibration should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            GPCTraceGraph.mw_graph_from_data(
                instrument='tosoh',
                data_file=gpc_data_file,
                calibration=None,
                graph_file=str(output_file)
            )
        assert 'Calibration failed' in str(exc_info.value)

    def test_from_trace_single_trace(self, gpc_data_file, tmp_path):
        """Test creating graph from a single GPCTrace object."""
        from polychemtools.visualization.trace_graph import GPCTraceGraph
        from polychemtools.analysis.gpc_trace import GPCTrace

        calibration = 'examples/sample_calibrations.json:sample_calibration'

        # Create GPCTrace from file
        traces = GPCTrace.from_file(
            'tosoh', gpc_data_file, calibration, correction='span'
        )
        trace = traces[0]

        output_file = tmp_path / "test_from_trace_single.png"
        GPCTraceGraph.mw_graph_from_trace(
            traces=trace,
            graph_file=str(output_file)
        )

        assert output_file.exists()

    def test_from_trace_multiple_traces(self, gpc_data_file, tmp_path):
        """Test creating graph from multiple GPCTrace objects."""
        from polychemtools.visualization.trace_graph import GPCTraceGraph
        from polychemtools.analysis.gpc_trace import GPCTrace

        calibration = 'examples/sample_calibrations.json:sample_calibration'

        # Create GPCTrace from file
        traces = GPCTrace.from_file(
            'tosoh', gpc_data_file, calibration, correction='span'
        )

        output_file = tmp_path / "test_from_trace_multiple.png"
        GPCTraceGraph.mw_graph_from_trace(
            traces=traces,
            graph_file=str(output_file),
            legend=['Trace 1']
        )

        assert output_file.exists()

    def test_from_trace_with_bounds(self, gpc_data_file, tmp_path):
        """Test creating graph from GPCTrace with custom bounds."""
        from polychemtools.visualization.trace_graph import GPCTraceGraph
        from polychemtools.analysis.gpc_trace import GPCTrace

        calibration = 'examples/sample_calibrations.json:sample_calibration'

        # Create GPCTrace from file with bounds
        traces = GPCTrace.from_file(
            'tosoh', gpc_data_file, calibration,
            bounds=(1000, 100000), correction='span'
        )
        trace = traces[0]

        output_file = tmp_path / "test_from_trace_bounds.png"
        GPCTraceGraph.mw_graph_from_trace(
            traces=trace,
            graph_file=str(output_file),
            set_bounds=(1000, 100000)
        )

        assert output_file.exists()

    def test_from_trace_without_calibration_raises_error(self, gpc_data_file, tmp_path):
        """Test that from_trace raises error for traces without calibration."""
        from polychemtools.visualization.trace_graph import GPCTraceGraph
        from polychemtools.analysis.gpc_trace import GPCTrace, MissingCalibrationError

        # Create GPCTrace without calibration
        traces = GPCTrace.from_file(
            'tosoh', gpc_data_file, correction='span'
        )
        trace = traces[0]

        output_file = tmp_path / "test_from_trace_no_cal.png"
        with pytest.raises(MissingCalibrationError):
            GPCTraceGraph.mw_graph_from_trace(
                traces=trace,
                graph_file=str(output_file)
            )

    def test_rt_graph_from_trace_single(self, gpc_data_file, tmp_path):
        """Test creating retention time graph from a single GPCTrace object."""
        from polychemtools.visualization.trace_graph import GPCTraceGraph
        from polychemtools.analysis.gpc_trace import GPCTrace

        # Create GPCTrace from file (no calibration needed for RT graph)
        traces = GPCTrace.from_file(
            'tosoh', gpc_data_file, correction='span'
        )
        trace = traces[0]

        output_file = tmp_path / "test_rt_from_trace_single.png"
        GPCTraceGraph.rt_graph_from_trace(
            traces=trace,
            graph_file=str(output_file)
        )

        assert output_file.exists()

    def test_rt_graph_from_trace_multiple(self, gpc_data_file, tmp_path):
        """Test creating retention time graph from multiple GPCTrace objects."""
        from polychemtools.visualization.trace_graph import GPCTraceGraph
        from polychemtools.analysis.gpc_trace import GPCTrace

        # Create GPCTrace from file
        traces = GPCTrace.from_file(
            'tosoh', gpc_data_file, correction='span'
        )

        output_file = tmp_path / "test_rt_from_trace_multiple.png"
        GPCTraceGraph.rt_graph_from_trace(
            traces=traces,
            graph_file=str(output_file),
            legend=['Trace 1']
        )

        assert output_file.exists()

    def test_rt_graph_from_trace_with_bounds(self, gpc_data_file, tmp_path):
        """Test creating retention time graph from GPCTrace with custom bounds."""
        from polychemtools.visualization.trace_graph import GPCTraceGraph
        from polychemtools.analysis.gpc_trace import GPCTrace

        calibration = 'examples/sample_calibrations.json:sample_calibration'

        # Create GPCTrace from file with bounds (needs calibration for MW bounds)
        traces = GPCTrace.from_file(
            'tosoh', gpc_data_file, calibration,
            bounds=(1000, 100000), correction='span'
        )
        trace = traces[0]

        output_file = tmp_path / "test_rt_from_trace_bounds.png"
        GPCTraceGraph.rt_graph_from_trace(
            traces=trace,
            graph_file=str(output_file),
            set_bounds=(10, 20)
        )

        assert output_file.exists()

    def test_rt_graph_from_trace_with_calibration(self, gpc_data_file, tmp_path):
        """Test that rt_graph_from_trace works with calibrated traces too."""
        from polychemtools.visualization.trace_graph import GPCTraceGraph
        from polychemtools.analysis.gpc_trace import GPCTrace

        calibration = 'examples/sample_calibrations.json:sample_calibration'

        # Create GPCTrace with calibration (should still work for RT graph)
        traces = GPCTrace.from_file(
            'tosoh', gpc_data_file, calibration, correction='span'
        )
        trace = traces[0]

        output_file = tmp_path / "test_rt_from_trace_with_cal.png"
        GPCTraceGraph.rt_graph_from_trace(
            traces=trace,
            graph_file=str(output_file)
        )

        assert output_file.exists()


class TestXScale:
    """Tests for x-axis scale functionality."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        x = np.linspace(1, 100, 100)  # Start from 1 for log scale
        y = np.sin(np.log10(x))
        return x, y

    def test_default_linear_scale(self, sample_data):
        """Test that default x-axis scale is linear."""
        x, y = sample_data
        graph = TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="X",
            ytitle="Y"
        )
        assert graph.xscale == 'linear'

    def test_log_scale(self, sample_data):
        """Test that log scale can be set."""
        x, y = sample_data
        graph = TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="X",
            ytitle="Y",
            xscale='log'
        )
        assert graph.xscale == 'log'

    def test_invalid_scale_raises_error(self, sample_data):
        """Test that invalid scale raises ValueError."""
        x, y = sample_data
        with pytest.raises(ValueError) as exc_info:
            TraceGraph(
                x_values=x,
                y_values=y,
                xtitle="X",
                ytitle="Y",
                xscale='invalid'
            )
        assert "xscale must be 'linear' or 'log'" in str(exc_info.value)

    def test_log_scale_graph_saves(self, sample_data, tmp_path):
        """Test that graphs with log scale can be saved."""
        x, y = sample_data
        graph = TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="X (log)",
            ytitle="Y",
            xscale='log'
        )
        output_file = tmp_path / "test_log_scale.png"
        graph.save_graph(str(output_file))
        assert output_file.exists()

    def test_mw_graph_defaults_to_log_scale(self, tmp_path):
        """Test that MW graphs can be created and return polymer analysis."""
        from polychemtools.visualization.trace_graph import GPCTraceGraph
        from polychemtools.analysis.gpc_trace import PolymerSample

        calibration = 'examples/sample_calibrations.json:sample_calibration'

        gpc_data_file = os.path.join('examples', 'sample_gpc_data.txt')
        output_file = tmp_path / "test_mw_log.png"

        result = GPCTraceGraph.mw_graph_from_data(
            instrument='tosoh',
            data_file=gpc_data_file,
            calibration=calibration,
            graph_file=str(output_file)
        )

        assert output_file.exists()
        assert result is not None
        assert isinstance(result, PolymerSample)


class TestStylesheet:
    """Tests for stylesheet functionality."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        return x, y

    def test_default_stylesheet_path(self, sample_data):
        """Test that default stylesheet path is set correctly."""
        x, y = sample_data
        graph = TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="Time",
            ytitle="Signal"
        )
        assert graph.stylesheet is not None
        assert 'default.mplstyle' in graph.stylesheet
        assert os.path.exists(graph.stylesheet)

    def test_custom_stylesheet(self, sample_data):
        """Test that custom stylesheet can be provided."""
        x, y = sample_data
        custom_path = "/custom/path/to/style.mplstyle"
        graph = TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="Time",
            ytitle="Signal",
            stylesheet=custom_path
        )
        assert graph.stylesheet == custom_path

    def test_graph_with_stylesheet_saves(self, sample_data, tmp_path):
        """Test that graph with stylesheet can be saved."""
        x, y = sample_data
        graph = TraceGraph(
            x_values=x,
            y_values=y,
            xtitle="Time",
            ytitle="Signal"
        )
        output_file = tmp_path / "test_styled.png"
        graph.save_graph(str(output_file))
        assert output_file.exists()
