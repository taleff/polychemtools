# Lab Notebook Tools

Python tools for processing, analyzing, and visualizing laboratory polymer chemistry data.

## Overview

This package provides data analysis tools with a focus on those useful for polymer chemistry. These tools were designed for use in org-mode code blocks, enabling reproducible analysis workflows within an electronic lab notebook. However, they may be used in other contexts as well.

**Currently Supported Instruments:**
- Gas Chromatography (GC): Shimadzu
- Gel Permeation Chromatography (GPC): Tosoh
- Differential Scanning Calorimetry (DSC): Generic CSV format

## Features

- **Data Processing**: 
  - Parse and extract data from GC and GPC instrument files
- **GC Analysis**: 
  - Extract peak areas and chromatograms with automatic peak detection
- **GPC Analysis**:
  - Molecular weight calibration (linear and cubic polynomial)
  - Calculate number-average (Mn) and weight-average (Mw) molecular weights
  - Automatic peak detection and integration
  - Multi-peak analysis for polymer samples
- **Visualization**:
  - Multi-trace line plots (chromatograms, GPC traces)
  - Kinetics scatter plots
  - Customizable color schemes and styling
  - Automatic normalization and bound calculation
  - Integration region visualization

## Installation

### 1. Clone the Repository

```bash
cd /path/to/your/projects
git clone <repository-url> lab-notebook-tools
```

### 2. Set Up Python Virtual Environment (Recommended)

Using a virtual environment keeps dependencies isolated from your system Python:

```bash
cd lab-notebook-tools
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `pandas >= 2.0.0`: Data processing and table parsing
- `numpy`: Numerical computations and array operations
- `scipy`: Peak detection and signal processing
- `matplotlib`: Plotting and visualization
- `pytest >= 7.0.0`: Testing framework (development)

### 4. Add to Python Path (Optional)

To use the package from anywhere without manual path manipulation, add it to your `~/.bashrc` or `~/.bash_profile`:

```bash
export PYTHONPATH="/path/to/your/projects/lab-notebook-tools:$PYTHONPATH"
```

Then reload your shell configuration:
```bash
source ~/.bashrc
```

If you are using a virtual environment as recommended above, you can add this module to your path by adding a .pth file (can be named anything) to the /lib/pythonx.xx/site-packages folder in your virutal environment. The contents of the .pth file should be a single line with the location of the module directory with no trailing spaces or lines.

## Quick Start

### GC: Extract Peak Areas

```python
from tools.processing import GCDataProcessor

# Load GC data
gc = GCDataProcessor('shimadzu', 'path/to/gc_data.TXT')

# Extract peak areas at specific retention times
retention_times = [3.521, 4.234, 5.891]
areas = gc.get_peak_areas(retention_times, tolerance=0.05)

print(areas)  # [area1, area2, area3]
```

### GPC: Analyze Molecular Weight Distribution

```python
from tools.analysis import GPCTrace

# Method 1: Using JSON calibration file (recommended)
traces = GPCTrace.from_file(
    'tosoh',
    'path/to/gpc_data.txt',
    'calibrations.json:sample_calibration'
)

# Method 2: Using dictionary (backward compatible)
calibration = {
    'type': 'cubic',
    'params': [-0.001701334, 0.064349247, -1.197289570, 14.035147838]
}
traces = GPCTrace.from_file('tosoh', 'path/to/gpc_data.txt', calibration)

# Analyze peaks in first trace
sample = traces[0].analyze_peaks()
print(sample)
# Output:
# Polymer(Mn=15234.5, Mw=23451.2, Đ=1.54)
# Polymer(Mn=45123.1, Mw=67890.3, Đ=1.50)
```

### GPC: Create Molecular Weight Distribution Plot

```python
from tools.visualization import GPCTraceGraph

# Method 1: Using JSON calibration file (recommended)
sample = GPCTraceGraph.mw_graph_from_data(
    'tosoh',
    'path/to/gpc_data.txt',
    '../data/calibrations.json:sample_calibration',
    'output_plot.png',
    show_bounds=True  # Visualize integration regions
)

