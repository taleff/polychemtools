# Polychemtools

Python tools for processing, analyzing, and visualizing polymer synthesis data.

## Overview

This package provides data analysis tools with a focus on those useful for polymer chemistry. These tools were designed for use in org-mode code blocks, enabling reproducible analysis workflows within an electronic lab notebook. However, they may be used in other contexts as well.

## Installation

### 1. Clone the Repository

```bash
cd /path/to/your/projects
git clone <repository-url> polychemtools
```

### 2. Set Up Python Virtual Environment (Recommended)

Using a virtual environment keeps dependencies isolated from your system Python:

```bash
cd polychemtools
python3 -m venv venv
source venv/bin/activate
```

### 3. Install the Package

```bash
# Install in editable mode (recommended for development)
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

**Dependencies:**
- `pandas >= 2.0.0`: Data processing and table parsing
- `numpy`: Numerical computations and array operations
- `scipy`: Peak detection and signal processing
- `matplotlib`: Plotting and visualization
- `pytest >= 7.0.0`: Testing framework (development)

If you are using a virtual environment as recommended above, you can add this module to the path of the virtual environment by adding a .pth file to the /lib/pythonx.xx/site-packages folder in your virutal environment. The contents of the .pth file should be a single line with the location of the module directory with no trailing spaces or lines.

## Quick Start

```python
from polychemtools.visualization import GPCTraceGraph

# Generate a molecular weight distribution plot with automatic peak analysis
sample = GPCTraceGraph.mw_graph_from_data(
    'tosoh',                          # Instrument type
    'data/polymer_sample.txt',        # Data file
    'calibrations.json:my_calibration', # Calibration reference
    'output.png',                     # Output file
    show_bounds=True                  # Show integration regions
)

print(sample)
# PolymerSample(1 polymer):
#   Peak 1: Mn: 15234 g/mol; Mw: 23451 g/mol; D: 1.54
```

## Usage

Instrumental data should be stored as a .txt or .csv file. These files can generally be exported in this format from the instruments they are generated on. The list of supported data formats is below.

**Currently Supported Instruments:**
- Gas Chromatography (GC): Shimadzu
- Gel Permeation Chromatography (GPC): Tosoh
- Differential Scanning Calorimetry (DSC): TA

The library is organized into three parts: processing, analysis, and visualization. The processing methods merely extract the raw data from the imported data files. The analysis library provides basic analysis functionality (like molecular weight calculations for GPC data). The visualization library provides some shortcut/convenience methods for quickly plotting data.

There is no need to call each part of the library sequentially, each subsequent part is downstream of the last. For example, when generating a GPC graph using the visualization tools, it creates an analysis object which itself creates a processing object.

For more information on the usage of each section, please see the following documentation:

- [Processing](docs/processing.md)
- [Analysis](docs/analysis.md)
- [Visualization](docs/visualization.md)

## License

Licensed under GNU GPLv3: https://www.gnu.org/licenses/gpl-3.0.html

