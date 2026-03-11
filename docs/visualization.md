# Visualization Module

The visualization module provides classes for creating publication-ready plots from experimental data. All graph classes inherit from `BaseGraph` and share common methods for setting bounds and saving figures.

## Common Methods

All graph classes support these methods:

```python
# Set axis bounds
graph.set_xbounds((min, max))
graph.set_ybounds((min, max))

# Save the figure
graph.save_graph('output.png')
```

## TraceGraph

Create multi-trace line plots for chromatograms and similar data.

```python
from polychemtools.visualization import TraceGraph
import numpy as np

# Single trace
graph = TraceGraph(
    x_values=retention_times,
    y_values=intensities,
    xtitle='Retention Time (min)',
    ytitle='Intensity (mV)'
)
graph.save_graph('chromatogram.png')

# Multiple traces
y_data = np.column_stack([trace1, trace2, trace3])
graph = TraceGraph(
    x_values=retention_times,
    y_values=y_data,
    xtitle='Retention Time (min)',
    ytitle='Intensity (mV)',
    legend=['Sample 1', 'Sample 2', 'Sample 3'],
    color_scheme='viridis'
)
graph.save_graph('comparison.png')
```

**Parameters:**
- `x_values` (np.ndarray): 1D array of x-axis values
- `y_values` (np.ndarray): 1D or 2D array of y-axis values (columns are traces)
- `xtitle` (str): X-axis label
- `ytitle` (str): Y-axis label
- `xscale` (str): Scale for x-axis: `'linear'` or `'log'` (default: `'linear'`)
- `legend` (list, optional): List of legend labels for each trace
- `legend_loc` (str): Legend location (default: `'upper left'`)
- `color_scheme` (str): Color scheme: `'viridis'` or `'black'` (default: `'black'`)
- `stylesheet` (str, optional): Path to matplotlib stylesheet file

**Color Schemes:**
- `'black'`: Monochrome (all traces in black)
- `'viridis'`: 8-color gradient from the viridis colormap

## GPCTraceGraph

GPC-specific plots with automatic normalization and molecular weight support.

### Quick Methods

These class methods handle the entire workflow from raw data to saved figure.

#### mw_graph_from_data

Create a molecular weight distribution plot from raw GPC data.

```python
from polychemtools.visualization import GPCTraceGraph

# Using JSON calibration (recommended)
sample = GPCTraceGraph.mw_graph_from_data(
    instrument='tosoh',
    data_file='polymer_sample.txt',
    calibration='calibrations.json:sample_calibration',
    graph_file='mw_plot.png',
    show_bounds=True  # Show integration regions
)
print(sample)  # Prints molecular weight statistics

# Using dict calibration
calibration = {
    'type': 'cubic',
    'params': [-0.001701334, 0.064349247, -1.197289570, 14.035147838]
}
sample = GPCTraceGraph.mw_graph_from_data(
    'tosoh',
    'polymer_sample.txt',
    calibration,
    'mw_plot.png'
)
```

**Parameters:**
- `instrument` (str): Instrument type (e.g., 'tosoh')
- `data_file` (str): Path to GPC data file
- `calibration` (dict or str): Calibration parameters or JSON reference
- `graph_file` (str): Output file path
- `legend` (list, optional): Legend labels
- `show_bounds` (bool): If True, show integration regions as shaded rectangles
- `set_bounds` (tuple, optional): Manual MW bounds (min, max)

**Returns:** `PolymerSample` with molecular weight statistics

#### rt_graph_from_data

Create a retention time plot from raw GPC data (no calibration needed).

```python
GPCTraceGraph.rt_graph_from_data(
    instrument='tosoh',
    data_file='polymer_sample.txt',
    graph_file='rt_plot.png',
    legend=['Sample 1'],
    set_bounds=(10, 25)
)
```

**Parameters:**
- `instrument` (str): Instrument type
- `data_file` (str): Path to GPC data file
- `graph_file` (str): Output file path
- `legend` (list, optional): Legend labels
- `set_bounds` (tuple, optional): Retention time bounds (min, max)

#### mw_graph_from_trace

Create a molecular weight plot from pre-processed GPCTrace objects.

```python
from polychemtools.analysis import GPCTrace

traces = GPCTrace.from_file('tosoh', 'data.txt', calibration)
GPCTraceGraph.mw_graph_from_trace(
    traces=traces,
    graph_file='output.png',
    legend=['Sample 1', 'Sample 2']
)
```

**Parameters:**
- `traces` (GPCTrace or tuple): One or more GPCTrace objects
- `graph_file` (str): Output file path
- `legend` (list, optional): Legend labels
- `set_bounds` (tuple, optional): MW bounds (min, max)

#### rt_graph_from_trace

Create a retention time plot from pre-processed GPCTrace objects.

```python
GPCTraceGraph.rt_graph_from_trace(
    traces=traces,
    graph_file='output.png'
)
```

### Manual Construction

For more control, create GPCTraceGraph directly:

```python
from polychemtools.analysis import GPCTrace
from polychemtools.visualization import GPCTraceGraph

traces = GPCTrace.from_file('tosoh', 'data.txt', calibration)
trace = traces[0]

graph = GPCTraceGraph(
    x_values=trace.molecular_weights,
    y_values=trace.get_normalized_intensities(),
    xtitle='Molecular Weight (g/mol)',
    ytitle='Intensity (A.U.)',
    xscale='log'
)
graph.set_xbounds((1000, 100000))
graph.set_ybounds((-0.1, 1.1))
graph.save_graph('mw_distribution.png')
```

## KineticsGraph

Create scatter plots for kinetics data.

```python
from polychemtools.visualization import KineticsGraph

time = [0, 10, 20, 30, 60, 120]
conversion = [0, 15, 32, 51, 78, 92]

graph = KineticsGraph(
    x_values=time,
    y_values=conversion,
    xtitle='Time (min)',
    ytitle='Conversion (%)'
)
graph.save_graph('kinetics.png')
```

**Parameters:**
- `x_values` (array-like): X-axis values
- `y_values` (array-like): Y-axis values
- `xtitle` (str): X-axis label
- `ytitle` (str): Y-axis label
- `color_scheme` (str): Color scheme (default: `'black'`)
- `stylesheet` (str, optional): Path to matplotlib stylesheet

## DSCTraceGraph

DSC-specific plots for thermal analysis data.

### Quick Methods

#### from_file

Create a plot of all heating/cooling ramps from a DSC file.

```python
from polychemtools.visualization import DSCTraceGraph

graph = DSCTraceGraph.from_file(
    instrument='trios',
    file_path='experiment.csv',
    graph_file='dsc_plot.png',
    color_scheme='viridis',
    xlim=(30, 90),
    ylim=(-0.5, 1.0)
)
```

**Parameters:**
- `instrument` (str): DSC instrument type (e.g., 'trios')
- `file_path` (str): Path to DSC data file
- `graph_file` (str): Output file path
- `color_scheme` (str): Color scheme (default: `'viridis'`)
- `xlim` (tuple, optional): X-axis limits (temp_min, temp_max)
- `ylim` (tuple, optional): Y-axis limits (flow_min, flow_max)

#### create_stacked_plot

Compare multiple samples by plotting specific ramps from each file.

```python
files = ['sample1.csv', 'sample2.csv', 'sample3.csv']

graph = DSCTraceGraph.create_stacked_plot(
    instrument='trios',
    file_paths=files,
    graph_file='comparison.png',
    ramp_index=-1,  # Second heating curve
    normalize=True,  # Normalize each trace to endpoint
    legend=['10% Loading', '20% Loading', '30% Loading'],
    color_scheme='viridis',
    xlim=(40, 80)
)
```

**Parameters:**
- `instrument` (str): DSC instrument type
- `file_paths` (list): List of file paths to compare
- `graph_file` (str): Output file path
- `ramp_index` (int): Which ramp to extract from each file (default: -1)
- `normalize` (bool): Normalize each trace to its endpoint (default: False)
- `legend` (list, optional): Legend labels
- `color_scheme` (str): Color scheme
- `xlim` (tuple, optional): X-axis limits
- `ylim` (tuple, optional): Y-axis limits

### Manual Construction

```python
from polychemtools.analysis import DSCTrace
from polychemtools.visualization import DSCTraceGraph
import numpy as np

trace = DSCTrace.from_file('trios', 'experiment.csv', ramp_index=-1, reverse=True)

# Plot raw and normalized data together
y_data = np.column_stack([trace.heat_flows, trace.normalize_to_baseline()])

graph = DSCTraceGraph(
    x_values=trace.temperatures,
    y_values=y_data,
    xtitle='Temperature (C)',
    ytitle='Heat Flow (W/g)',
    legend=['Raw', 'Normalized'],
    color_scheme='black'
)
graph.set_xbounds((30, 90))
graph.save_graph('custom_dsc.png')
```

## Styling

### Custom Stylesheets

All graph classes accept a `stylesheet` parameter for custom matplotlib styling:

```python
graph = TraceGraph(
    x_values, y_values,
    xtitle='X', ytitle='Y',
    stylesheet='/path/to/custom.mplstyle'
)
```

### Default Stylesheet

The default stylesheet is located at `polychemtools/visualization/default.mplstyle`. You can copy and modify this file to create custom styles.

## Usage in Emacs Org-Mode

The visualization module is designed for use in org-mode code blocks:

```org
#+begin_src python :session gpc :results file :file gpc_output.png
from polychemtools.visualization import GPCTraceGraph

sample = GPCTraceGraph.mw_graph_from_data(
    'tosoh',
    '../data/polymer_sample.txt',
    '../data/calibrations.json:sample_calibration',
    'gpc_output.png',
    show_bounds=True
)

print(sample)
'gpc_output.png'  # Return filename for org-mode display
#+end_src

#+RESULTS:
[[file:gpc_output.png]]
```