# Method 2: Using dictionary (backward compatible)
calibration = {
    'type': 'cubic',
    'params': [-0.001701334, 0.064349247, -1.197289570, 14.035147838]
}
sample = GPCTraceGraph.mw_graph_from_data(
    'tosoh',
    'path/to/gpc_data.txt',
    calibration,
    'output_plot.png',
    show_bounds=True
)

print(sample)  # Prints molecular weight statistics
```

### DSC: Analyze Thermal Transitions

```python
from tools.visualization import DSCTraceGraph
from tools.analysis import DSCTrace

# Quick plot of all heating/cooling ramps
DSCTraceGraph.from_file('trios', 'experiment.csv', 'dsc_plot.png')

# Measure baseline slope in second heating curve
trace = DSCTrace.from_file('trios', 'experiment.csv', ramp_index=-1, reverse=True)
slope = trace.measure_slope((55, 60))  # Temperature range in °C
print(f'Baseline slope: {slope:.4f} W/g/°C')

# Compare multiple samples
files = ['sample1.csv', 'sample2.csv', 'sample3.csv']
DSCTraceGraph.create_stacked_plot(
    'trios',
    files,
    'comparison.png',
    legend=['10%', '20%', '30%'],
    normalize=True
)
```

## Detailed Usage

### Gas Chromatography (GC)

#### Initialize GC Data Processor

```python
from tools.processing import GCDataProcessor

gc = GCDataProcessor('shimadzu', 'path/to/gc_data.TXT')
```

**Supported instruments:** `'shimadzu'`

#### Extract Peak Areas

Extract areas for peaks at specific retention times:

```python
# Single peak
areas = gc.get_peak_areas([3.521], tolerance=0.05)

# Multiple peaks
retention_times = [3.521, 4.234, 5.891]
areas = gc.get_peak_areas(retention_times, tolerance=0.05)
```

**Parameters:**
- `retention_times`: List of retention times (minutes)
- `tolerance`: Search window around each retention time (default: 0.05 minutes)

**Returns:** List of peak areas in the same order as input retention times

**Raises:**
- `MultiplePeaksFoundError`: If multiple peaks found within tolerance window
- `ValueError`: If no peak found at specified retention time

#### Get Full Chromatogram

```python
# Get complete chromatogram
rt, intensity = gc.get_chromatogram()

# Get chromatogram in specific time range
rt, intensity = gc.get_chromatogram(min_time=2.0, max_time=8.0)
```

**Parameters:**
- `min_time`: Minimum retention time (optional)
- `max_time`: Maximum retention time (optional)

**Returns:** Tuple of (retention_times, intensities) as numpy arrays

### Gel Permeation Chromatography (GPC)

#### Managing Calibrations

GPC molecular weight calibrations can be stored and loaded in two ways:

##### Method 1: Direct Dictionary (Backward Compatible)

```python
calibration = {
    'type': 'cubic',
    'params': [-0.001701334, 0.064349247, -1.197289570, 14.035147838]
}
```

##### Method 2: JSON File with Named Calibrations (Recommended)

**Step 1: Create a JSON file** (`calibrations.json`):

```json
{
  "sample_calibration": {
    "type": "cubic",
    "params": [-0.001701334, 0.064349247, -1.197289570, 14.035147838]
  },
  "calibration_2024_01": {
    "type": "linear",
    "params": [1.5, 2.3]
  },
  "old_calibration_2023": {
    "type": "cubic",
    "params": [-0.0015, 0.055, -1.05, 13.5]
  }
}
```

**Step 2: Load calibration by name**:

```python
# Use filepath:calibration_name format
sample = GPCTraceGraph.mw_graph_from_data(
    'tosoh',
    'data.txt',
    'calibrations.json:sample_calibration',  # <- filepath:name
    'output.png'
)
```

**Benefits of JSON method:**
- Store all calibrations in one file
- No need for `sys.path` manipulation
- Easy to maintain and version control
- Preserve historical calibrations for data reproducibility

##### Migrating Existing Python Calibrations

If you have existing calibrations in Python format, use the migration script:

```bash
python migrate_calibrations.py old_calibrations.py calibrations.json
```

This will automatically convert all calibrations from the Python file to JSON format.

#### Load GPC Data

```python
from tools.processing import GPCDataProcessor

# Initialize processor
gpc = GPCDataProcessor('tosoh', 'path/to/gpc_data.txt')

