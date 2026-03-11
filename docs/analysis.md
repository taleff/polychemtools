# Analysis Module

The analysis module provides classes for analyzing processed chromatography and calorimetry data, including molecular weight calculations and thermal transition analysis.

## Module: `polychemtools.analysis`

---

## GPCTrace

```python
from polychemtools.analysis.gpc_trace import GPCTrace
```

Represents a single GPC trace with methods for molecular weight analysis.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `retention_times` | `np.ndarray` | 1D array of retention times |
| `intensities` | `np.ndarray` | 1D array of measured intensities |
| `molecular_weights` | `np.ndarray` or `None` | 1D array of molecular weights (if calibrated) |

### Class Constants

| Constant | Default | Description |
|----------|---------|-------------|
| `PEAK_HEIGHT_THRESHOLD` | 0 | Minimum peak height for detection |
| `PEAK_PROMINENCE` | 0.2 | Minimum prominence (0-1 scale) |
| `PEAK_WIDTH` | 5 | Minimum peak width in data points |
| `MINIMUM_POLYMER_MW` | 500 | Minimum MW for valid polymer peaks |
| `BASELINE_THRESHOLD` | 0.99 | Relative height for peak bounds |

### Supported Calibration Types

- `'linear'` - Linear calibration: `10^(a*x + b)`
- `'cubic'` - Cubic calibration: `10^(a*x³ + b*x² + c*x + d)`

### Constructor

```python
GPCTrace(
    retention_times: np.ndarray,
    intensities: np.ndarray,
    calibration: dict | str | None = None
)
```

**Parameters:**
- `retention_times` - 1D array of retention times
- `intensities` - 1D array of intensities
- `calibration` - Calibration data (dict, filepath string, or None)

**Raises:**
- `ValueError` - If arrays have mismatched lengths
- `ValueError` - If retention times are not monotonically increasing

### Class Methods

#### `from_file`

```python
@classmethod
def from_file(
    cls,
    instrument: str,
    file_path: str,
    calibration: dict | str | None = None,
    bounds: Tuple[float, float] | None = None,
    correction: str | None = None
) -> Tuple[GPCTrace, ...]
```

Create GPCTrace objects from a data file.

**Parameters:**
- `instrument` - Instrument type (`'tosoh'`)
- `file_path` - Path to GPC data file
- `calibration` - Calibration data or filepath string
- `bounds` - Optional molecular weight bounds to restrict traces
- `correction` - Baseline correction method (`'span'` or None)

**Returns:** Tuple of GPCTrace objects

**Example:**
```python
# Using dict calibration
cal = {'type': 'cubic', 'params': [-0.0017, 0.064, -1.197, 14.035]}
traces = GPCTrace.from_file('tosoh', 'data.txt', cal)

# Using filepath string
traces = GPCTrace.from_file('tosoh', 'data.txt',
                            'calibrations.json:sample_calibration')

# With bounds and baseline correction
traces = GPCTrace.from_file('tosoh', 'data.txt', cal,
                            bounds=(1000, 100000), correction='span')
```

### Molecular Weight Methods

#### `number_average_molecular_weight`

```python
def number_average_molecular_weight(self, bounds: Tuple[float, float]) -> float
```

Calculate the number average molecular weight (Mn).

**Parameters:**
- `bounds` - (min_MW, max_MW) tuple for integration range

**Returns:** Number average molecular weight

**Raises:**
- `MissingCalibrationError` - If no calibration provided
- `ValueError` - If no signal in specified bounds

#### `weight_average_molecular_weight`

```python
def weight_average_molecular_weight(self, bounds: Tuple[float, float]) -> float
```

Calculate the weight average molecular weight (Mw).

**Parameters:**
- `bounds` - (min_MW, max_MW) tuple for integration range

**Returns:** Weight average molecular weight

**Raises:**
- `MissingCalibrationError` - If no calibration provided
- `ValueError` - If no signal in specified bounds

#### `dispersity`

```python
def dispersity(self, bounds: Tuple[float, float]) -> float
```

Calculate the dispersity (Mw/Mn).

**Parameters:**
- `bounds` - (min_MW, max_MW) tuple for integration range

