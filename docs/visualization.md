# Visualization Module

The visualization module provides matplotlib-based classes for creating publication-quality plots of chromatography and calorimetry data.

## Module: `polychemtools.visualization`

---

## BaseGraph (Abstract)

```python
from polychemtools.visualization.base_graph import BaseGraph
```

Abstract base class for all graph types. Provides common functionality for creating, configuring, and saving matplotlib graphs.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `x_values` | `np.ndarray` | Independent variable data |
| `y_values` | `np.ndarray` | Dependent variable data |
| `xtitle` | `str` | X-axis label |
| `ytitle` | `str` | Y-axis label |
| `xbounds` | `tuple` or `None` | X-axis limits |
| `ybounds` | `tuple` or `None` | Y-axis limits |
| `stylesheet` | `str` | Path to matplotlib stylesheet |

### Color Schemes

| Scheme | Description |
|--------|-------------|
| `'viridis'` | Matplotlib viridis colormap |
| `'black'` | All traces in black |

### Methods

#### `set_xbounds`

```python
def set_xbounds(self, xbounds: Tuple[float, float]) -> None
```

Set x-axis limits.

**Parameters:**
- `xbounds` - (min, max) tuple

#### `set_ybounds`

```python
def set_ybounds(self, ybounds: Tuple[float, float]) -> None
```

Set y-axis limits.

**Parameters:**
- `ybounds` - (min, max) tuple

#### `save_graph`

```python
def save_graph(self, filename: str) -> None
```

Create and save the graph to a file.

**Parameters:**
- `filename` - Output file path (supports PNG, PDF, SVG, etc.)

---

## TraceGraph

```python
from polychemtools.visualization.trace_graph import TraceGraph
```

Line plot visualization for multi-trace experimental data.

### Attributes

Inherits all `BaseGraph` attributes, plus:

| Attribute | Type | Description |
|-----------|------|-------------|
| `xscale` | `str` | X-axis scale (`'linear'` or `'log'`) |
| `legend` | `list` or `None` | Legend labels for traces |
| `legend_loc` | `str` | Legend location |
| `colors` | `list` | Colors for each trace |

### Constructor

```python
TraceGraph(
    x_values: np.ndarray,
    y_values: np.ndarray,
    xtitle: str,
    ytitle: str,
    xscale: str = 'linear',
    legend: list | None = None,
    legend_loc: str = 'upper left',
    color_scheme: str = 'black',
    stylesheet: str | None = None
)
```

**Parameters:**
- `x_values` - 1D array of x-axis values
- `y_values` - 1D or 2D array of y-axis values (columns = traces)
- `xtitle` - X-axis label
- `ytitle` - Y-axis label
- `xscale` - Axis scale (`'linear'` or `'log'`)
- `legend` - List of legend labels
- `legend_loc` - Legend position
- `color_scheme` - Color scheme (`'viridis'` or `'black'`)
- `stylesheet` - Path to matplotlib stylesheet

**Example:**
```python
import numpy as np
from polychemtools.visualization.trace_graph import TraceGraph

x = np.linspace(0, 10, 100)
y = np.column_stack([np.sin(x), np.cos(x)])

graph = TraceGraph(
    x, y, 'Time (s)', 'Signal',
    legend=['sin(x)', 'cos(x)'],
    color_scheme='viridis'
)
graph.save_graph('traces.png')
```

---

## GPCTraceGraph

```python
from polychemtools.visualization.trace_graph import GPCTraceGraph
```

Specialized graph for GPC chromatograms with automatic bound calculation and peak visualization.

### Class Constants

| Constant | Default | Description |
|----------|---------|-------------|
| `BOUND_EDGE_SCALE` | 5 | Multiplier for extending bounds |
| `LOWER_BOUND_THRESHOLD` | 0.2 | Threshold for rounding min bound |
| `UPPER_BOUND_THRESHOLD` | 0.8 | Threshold for rounding max bound |
| `DEFAULT_Y_MIN` | -0.1 | Default y-axis minimum |
| `DEFAULT_Y_MAX` | 1.1 | Default y-axis maximum |

### Class Methods

#### `rt_graph_from_data`