# Extract data
retention_times, intensities = gpc.get_data()
```

**Supported instruments:** `'tosoh'`

**Returns:**
- `retention_times`: 1D numpy array of retention times
- `intensities`: 2D numpy array (each row is a trace)

#### Molecular Weight Analysis

##### Create GPCTrace with Calibration

```python
from tools.analysis import GPCTrace

# Define calibration
# For cubic: MW = 10^(a*RT^3 + b*RT^2 + c*RT + d)
calibration = {
    'type': 'cubic',
    'params': [-0.001701334, 0.064349247, -1.197289570, 14.035147838]
}

# For linear: MW = 10^(a*RT + b)
calibration_linear = {
    'type': 'linear',
    'params': [-0.5, 6.5]
}

# Create trace manually
rt, intensities = gpc.get_data()
trace = GPCTrace(rt, intensities[0], calibration)

# Or use shortcut (recommended)
traces = GPCTrace.from_file('tosoh', 'path/to/gpc_data.txt', calibration)
trace = traces[0]
```

##### Calculate Molecular Weight Statistics

```python
# Define integration bounds (molecular weight range)
bounds = (1000, 50000)  # g/mol

# Calculate statistics
mn = trace.number_average_molecular_weight(bounds)
mw = trace.weight_average_molecular_weight(bounds)
dispersity = trace.dispersity(bounds)

print(f"Mn: {mn:.1f} g/mol")
print(f"Mw: {mw:.1f} g/mol")
print(f"Đ: {dispersity:.2f}")
```

**Available methods:**
- `number_average_molecular_weight(bounds)`: Calculate Mn
- `weight_average_molecular_weight(bounds)`: Calculate Mw
- `dispersity(bounds)`: Calculate Đ = Mw/Mn
- `peak_area(bounds)`: Integrate signal over MW range
- `moment(n, bounds)`: Calculate nth moment of distribution

##### Automatic Peak Detection and Analysis

```python
# Detect all peaks and calculate statistics for each
sample = trace.analyze_peaks()

# Print results
print(sample)
# Output:
# Polymer(Mn=15234.5, Mw=23451.2, Đ=1.54)
# Polymer(Mn=45123.1, Mw=67890.3, Đ=1.50)

# Access individual peaks
for i, polymer in enumerate(sample.polymers):
    print(f"Peak {i+1}: Mn={polymer.mn:.1f}, Mw={polymer.mw:.1f}, Đ={polymer.dispersity:.2f}")
```

**Peak detection parameters** (automatically configured):
- Minimum molecular weight: 200 g/mol (filters noise)
- Prominence threshold: 0.5 (relative to max peak)
- Baseline threshold: 0.993 (relative height)

##### Manual Peak Finding

```python
# Get peak positions and properties
peaks = trace.peak_finder()
# Returns dictionary with 'peaks', 'peak_heights', 'left_bases', 'right_bases'
```

### Differential Scanning Calorimetry (DSC)

#### Load DSC Data

```python
from tools.processing import DSCDataProcessor

# Initialize processor
dsc = DSCDataProcessor('trios', 'path/to/experiment.csv')

# Get information about the data
print(f'Number of ramps: {len(dsc)}')
print(f'Total data points: {len(dsc.temperatures)}')
```

**Supported file format:** CSV files with temperature (°C) and heat flow (W/g) data

**Returns:**
- `temperatures`: 1D numpy array of temperature values
- `heat_flows`: 1D numpy array of heat flow values
- `ramp_indices`: Array indicating where heating/cooling ramps begin

#### Extract Individual Ramps

DSC experiments typically contain multiple ramps (e.g., first heating, cooling, second heating):

```python
# Get second heating curve (last ramp, reversed for ascending temperature)
temps, flows = dsc.get_ramp_data(ramp_index=-1, reverse=True)

# Get first heating curve
temps, flows = dsc.get_ramp_data(ramp_index=0, reverse=False)

# Get cooling curve (second ramp)
temps, flows = dsc.get_ramp_data(ramp_index=1)
```

**Parameters:**
- `ramp_index`: Index of ramp to extract (0-based, negative indices count from end)
- `reverse`: If True, reverse the arrays (useful for analysis)

#### Thermal Analysis

##### Create DSCTrace for Analysis

```python
from tools.analysis import DSCTrace

