# Analysis Module

The analysis module provides classes for calculating molecular weight statistics, thermal transitions, and other derived quantities from raw instrument data.

## GPC Analysis

### GPCTrace

Represents a single GPC trace with methods for molecular weight analysis.

```python
from polychemtools.analysis import GPCTrace

# Create from file (recommended)
traces = GPCTrace.from_file(
    'tosoh',
    'path/to/gpc_data.txt',
    calibration='calibrations.json:my_calibration'
)

# Or create manually
trace = GPCTrace(gpc.retention_times, gpc.intensities[:, 0], calibration)
```

### Calibrations

Calibrations convert retention time to molecular weight. They can be specified two ways:

**Dictionary format:**
```python
calibration = {
    'type': 'cubic',
    'params': [-0.001701334, 0.064349247, -1.197289570, 14.035147838]
}
```

**JSON file reference:**
```python
calibration = 'calibrations.json:sample_calibration'
```

The JSON file should contain named calibrations:
```json
{
  "sample_calibration": {
    "type": "cubic",
    "params": [-0.001701334, 0.064349247, -1.197289570, 14.035147838]
  },
}
```

**Calibration types:**
- `linear`: MW = 10^(a*RT + b) where params = [a, b]
- `cubic`: MW = 10^(a*RT^3 + b*RT^2 + c*RT + d) where params = [a, b, c, d]

### Class Methods

#### from_file

Create GPCTrace objects from a data file.

```python
traces = GPCTrace.from_file(
    instrument='tosoh',
    file_path='data.txt',
    calibration='calibrations.json:my_cal',
    bounds=(1000, 100000),  # Optional MW bounds
    correction='span'       # Optional baseline correction
)
```

**Parameters:**
- `instrument` (str): Instrument type (e.g., 'tosoh')
- `file_path` (str): Path to GPC data file
- `calibration` (dict, str, or None): Calibration parameters
- `bounds` (tuple, optional): Molecular weight bounds to restrict the trace
- `correction` (str, optional): Baseline correction method ('span' or None)

**Returns:** Tuple of GPCTrace objects, one for each trace in the file

### Instance Attributes

- `retention_times` (np.ndarray): 1D array of retention times
- `intensities` (np.ndarray): 1D array of measured intensities
- `molecular_weights` (np.ndarray or None): 1D array of molecular weights (if calibrated)
- `has_calibration` (bool): True if calibration data is available

### Molecular Weight Methods

All molecular weight methods require a calibration and take `bounds` as a tuple of (min_MW, max_MW).

#### number_average_molecular_weight

Calculate number-average molecular weight (Mn).

```python
bounds = (1000, 50000)
mn = trace.number_average_molecular_weight(bounds)
print(f"Mn: {mn:.1f} g/mol")
```

#### weight_average_molecular_weight

Calculate weight-average molecular weight (Mw).

```python
mw = trace.weight_average_molecular_weight(bounds)
print(f"Mw: {mw:.1f} g/mol")
```

#### dispersity

Calculate dispersity (D = Mw/Mn).

```python
d = trace.dispersity(bounds)
print(f"D: {d:.2f}")
```

### Peak Detection Methods

#### peak_finder

Find peaks in the GPC trace automatically.

```python
peaks, heights, left_bounds, right_bounds = trace.peak_finder()

# peaks: Molecular weights at peak positions
# heights: Peak heights
# left_bounds: MW at left edge of each peak
# right_bounds: MW at right edge of each peak
```

#### analyze_peaks

Detect peaks and calculate molecular weight statistics for each.

```python
sample = trace.analyze_peaks()
print(sample)
# PolymerSample(2 polymers):
#   Peak 1: Mn: 15234 g/mol; Mw: 23451 g/mol; D: 1.54
#   Peak 2: Mn: 45123 g/mol; Mw: 67890 g/mol; D: 1.50

# Access individual polymers
for polymer in sample.polymers:
    print(f"Mn={polymer.mn:.0f}, Mw={polymer.mw:.0f}, D={polymer.dispersity:.2f}")
```

### Other Methods

#### peak_area

Integrate signal over a range.

