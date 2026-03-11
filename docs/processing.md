# Processing Module

The processing module provides data parsers for various analytical instruments. Each processor handles instrument-specific file formats and extracts the relevant data.

## Module: `polychemtools.processing`

---

## GPCData

```python
from polychemtools.processing.gpc_data_processor import GPCData
```

Gel permeation chromatography data parser from instrumental data.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `retention_times` | `np.ndarray` | 1D array of retention times |
| `intensities` | `np.ndarray` | 2D array of intensities (columns = traces) |

### Supported Instruments

- `'tosoh'` - Tosoh GPC system (whitespace-delimited text files)

### Constructor

```python
GPCData(retention_times: np.ndarray, intensities: np.ndarray)
```

**Parameters:**
- `retention_times` - 1D array of retention times
- `intensities` - 2D array of intensities (columns = different traces)

### Class Methods

#### `from_file`

```python
@classmethod
def from_file(cls, instrument: str, file_path: str) -> GPCData
```

Create GPCData from an instrument data file.

**Parameters:**
- `instrument` - Instrument type (`'tosoh'`)
- `file_path` - Path to the GPC data file

**Returns:** `GPCData` instance

**Raises:**
- `UnsupportedInstrumentError` - If instrument type is not supported
- `ValueError` - If file format is invalid

**Example:**
```python
gpc_data = GPCData.from_file('tosoh', 'data.txt')
print(f"Number of traces: {len(gpc_data)}")
```

### Methods

#### `__len__`

```python
def __len__(self) -> int
```

Returns the number of GPC traces in the data.

---

## GCData

```python
from polychemtools.processing.gc_data_processor import GCData
```

Gas chromatography data parser with instrument-specific parsing.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `instrument` | `str` | The GC instrument type |
| `peak_retention_times` | `np.ndarray` | 1D array of peak retention times |
| `peak_areas` | `np.ndarray` | 1D array of peak areas |
| `chromatogram_times` | `np.ndarray` | 1D array of chromatogram retention times |
| `chromatogram_intensities` | `np.ndarray` | 1D array of chromatogram intensities |

### Supported Instruments

- `'shimadzu'` - Shimadzu GC system (tab-delimited text files)

### Constructor

```python
GCData(instrument: str, file_path: str)
```

**Parameters:**
- `instrument` - GC instrument type (`'shimadzu'`)
- `file_path` - Path to the GC data file

**Raises:**
- `UnsupportedInstrumentError` - If instrument type is not supported
- `FileNotFoundError` - If file does not exist

### Methods

#### `get_peak_areas`

```python
def get_peak_areas(
    self,
    retention_times: List[float],
    tolerance: float = 0.10
) -> List[Optional[float]]
```

Extract peak areas at specified retention times.

**Parameters:**
- `retention_times` - List of target retention times (minutes)
- `tolerance` - Matching tolerance (±tolerance minutes, default: 0.10)

**Returns:** List of peak areas (None if no peak found at that RT)

**Raises:**
- `MultiplePeaksFoundError` - If multiple peaks found within tolerance

**Example:**
```python
gc = GCData('shimadzu', 'gc_data.txt')
areas = gc.get_peak_areas([5.2, 8.7, 12.3], tolerance=0.05)
for rt, area in zip([5.2, 8.7, 12.3], areas):
    if area:
        print(f"RT {rt}: Area = {area}")
    else:
        print(f"RT {rt}: No peak found")
```

#### `get_chromatogram`

```python
def get_chromatogram(
    self,
    time_range: Optional[tuple[float, float]] = None
) -> tuple[np.ndarray, np.ndarray]
```

Extract chromatogram data.

**Parameters:**
- `time_range` - Optional (min_time, max_time) tuple to filter data

**Returns:** Tuple of (retention_times, intensities) arrays

**Raises:**
- `ValueError` - If time_range is invalid

**Example:**
```python
gc = GCData('shimadzu', 'gc_data.txt')

# Get full chromatogram
times, intensities = gc.get_chromatogram()

# Get specific time range
times, intensities = gc.get_chromatogram(time_range=(5.0, 15.0))
```

---

## DSCData

```python
from polychemtools.processing.dsc_data_processor import DSCData
```

Differential scanning calorimetry data parser.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `instrument` | `str` | DSC instrument type |
| `file_path` | `str` | Path to data file |
| `temperatures` | `np.ndarray` | 1D array of temperatures (°C) |
| `heat_flows` | `np.ndarray` | 1D array of heat flows (W/g) |
| `ramp_indices` | `np.ndarray` | Indices where ramps start |

### Supported Instruments

- `'trios'` - TA Instruments Trios software (CSV files)

### Constructor

```python
DSCData(instrument: str, file_path: str)
```

**Parameters:**
- `instrument` - DSC instrument type (`'trios'`)
- `file_path` - Path to DSC CSV file

**Raises:**
- `UnsupportedInstrumentError` - If instrument type is not supported
- `FileNotFoundError` - If file does not exist
- `ValueError` - If file format is invalid

### Methods

#### `get_ramp_data`

```python
def get_ramp_data(
    self,
    ramp_index: int,
    reverse: bool = False
) -> Tuple[np.ndarray, np.ndarray]
```

Get temperature and heat flow data for a specific ramp.

**Parameters:**
- `ramp_index` - Index of ramp (0-based, negative indices supported)
- `reverse` - If True, reverse the data arrays

**Returns:** Tuple of (temperatures, heat_flows) arrays

**Raises:**
- `IndexError` - If ramp_index is out of range

**Example:**
```python
dsc = DSCData('trios', 'experiment.csv')

# Get last ramp (typically second heating), reversed for analysis
temps, flows = dsc.get_ramp_data(-1, reverse=True)

# Get first heating curve
temps, flows = dsc.get_ramp_data(0)
```

#### `__len__`

```python
def __len__(self) -> int
```

Returns the number of ramps in the DSC data.

---

## Exceptions

### UnsupportedInstrumentError

```python
from polychemtools.processing.data_processor import UnsupportedInstrumentError
```

Raised when an unsupported instrument type is specified.

### MultiplePeaksFoundError

```python
from polychemtools.processing.gc_data_processor import MultiplePeaksFoundError
```

Raised when multiple peaks are found within the specified tolerance for GC peak matching.