# From file (shortcut method)
trace = DSCTrace.from_file(
    'trios',
    'path/to/experiment.csv',
    ramp_index=-1,  # Last ramp (second heating)
    reverse=True     # Reverse for ascending temperature
)

# Or create manually from arrays
trace = DSCTrace(temperatures, heat_flows)
```

##### Measure Baseline Slope

```python
# Measure slope in a temperature range (e.g., for heat capacity)
slope = trace.measure_slope((55, 60))  # Temperature range in °C
print(f'Baseline slope: {slope:.4f} W/g/°C')

# Get full fit data for plotting
slope, intercept, fit_temps, fit_flows = trace.measure_slope(
    (55, 60),
    return_fit_data=True
)
```

##### Normalize Data

```python
# Normalize to endpoint (common DSC normalization)
normalized_flows = trace.normalize_to_baseline()

# Normalize to specific value
normalized_flows = trace.normalize_to_baseline(baseline_value=0.5)
```

#### Visualization

##### Quick Plot of All Ramps

```python
from tools.visualization import DSCTraceGraph

# Create plot with all heating/cooling curves
graph = DSCTraceGraph.from_file(
    'trios',
    'path/to/experiment.csv',
    'output.png',
    color_scheme='viridis',  # Uses default labels
    xlim=(30, 90),
    ylim=(-0.5, 1.0)
)
```

##### Compare Multiple Samples (Stacked Plot)

```python
# Compare second heating curves from multiple experiments
files = ['sample1.csv', 'sample2.csv', 'sample3.csv']

graph = DSCTraceGraph.create_stacked_plot(
    'trios',
    files,
    'comparison.png',
    ramp_index=-1,  # Second heating curve
    normalize=True,  # Normalize each trace to endpoint
    legend=['10% Loading', '20% Loading', '30% Loading'],
    color_scheme='viridis',
    xlim=(40, 80)
)
```

##### Manual Plot Creation

```python
import numpy as np

# Load and analyze data
trace = DSCTrace.from_file('trios', 'experiment.csv', ramp_index=-1, reverse=True)

# Create custom plot with raw and normalized data
graph = DSCTraceGraph(
    trace.temperatures,
    np.column_stack([trace.heat_flows, trace.normalize_to_baseline()]),
    legend=['Raw Heat Flow', 'Normalized'],
    color_scheme='black'
)

graph.set_xbounds((30, 90))
graph.save_graph('custom_dsc.png')
```

### Visualization

#### Create Multi-Trace Plots

```python
from tools.visualization import TraceGraph

# Load data
gpc = GPCDataProcessor('tosoh', 'path/to/gpc_data.txt')
rt, intensities = gpc.get_data()

# Create graph with multiple traces
graph = TraceGraph(
    rt,
    intensities,
    'output.png',
    x_label='Retention Time (min)',
    y_label='Intensity (mV)',
    color_scheme='viridis'  # or 'black' for monochrome
)

# Optional: Set axis bounds
graph.set_xbounds(10, 20)
graph.set_ybounds(0, 100)

# Save the plot
graph.save_graph()
```

**TraceGraph features:**
- Supports 1D or 2D intensity arrays (multiple traces)
- Color schemes: `'viridis'` (8-color gradient) or `'black'` (monochrome)
- Optional legend with configurable position
- Linear or logarithmic x-axis scaling
- Custom post-processing via callback functions

#### Create GPC Molecular Weight Distribution Plots

##### Using the Shortcut Method (Recommended)

```python
from tools.visualization import GPCTraceGraph

calibration = {
    'type': 'cubic',
    'params': [-0.001701334, 0.064349247, -1.197289570, 14.035147838]
}

# Create plot and get analysis results in one step
sample = GPCTraceGraph.mw_graph_from_data(
    'tosoh',
    'path/to/gpc_data.txt',
    calibration,
    'mw_distribution.png',
    show_bounds=True,  # Show integration regions as shaded rectangles
    color_scheme='viridis'
)

# Sample contains molecular weight statistics for all detected peaks
print(sample)
```

##### Using Manual Construction

```python
from tools.analysis import GPCTrace
from tools.visualization import GPCTraceGraph

