# Utilities Module

The utilities module provides helper classes and functions for calibration management and mathematical operations.

## Module: `polychemtools.utils`

---

## Calibration Loader

```python
from polychemtools.utils.calibration_loader import (
    load_calibration,
    parse_calibration_string,
    resolve_calibration
)
```

Functions for loading GPC calibration data from JSON files.

### Calibration File Format

Calibration files are JSON with named calibrations:

```json
{
    "sample_calibration": {
        "type": "cubic",
        "params": [-0.001701334, 0.064349247, -1.197289570, 14.035147838]
    },
    "another_calibration": {
        "type": "linear",
        "params": [-0.5, 10.0]
    }
}
```

### Functions

#### `load_calibration`

```python
def load_calibration(filepath: str, calibration_name: str) -> Dict[str, Any]
```

Load a calibration by name from a JSON file.

**Parameters:**
- `filepath` - Path to JSON calibration file
- `calibration_name` - Name of calibration to load

**Returns:** Dict with `'type'` and `'params'` keys

**Raises:**
- `CalibrationFileError` - If file cannot be read or parsed
- `CalibrationNotFoundError` - If calibration name not found
- `InvalidCalibrationError` - If calibration structure is invalid

**Example:**
```python
calibration = load_calibration('calibrations.json', 'sample_calibration')
print(calibration)
# {'type': 'cubic', 'params': [-0.0017, 0.064, -1.197, 14.035]}
```

#### `parse_calibration_string`

```python
def parse_calibration_string(calibration_string: str) -> Tuple[str, str]
```

Parse a calibration string in format `'filepath:calibration_name'`.

**Parameters:**
- `calibration_string` - String in format `'filepath:calibration_name'`

**Returns:** Tuple of (filepath, calibration_name)

**Raises:**
- `ValueError` - If string format is invalid

**Example:**
```python
filepath, name = parse_calibration_string('../data/calibrations.json:sample_calibration')
# filepath = '../data/calibrations.json'
# name = 'sample_calibration'
```

#### `resolve_calibration`

```python
def resolve_calibration(calibration: dict | str) -> Dict[str, Any]
```

Resolve a calibration from either a dict or filepath string.

**Parameters:**
- `calibration` - Either a calibration dict or filepath string

**Returns:** Calibration dict with `'type'` and `'params'` keys

**Raises:**
- `ValueError` - If calibration is neither dict nor string
- `CalibrationFileError` - If file loading fails
- `CalibrationNotFoundError` - If calibration name not found
- `InvalidCalibrationError` - If calibration structure is invalid

**Example:**
```python
# Dict format (backward compatible)
cal = resolve_calibration({'type': 'cubic', 'params': [1, 2, 3, 4]})

# String format
cal = resolve_calibration('../data/calibrations.json:sample_calibration')
```

### Exceptions

#### `CalibrationError`

Base exception for all calibration-related errors.

#### `CalibrationFileError`

Raised when the calibration file cannot be read or parsed.

#### `CalibrationNotFoundError`

Raised when a requested calibration name is not found in the file.

#### `InvalidCalibrationError`

Raised when calibration data has invalid structure (missing `'type'` or `'params'`).

---

## LogNormal

```python
from polychemtools.utils.log_normal import LogNormal
```

Log-normal distribution class for polymer molecular weight modeling and deconvolution.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `sigma` | `float` | Shape parameter (must be > 0) |
| `mu` | `float` | Location parameter (default: 0) |
| `scale` | `float` | Scale factor (default: 1) |

### Constructor

```python
LogNormal(sigma: float, mu: float = 0, scale: float = 1)
```

**Parameters:**
- `sigma` - Shape parameter (width of distribution, must be > 0)
- `mu` - Location parameter (log of median)
- `scale` - Scaling factor for amplitude

**Raises:**
- `ValueError` - If sigma <= 0

**Example:**
```python
# Distribution centered at MW = e^12 ≈ 162,755
dist = LogNormal(sigma=0.3, mu=12, scale=1.0)
```

### Methods

#### `pdf`

```python
def pdf(self, x: float | np.ndarray) -> float | np.ndarray
```

Calculate the probability density function.

**Parameters:**
- `x` - Values at which to evaluate PDF (must be positive)

**Returns:** PDF values

**Raises:**
- `ValueError` - If any x values are <= 0

**Example:**
```python
dist = LogNormal(sigma=0.3, mu=np.log(100000))

# Single value
y = dist.pdf(100000)

# Array of values
mws = np.logspace(3, 6, 100)
y = dist.pdf(mws)
```

### Properties

#### `mn`

```python
@property
def mn(self) -> float
```

Number average molecular weight.

**Returns:** Mn = exp(μ + σ²/2)

#### `mw`

```python
@property
def mw(self) -> float
```

Weight average molecular weight.

**Returns:** Mw = exp(σ²) × Mn

#### `dispersity`

```python
@property
def dispersity(self) -> float
```

Dispersity (Mw/Mn).

**Returns:** Đ = exp(σ²)

**Example:**
```python
dist = LogNormal(sigma=0.3, mu=np.log(50000))
print(f"Mn: {dist.mn:.0f}")
print(f"Mw: {dist.mw:.0f}")
print(f"Dispersity: {dist.dispersity:.2f}")
```

---

## Mathematical Background

### Log-Normal Distribution for Polymers

The log-normal distribution is commonly used to model polymer molecular weight distributions from controlled polymerizations. For a polymer with:

- **σ (sigma)**: Related to the dispersity via Đ = exp(σ²)
- **μ (mu)**: Related to the median MW via M_median = exp(μ)

The number average (Mn) and weight average (Mw) molecular weights are:

```
Mn = exp(μ + σ²/2)
Mw = exp(μ + 3σ²/2)
Đ = Mw/Mn = exp(σ²)
```

### GPC Calibration Types

| Type | Equation | Parameters |
|------|----------|------------|
| `'linear'` | MW = 10^(a×RT + b) | [a, b] |
| `'cubic'` | MW = 10^(a×RT³ + b×RT² + c×RT + d) | [a, b, c, d] |

Where RT is retention time in minutes.