```python
@classmethod
def rt_graph_from_data(
    cls,
    instrument: str,
    data_file: str,
    graph_file: str,
    legend: list | None = None,
    set_bounds: tuple | None = None
) -> None
```

Create retention time graph from raw GPC data.

**Parameters:**
- `instrument` - Instrument type (`'tosoh'`)
- `data_file` - Path to GPC data file
- `graph_file` - Output graph path
- `legend` - Optional legend labels
- `set_bounds` - Optional (min_RT, max_RT) bounds

**Example:**
```python
GPCTraceGraph.rt_graph_from_data(
    'tosoh', 'data.txt', 'rt_plot.png',
    legend=['Sample 1', 'Sample 2']
)
```

#### `mw_graph_from_data`

```python
@classmethod
def mw_graph_from_data(
    cls,
    instrument: str,
    data_file: str,
    calibration: dict | str,
    graph_file: str,
    legend: list | None = None,
    show_bounds: bool = False,
    set_bounds: tuple | None = None
) -> PolymerSample
```

Create molecular weight graph from raw GPC data.

**Parameters:**
- `instrument` - Instrument type (`'tosoh'`)
- `data_file` - Path to GPC data file
- `calibration` - Calibration dict or filepath string
- `graph_file` - Output graph path
- `legend` - Optional legend labels
- `show_bounds` - If True, show integration bounds on plot
- `set_bounds` - Optional (min_MW, max_MW) bounds

**Returns:** `PolymerSample` with analyzed peak data

**Example:**
```python
# With dict calibration
cal = {'type': 'cubic', 'params': [-0.0017, 0.064, -1.197, 14.035]}
sample = GPCTraceGraph.mw_graph_from_data(
    'tosoh', 'data.txt', cal, 'mw_plot.png',
    show_bounds=True
)
print(sample)

# With filepath calibration
sample = GPCTraceGraph.mw_graph_from_data(
    'tosoh', 'data.txt',
    'calibrations.json:sample_calibration',
    'mw_plot.png'
)
```

#### `mw_graph_from_trace`

```python
@classmethod
def mw_graph_from_trace(
    cls,
    traces: GPCTrace | Tuple[GPCTrace, ...],
    graph_file: str,
    legend: list | None = None,
    set_bounds: tuple | None = None
) -> None
```

Create molecular weight graph from pre-processed GPCTrace objects.

**Parameters:**
- `traces` - One or more GPCTrace objects (must have calibration)
- `graph_file` - Output graph path
- `legend` - Optional legend labels
- `set_bounds` - Optional (min_MW, max_MW) bounds

**Raises:**
- `MissingCalibrationError` - If any trace lacks calibration

**Example:**
```python
traces = GPCTrace.from_file('tosoh', 'data.txt', calibration)
GPCTraceGraph.mw_graph_from_trace(traces, 'mw_plot.png')
```

#### `rt_graph_from_trace`

```python
@classmethod
def rt_graph_from_trace(
    cls,
    traces: GPCTrace | Tuple[GPCTrace, ...],
    graph_file: str,
    legend: list | None = None,
    set_bounds: tuple | None = None
) -> None
```

Create retention time graph from GPCTrace objects.

**Parameters:**
- `traces` - One or more GPCTrace objects
- `graph_file` - Output graph path
- `legend` - Optional legend labels
- `set_bounds` - Optional (min_RT, max_RT) bounds

---

## KineticsGraph

```python
from polychemtools.visualization.kinetics_graph import KineticsGraph
```

Scatter plot visualization for kinetics data.

### Constructor

```python
KineticsGraph(
    x_values: np.ndarray,
    y_values: np.ndarray,
    xtitle: str,
    ytitle: str,
    stylesheet: str | None = None
)
```

**Parameters:**
- `x_values` - 1D array of x-axis values
- `y_values` - 1D array of y-axis values
- `xtitle` - X-axis label
- `ytitle` - Y-axis label
- `stylesheet` - Path to matplotlib stylesheet

**Example:**
```python
from polychemtools.visualization.kinetics_graph import KineticsGraph
import numpy as np

time = np.array([0, 30, 60, 120, 240, 480])
conversion = np.array([0, 15, 28, 45, 68, 85])

graph = KineticsGraph(
    time, conversion,
    'Time (min)', 'Conversion (%)'
)
graph.set_xbounds((0, 500))
graph.set_ybounds((0, 100))
graph.save_graph('kinetics.png')
```