# Load and calibrate data
traces = GPCTrace.from_file('tosoh', 'path/to/gpc_data.txt', calibration)

# Extract molecular weights and intensities
mw = traces[0].molecular_weights
intensities = traces[0].intensities

# Create graph
graph = GPCTraceGraph(
    mw,
    intensities,
    'mw_distribution.png',
    x_label='Molecular Weight (g/mol)',
    y_label='Normalized Intensity'
)

# GPC graphs automatically:
# - Use logarithmic x-axis
# - Normalize intensities to peak height
# - Calculate appropriate bounds

graph.save_graph()
```

##### Retention Time Plots

```python
# Create retention time plot (without MW calibration)
graph = GPCTraceGraph.rt_graph_from_data(
    'tosoh',
    'path/to/gpc_data.txt',
    'rt_plot.png'
)
```

#### Create Kinetics Plots

```python
from tools.visualization import KineticsGraph

# Your kinetics data
time = [0, 10, 20, 30, 60, 120]  # minutes
conversion = [0, 15, 32, 51, 78, 92]  # percent

graph = KineticsGraph(
    time,
    conversion,
    'kinetics.png',
    x_label='Time (min)',
    y_label='Conversion (%)'
)

graph.save_graph()
```

## API Reference

### Processing Module (`tools.processing`)

#### `GCDataProcessor`
Parse and extract data from GC instrument files.

**Methods:**
- `__init__(instrument_type, file_path)`: Initialize with instrument type and data file
- `get_peak_areas(retention_times, tolerance=0.05)`: Extract peak areas at specified retention times
- `get_chromatogram(min_time=None, max_time=None)`: Get full chromatogram data

**Exceptions:**
- `MultiplePeaksFoundError`: Multiple peaks found within tolerance window
- `UnsupportedInstrumentError`: Unsupported instrument type specified

#### `GPCDataProcessor`
Parse GPC data from instrument files.

**Methods:**
- `__init__(instrument_type, file_path)`: Initialize with instrument type and data file
- `get_data()`: Returns (retention_times, intensities) tuple
- `__len__()`: Returns number of traces in file

### Analysis Module (`tools.analysis`)

#### `GPCTrace`
Analyze GPC traces with molecular weight calibration.

**Class Methods:**
- `from_file(instrument_type, file_path, calibration)`: Load traces directly from file (returns tuple)
  - `calibration` can be:
    - `dict`: Direct calibration with 'type' and 'params' keys
    - `str`: Path string in format 'filepath:calibration_name'
    - `None`: No calibration applied

**Instance Methods:**
- `number_average_molecular_weight(bounds)`: Calculate Mn over specified MW range
- `weight_average_molecular_weight(bounds)`: Calculate Mw over specified MW range
- `dispersity(bounds)`: Calculate Đ = Mw/Mn
- `peak_area(bounds)`: Integrate signal over MW range
- `moment(n, bounds)`: Calculate nth statistical moment
- `peak_finder()`: Detect peaks automatically
- `analyze_peaks()`: Detect peaks and return PolymerSample with statistics for each

**Attributes:**
- `retention_times`: 1D numpy array
- `intensities`: 1D numpy array
- `molecular_weights`: 1D numpy array (if calibrated)

**Exceptions:**
- `MissingCalibrationError`: MW operation attempted without calibration
- `NoPeakError`: Peak analysis attempted but no peaks detected

#### `Polymer`
Data class storing molecular weight statistics for a single peak.

**Attributes:**
- `mn`: Number-average molecular weight
- `mw`: Weight-average molecular weight
- `dispersity`: Đ = Mw/Mn

#### `PolymerSample`
Container for multiple Polymer objects (multi-peak samples).

**Attributes:**
- `polymers`: List of Polymer objects

### Utilities Module (`tools.utils`)

#### `load_calibration(filepath, calibration_name)`
Load a calibration by name from a JSON file.

**Parameters:**
- `filepath`: Path to JSON file containing calibrations
- `calibration_name`: Name of the calibration to load

**Returns:** Dictionary with 'type' and 'params' keys

**Raises:**
- `CalibrationFileError`: File not found or invalid JSON
- `CalibrationNotFoundError`: Calibration name not found
- `InvalidCalibrationError`: Calibration structure is invalid

**Example:**
```python
from tools.utils import load_calibration