**Returns:** Dispersity value

#### `moment`

```python
def moment(self, n: int, bounds: Tuple[float, float]) -> float
```

Calculate the nth moment of the molecular weight distribution.

**Parameters:**
- `n` - Moment order (0, 1, 2, etc.)
- `bounds` - (min_MW, max_MW) tuple for integration range

**Returns:** The nth moment value

### Peak Analysis Methods

#### `peak_finder`

```python
def peak_finder(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
```

Find peaks and their bounds in the GPC trace.

**Returns:** Tuple of (peak_mw, peak_heights, left_bounds, right_bounds)

**Raises:**
- `MissingCalibrationError` - If no calibration provided
- `NoPeakError` - If no valid peaks found

#### `peaks` (property)

```python
@property
def peaks(self) -> np.ndarray
```

Get molecular weights of detected peaks.

**Returns:** Array of peak molecular weights

#### `analyze_peaks`

```python
def analyze_peaks(self) -> PolymerSample
```

Analyze all peaks and return polymer properties.

**Returns:** `PolymerSample` containing `Polymer` objects for each peak

**Example:**
```python
trace = GPCTrace.from_file('tosoh', 'data.txt', calibration)[0]
sample = trace.analyze_peaks()
print(sample)
# PolymerSample(2 polymers):
#   Peak 1: Mn: 15000 g/mol; Mw: 18000 g/mol; D: 1.20
#   Peak 2: Mn: 45000 g/mol; Mw: 52000 g/mol; D: 1.16
```

#### `tight_bounds` (property)

```python
@property
def tight_bounds(self) -> Tuple[float, float]
```

Get bounds that encompass all detected peaks.

**Returns:** (min_bound, max_bound) tuple

### Trace Manipulation Methods

#### `restrict_molecular_weights`

```python
def restrict_molecular_weights(self, bounds: Tuple[float, float]) -> GPCTrace
```

Create a new trace restricted to a molecular weight range.

**Parameters:**
- `bounds` - (min_MW, max_MW) tuple

**Returns:** New GPCTrace with restricted range

#### `restrict_retention_times`

```python
def restrict_retention_times(self, bounds: Tuple[float, float]) -> GPCTrace
```

Create a new trace restricted to a retention time range.

**Parameters:**
- `bounds` - (min_RT, max_RT) tuple

**Returns:** New GPCTrace with restricted range

#### `correct_baseline`

```python
def correct_baseline(self, correction: str | None) -> None
```

Apply baseline correction to intensities (modifies in place).

**Parameters:**
- `correction` - Correction method (`'span'` for linear baseline, or None)

#### `get_normalized_intensities`

```python
def get_normalized_intensities(self) -> np.ndarray
```

Get intensities normalized to maximum = 1.

**Returns:** Normalized intensity array

#### `get_mole_fractions`

```python
def get_mole_fractions(self) -> np.ndarray
```

Get the mole fraction distribution.

**Returns:** Mole fraction array

### Deconvolution

#### `deconvolute`

```python
def deconvolute(
    self,
    parts: int,
    bounds: Tuple[float, float]
) -> List[LogNormal]
```

Deconvolute trace into log-normal Gaussian components.

**Parameters:**
- `parts` - Number of Gaussians to fit
- `bounds` - (min_MW, max_MW) range for fitting

**Returns:** List of fitted `LogNormal` objects

**Example:**
```python
trace = GPCTrace.from_file('tosoh', 'data.txt', calibration)[0]
gaussians = trace.deconvolute(2, (1000, 500000))
for g in gaussians:
    print(f"Mn: {g.mn:.0f}, Mw: {g.mw:.0f}, D: {g.dispersity:.2f}")
```

### Utility Methods

#### `input_calibration`

```python
def input_calibration(self, calibration: dict) -> None
```

Apply calibration to calculate molecular weights.

**Parameters:**
- `calibration` - Dict with `'type'` and `'params'` keys

#### `has_calibration` (property)

```python
@property
def has_calibration(self) -> bool
```

Check if calibration data exists.

#### `retention_time_index`

