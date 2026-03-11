# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python library for processing, analyzing, and visualizing polymer chemistry laboratory data. Designed for use in Emacs org-mode code blocks for reproducible analysis workflows in electronic lab notebooks.

## Commands

```bash
# Install package (editable mode for development)
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_gc_data.py -v
pytest tests/test_gpc_data.py -v
pytest tests/test_trace_graph.py -v
pytest tests/test_calibration_loader.py -v

# Run single test
pytest tests/test_gc_data.py::TestGetPeakAreas::test_single_peak_exact_match -v

# Run tests with coverage
pytest tests/ -v --cov=tools --cov-report=html
```

## Architecture

### Three-Layer Structure

The codebase follows a three-layer architecture under `tools/`:

1. **processing/** - Data parsing from instrument files
   - `GCDataProcessor` (Shimadzu GC files)
   - `GPCDataProcessor` (Tosoh GPC files)
   - `DSCDataProcessor` (Trios CSV files)

2. **analysis/** - Data analysis and calculations
   - `GPCTrace` - Molecular weight calculations with calibration
   - `DSCTrace` - Thermal transition analysis

3. **visualization/** - Matplotlib-based plotting
   - `BaseGraph` - Abstract base class defining plot interface
   - `TraceGraph`, `GPCTraceGraph` - Multi-trace line plots
   - `KineticsGraph` - Scatter plots
   - `DSCTraceGraph` - DSC-specific plots

### Key Patterns

**Calibration Loading**: GPC molecular weight calibrations can be loaded two ways:
- Direct dictionary: `{'type': 'cubic', 'params': [a, b, c, d]}`
- JSON file reference: `'path/to/calibrations.json:calibration_name'`

The `resolve_calibration()` function in `tools/utils/calibration_loader.py` handles both formats transparently.

**Factory Methods**: Analysis and visualization classes provide `from_file()` class methods that combine processing and object creation:
```python
traces = GPCTrace.from_file('tosoh', 'data.txt', calibration)
graph = DSCTraceGraph.from_file('trios', 'data.csv', 'output.png')
```

**Instrument Abstraction**: Processors accept an `instrument_type` string (e.g., 'shimadzu', 'tosoh', 'trios') to select the appropriate parser implementation.

## Testing

Tests use pytest with fixtures. Test classes are organized by feature area. Tests run from the project root directory and reference example data files in `examples/`.

## Dependencies

Defined in `pyproject.toml`:
- Core: pandas (>=2.0.0), numpy, scipy, matplotlib
- Dev: pytest (>=7.0.0), pytest-cov