```python
# Using retention time bounds
area = trace.peak_area((12.0, 15.0), mw=False)

# Using molecular weight bounds
area = trace.peak_area((5000, 50000), mw=True)
```

#### restrict_molecular_weights

Create a new GPCTrace restricted to a molecular weight range.

```python
restricted = trace.restrict_molecular_weights((1000, 100000))
```

#### restrict_retention_times

Create a new GPCTrace restricted to a retention time range.

```python
restricted = trace.restrict_retention_times((10.0, 20.0))
```

#### correct_baseline

Apply baseline correction to the intensities.

```python
trace.correct_baseline('span')  # Linear baseline from endpoints
```

#### get_normalized_intensities

Get intensities normalized to a maximum of 1.

```python
normalized = trace.get_normalized_intensities()
```

#### deconvolute

Deconvolute a region into log-normal distributions.

```python
gaussians = trace.deconvolute(parts=2, bounds=(5000, 100000))
for g in gaussians:
    print(f"Mn={g.mn:.0f}, Mw={g.mw:.0f}, D={g.dispersity:.2f}")
```

## DSC Analysis

### DSCTrace

Represents a single DSC ramp with methods for thermal analysis.

```python
from polychemtools.analysis import DSCTrace

# Create from file (recommended)
trace = DSCTrace.from_file(
    'trios',
    'experiment.csv',
    ramp_index=-1,  # Last ramp (typically second heating)
    reverse=True    # Reverse for ascending temperature
)

# Or create manually
trace = DSCTrace(temperatures, heat_flows)
```

### Class Methods

#### from_file

Create a DSCTrace from a data file.

```python
trace = DSCTrace.from_file(
    instrument='trios',
    file_path='experiment.csv',
    ramp_index=-1,
    reverse=True
)
```

**Parameters:**
- `instrument` (str): DSC instrument type (e.g., 'trios')
- `file_path` (str): Path to the DSC data file
- `ramp_index` (int): Index of ramp to extract (default: -1, last ramp)
- `reverse` (bool): If True, reverse data for ascending temperature (default: True)

### Instance Attributes

- `temperatures` (np.ndarray): 1D array of temperature values (degrees C)
- `heat_flows` (np.ndarray): 1D array of heat flow values (W/g)

### Methods

#### measure_slope

Measure the slope (baseline) in a temperature range.

```python
# Simple slope measurement
slope = trace.measure_slope((55, 60))
print(f'Baseline slope: {slope:.4f} W/g/C')

# Get full fit data for plotting
slope, intercept, fit_temps, fit_flows = trace.measure_slope(
    (55, 60),
    return_fit_data=True
)
```

**Parameters:**
- `temperature_range` (tuple): (min_temp, max_temp) in degrees C
- `return_fit_data` (bool): If True, return additional fit parameters

**Returns:**
- If `return_fit_data=False`: slope (float)
- If `return_fit_data=True`: (slope, intercept, fit_temps, fit_flows)

#### normalize_to_baseline

Normalize heat flows by subtracting a baseline value.

```python
# Normalize to endpoint (common DSC normalization)
normalized = trace.normalize_to_baseline()

# Normalize to specific value
normalized = trace.normalize_to_baseline(baseline_value=0.5)
```

**Parameters:**
- `baseline_value` (float, optional): Value to subtract. If None, uses the last value.

**Returns:** Normalized heat flow values as numpy array

#### get_temperature_index

Find the index closest to a given temperature.

```python
idx = trace.get_temperature_index(65.0)
```

## Exceptions

- `MissingCalibrationError`: Raised when MW operations are attempted without calibration
- `NoPeakError`: Raised when peak analysis finds no valid peaks

## Utilities

### load_calibration

Load a calibration from a JSON file.

```python
from polychemtools.utils import load_calibration

calibration = load_calibration('calibrations.json', 'sample_calibration')
```

### LogNormal

Log-normal distribution utility for peak deconvolution.

```python
from polychemtools.utils import LogNormal

ln = LogNormal(sigma=0.3, mu=10.0, scale=1.0)
print(f"Mn: {ln.mn:.0f}, Mw: {ln.mw:.0f}, D: {ln.dispersity:.2f}")
```
