# Polychemtools API Documentation

Python library for processing, analyzing, and visualizing polymer chemistry laboratory data. Designed for use in Emacs org-mode code blocks for reproducible analysis workflows in electronic lab notebooks.

## Installation

```bash
# Install package (editable mode for development)
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

## Architecture

The library follows a three-layer architecture:

```
polychemtools/
├── processing/     # Data parsing from instrument files
├── analysis/       # Data analysis and calculations
├── visualization/  # Matplotlib-based plotting
└── utils/          # Utility functions and classes
```

## Quick Start

### GPC Analysis

```python
from polychemtools.analysis.gpc_trace import GPCTrace
from polychemtools.visualization.trace_graph import GPCTraceGraph

# Load GPC data with calibration
calibration = {'type': 'cubic', 'params': [-0.0017, 0.064, -1.197, 14.035]}
traces = GPCTrace.from_file('tosoh', 'data.txt', calibration)

# Analyze the polymer
trace = traces[0]
mn = trace.number_average_molecular_weight((1000, 100000))
mw = trace.weight_average_molecular_weight((1000, 100000))
dispersity = trace.dispersity((1000, 100000))

print(f"Mn: {mn:.0f} g/mol")
print(f"Mw: {mw:.0f} g/mol")
print(f"Dispersity: {dispersity:.2f}")

# Create a molecular weight plot
sample = GPCTraceGraph.mw_graph_from_data(
    'tosoh', 'data.txt', calibration, 'output.png'
)
```

### DSC Analysis

```python
from polychemtools.analysis.dsc_trace import DSCTrace
from polychemtools.visualization.dsc_trace_graph import DSCTraceGraph

# Load DSC data (second heating curve)
trace = DSCTrace.from_file('trios', 'experiment.csv', ramp_index=-1, reverse=True)

# Measure baseline slope
slope = trace.measure_slope((55, 60))
print(f"Heat capacity slope: {slope:.4f} W/g/°C")

# Create a DSC plot
graph = DSCTraceGraph.from_file('trios', 'experiment.csv', 'dsc_output.png')
```

### GC Analysis

```python
from polychemtools.processing.gc_data_processor import GCData

# Load GC data
gc = GCData('shimadzu', 'gc_data.txt')

# Get peak areas at specific retention times
areas = gc.get_peak_areas([5.2, 8.7, 12.3], tolerance=0.1)
print(f"Peak areas: {areas}")

# Get chromatogram data
times, intensities = gc.get_chromatogram(time_range=(5.0, 15.0))
```

### Using Calibration Files

```python
from polychemtools.utils.calibration_loader import resolve_calibration

# Load calibration from JSON file
calibration = resolve_calibration('calibrations.json:sample_calibration')

# Or use dict directly
calibration = {'type': 'cubic', 'params': [-0.0017, 0.064, -1.197, 14.035]}
```

## Module Documentation

- [Processing Module](processing.md) - Data parsers for GPC, GC, and DSC instruments
- [Analysis Module](analysis.md) - Data analysis classes for GPC and DSC traces
- [Visualization Module](visualization.md) - Matplotlib-based plotting classes
- [Utilities Module](utils.md) - Calibration loader and helper classes

## Supported Instruments

| Technique | Instrument | Data Format |
|-----------|------------|-------------|
| GPC | Tosoh | Text file (whitespace-delimited) |
| GC | Shimadzu | Text file (tab-delimited) |
| DSC | Trios | CSV file |

## Dependencies

- pandas (>=2.0.0)
- numpy
- scipy
- matplotlib