---

## DSCTraceGraph

```python
from polychemtools.visualization.dsc_trace_graph import DSCTraceGraph
```

Specialized graph for DSC heating/cooling curves.

### Class Constants

| Constant | Default | Description |
|----------|---------|-------------|
| `DEFAULT_RAMP_LABELS` | `['First Heating', 'Cooling', 'Second Heating']` | Default legend labels |

### Constructor

```python
DSCTraceGraph(
    x_values: np.ndarray,
    y_values: np.ndarray,
    xtitle: str = 'Temperature (°C)',
    ytitle: str = 'Heat Flow (W/g)',
    legend: list | None = None,
    legend_loc: str = 'upper left',
    color_scheme: str = 'viridis',
    stylesheet: str | None = None
)
```

**Parameters:**
- `x_values` - 1D array of temperatures
- `y_values` - 2D array of heat flows (columns = ramps)
- `xtitle` - X-axis label (default: 'Temperature (°C)')
- `ytitle` - Y-axis label (default: 'Heat Flow (W/g)')
- `legend` - Legend labels (default: auto-generated)
- `legend_loc` - Legend position
- `color_scheme` - Color scheme
- `stylesheet` - Path to matplotlib stylesheet

### Class Methods

#### `from_file`

```python
@classmethod
def from_file(
    cls,
    instrument: str,
    file_path: str,
    graph_file: str,
    ramp_indices: list | None = None,
    legend: list | None = None,
    color_scheme: str = 'viridis',
    xlim: tuple | None = None,
    ylim: tuple | None = None
) -> DSCTraceGraph
```

Create and save a DSC plot from a data file.

**Parameters:**
- `instrument` - DSC instrument type (`'trios'`)
- `file_path` - Path to DSC data file
- `graph_file` - Output graph path
- `ramp_indices` - Indices of ramps to plot (default: all)
- `legend` - Legend labels
- `color_scheme` - Color scheme
- `xlim` - X-axis limits
- `ylim` - Y-axis limits

**Returns:** DSCTraceGraph object

**Example:**
```python
# Plot all ramps
graph = DSCTraceGraph.from_file('trios', 'dsc.csv', 'dsc_plot.png')

# Plot only second heating
graph = DSCTraceGraph.from_file(
    'trios', 'dsc.csv', 'dsc_plot.png',
    ramp_indices=[-1],
    legend=['Second Heating']
)
```

#### `create_stacked_plot`

```python
@classmethod
def create_stacked_plot(
    cls,
    instrument: str,
    file_paths: list,
    graph_file: str,
    ramp_index: int = -1,
    normalize: bool = True,
    legend: list | None = None,
    color_scheme: str = 'viridis',
    xlim: tuple | None = None,
    ylim: tuple | None = None
) -> DSCTraceGraph
```

Create a comparison plot of the same ramp from multiple experiments.

**Parameters:**
- `instrument` - DSC instrument type
- `file_paths` - List of data file paths
- `graph_file` - Output graph path
- `ramp_index` - Ramp to extract from each file (default: -1)
- `normalize` - If True, normalize to baseline (default: True)
- `legend` - Legend labels
- `color_scheme` - Color scheme
- `xlim` - X-axis limits
- `ylim` - Y-axis limits

**Returns:** DSCTraceGraph object

**Example:**
```python
files = ['sample1.csv', 'sample2.csv', 'sample3.csv']
graph = DSCTraceGraph.create_stacked_plot(
    'trios', files, 'comparison.png',
    ramp_index=-1,
    legend=['Sample 1', 'Sample 2', 'Sample 3'],
    xlim=(0, 200)
)
```

---

## Customization

### Custom Stylesheets

All graph classes accept a `stylesheet` parameter for custom matplotlib styling:

```python
graph = TraceGraph(x, y, 'X', 'Y', stylesheet='my_style.mplstyle')
```

### Default Stylesheet

The default stylesheet is located at:
```
polychemtools/visualization/default.mplstyle
```