cal = load_calibration('calibrations.json', 'sample_calibration')
```

#### `resolve_calibration(calibration)`
Resolve a calibration from either dict or filepath string.

**Parameters:**
- `calibration`: Either a dict or a string in format 'filepath:calibration_name'

**Returns:** Dictionary with 'type' and 'params' keys

This function provides backward compatibility by accepting both formats.

### Visualization Module (`tools.visualization`)

#### `TraceGraph`
Create multi-trace line plots.

**Methods:**
- `__init__(x_values, y_values, file_path, x_label, y_label, color_scheme='viridis', ...)`: Initialize graph
- `set_xbounds(lower, upper)`: Set x-axis limits
- `set_ybounds(lower, upper)`: Set y-axis limits
- `save_graph()`: Create and save the plot
- `__len__()`: Returns number of traces

**Parameters:**
- `color_scheme`: `'viridis'` (8-color gradient) or `'black'` (monochrome)
- `x_scale`: `'linear'` or `'log'`
- `show_legend`: Boolean, show legend (default: True if >1 trace)

#### `GPCTraceGraph`
GPC-specific trace plots with automatic normalization and MW support.

**Class Methods:**
- `mw_graph_from_data(instrument_type, file_path, calibration, output_path, show_bounds=False, ...)`: Create MW distribution plot with automatic analysis
  - `calibration` can be:
    - `dict`: Direct calibration with 'type' and 'params' keys
    - `str`: Path string in format 'filepath:calibration_name'
- `rt_graph_from_data(instrument_type, file_path, output_path, ...)`: Create retention time plot

**Features:**
- Automatic intensity normalization to peak height
- Logarithmic x-axis for MW plots
- Optional integration region visualization (`show_bounds=True`)
- Returns PolymerSample with analysis results

#### `KineticsGraph`
Create scatter plots for kinetics data.

**Methods:**
- `__init__(x_values, y_values, file_path, x_label, y_label, ...)`: Initialize graph
- `set_xbounds(lower, upper)`: Set x-axis limits
- `set_ybounds(lower, upper)`: Set y-axis limits
- `save_graph()`: Create and save the plot

## Usage in Emacs Org-Mode

### Example: GC Analysis in Org-Mode

```org
#+begin_src python :session gc-analysis :results output
from tools.processing import GCDataProcessor

gc = GCDataProcessor('shimadzu', 'data/experiment_001.TXT')
areas = gc.get_peak_areas([3.521, 4.234, 5.891], tolerance=0.05)

print(f"Peak areas: {areas}")
print(f"Conversion: {(areas[1] / sum(areas)) * 100:.1f}%")
#+end_src

#+RESULTS:
: Peak areas: [1234.5, 5678.9, 890.2]
: Conversion: 72.8%
```

### Example: GPC Plot in Org-Mode

```org
#+begin_src python :session gpc :results file :file gpc_output.png
from tools.visualization import GPCTraceGraph

# Load calibration from JSON file (no sys.path manipulation needed!)
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

## Examples

The `examples/` directory contains sample data files and usage demonstrations:

- `sample_gc_data.TXT`: Example Shimadzu GC data file
- `sample_gpc_data.txt`: Example Tosoh GPC data file (18,001 data points)
- `sample_calibration.py`: Example cubic calibration coefficients (legacy Python format)
- `sample_calibrations.json`: Example calibrations in JSON format (recommended)
- `*.png`: Example output plots

To convert your own Python calibration files to JSON:
```bash
python migrate_calibrations.py examples/sample_calibration.py examples/calibrations.json
```

## Running Tests

Tests use pytest and provide 85+ test cases covering all modules:

```bash
cd /path/to/lab-notebook-tools
pytest tests/ -v
```

Test a specific module:
```bash
pytest tests/test_gc_data.py -v     # GC processing tests
pytest tests/test_gpc_data.py -v    # GPC processing tests
pytest tests/test_trace_graph.py -v # Visualization tests
```

Run tests with coverage report:
```bash
pytest tests/ -v --cov=tools --cov-report=html
```

## License

[Add your license information here]

## Citation

If you use this package in your research, please cite:

[Add citation information here]