```python
def retention_time_index(self, retention_time: float) -> int
```

Find the index for a given retention time.

#### `molecular_weight_index`

```python
def molecular_weight_index(self, molecular_weight: float) -> int
```

Find the index for a given molecular weight.

#### `peak_area`

```python
def peak_area(self, bounds: Tuple[float, float]) -> float
```

Calculate peak area within retention time bounds.

---

## Polymer

```python
from polychemtools.analysis.gpc_trace import Polymer
```

Dataclass representing a single polymer and its properties.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `mn` | `float` | Number average molecular weight |
| `mw` | `float` | Weight average molecular weight |
| `dispersity` | `float` | Dispersity (Mw/Mn) |

---

## PolymerSample

```python
from polychemtools.analysis.gpc_trace import PolymerSample
```

Dataclass representing a sample containing multiple polymers.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `polymers` | `List[Polymer]` | List of Polymer objects |

---

## DSCTrace

```python
from polychemtools.analysis.dsc_trace import DSCTrace
```

Represents a single DSC ramp with methods for thermal analysis.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `temperatures` | `np.ndarray` | 1D array of temperatures (°C) |
| `heat_flows` | `np.ndarray` | 1D array of heat flows (W/g) |

### Constructor

```python
DSCTrace(temperatures: np.ndarray, heat_flows: np.ndarray)
```

**Parameters:**
- `temperatures` - 1D array of temperature values
- `heat_flows` - 1D array of heat flow values

**Raises:**
- `ValueError` - If arrays have different lengths or invalid dimensions

**Note:** If temperature data is not monotonically increasing, it will be automatically sorted with a warning logged.

### Class Methods

#### `from_file`

```python
@classmethod
def from_file(
    cls,
    instrument: str,
    file_path: str,
    ramp_index: int = -1,
    reverse: bool = True
) -> DSCTrace
```

Create a DSCTrace from a data file.

**Parameters:**
- `instrument` - DSC instrument type (`'trios'`)
- `file_path` - Path to DSC data file
- `ramp_index` - Index of ramp to extract (default: -1, last ramp)
- `reverse` - If True, reverse data (default: True)

**Returns:** DSCTrace object

**Example:**
```python
# Get second heating curve (last ramp, reversed)
trace = DSCTrace.from_file('trios', 'experiment.csv')

# Get first heating curve
trace = DSCTrace.from_file('trios', 'experiment.csv', ramp_index=0, reverse=False)
```

### Methods

#### `measure_slope`

```python
def measure_slope(
    self,
    temperature_range: Tuple[float, float],
    return_fit_data: bool = False
) -> float | Tuple[float, float, np.ndarray, np.ndarray]
```

Measure baseline slope in a temperature range.

**Parameters:**
- `temperature_range` - (min_temp, max_temp) for slope measurement
- `return_fit_data` - If True, return additional fit data

**Returns:**
- If `return_fit_data=False`: slope (W/g/°C)
- If `return_fit_data=True`: (slope, intercept, fit_temps, fit_flows)

**Raises:**
- `ValueError` - If range is invalid or contains no data

**Example:**
```python
trace = DSCTrace.from_file('trios', 'experiment.csv')

# Simple slope measurement
slope = trace.measure_slope((55, 60))

# With fit data for plotting
slope, intercept, temps, flows = trace.measure_slope((55, 60), return_fit_data=True)
```

#### `normalize_to_baseline`

```python
def normalize_to_baseline(self, baseline_value: float | None = None) -> np.ndarray
```

Normalize heat flows by subtracting a baseline value.

**Parameters:**
- `baseline_value` - Value to subtract (default: last heat flow value)

**Returns:** Normalized heat flow array

#### `get_temperature_index`

```python
def get_temperature_index(self, temperature: float) -> int
```

Find the index closest to a given temperature.

---

## Exceptions

### MissingCalibrationError

```python
from polychemtools.analysis.gpc_trace import MissingCalibrationError
```

Raised when operations requiring calibration are called without calibration data.

### NoPeakError

```python
from polychemtools.analysis.gpc_trace import NoPeakError
```

Raised when no valid peaks are found in a GPC trace.
