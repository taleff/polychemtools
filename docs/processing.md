# Processing Module

The processing module extracts raw data from instrument files. Each class handles a specific instrument type and provides access to the underlying data arrays.

## Gas Chromatography (GC)

### GCData

Parse and extract data from Shimadzu GC data files.

```python
from polychemtools.processing import GCData

gc = GCData('shimadzu', 'path/to/gc_data.TXT')
```

**Parameters:**
- `instrument` (str): Instrument type. Supported: `'shimadzu'`
- `file_path` (str): Path to the GC data file

**Attributes:**
- `peak_retention_times` (np.ndarray): 1D array of retention times for detected peaks
- `peak_areas` (np.ndarray): 1D array of areas for detected peaks
- `chromatogram_times` (np.ndarray): 1D array of retention times for the full chromatogram
- `chromatogram_intensities` (np.ndarray): 1D array of intensities for the full chromatogram

### Methods

#### get_peak_areas

Extract peak areas at specified retention times.

```python
# Single peak
areas = gc.get_peak_areas([3.521], tolerance=0.10)

# Multiple peaks
retention_times = [3.521, 4.234, 5.891]
areas = gc.get_peak_areas(retention_times, tolerance=0.10)
```

**Parameters:**
- `retention_times` (List[float]): Target retention times in minutes
- `tolerance` (float): Search window around each retention time (default: 0.10 minutes)

**Returns:** List of peak areas. Returns `None` for retention times where no peak was found.

**Raises:**
- `MultiplePeaksFoundError`: If multiple peaks found within tolerance window

#### get_chromatogram

Extract chromatogram data, optionally filtered to a time range.

```python
# Get complete chromatogram
rt, intensity = gc.get_chromatogram()

# Get chromatogram in specific time range
rt, intensity = gc.get_chromatogram(time_range=(2.0, 8.0))
```

**Parameters:**
- `time_range` (tuple, optional): Tuple of (min_time, max_time) in minutes

**Returns:** Tuple of (retention_times, intensities) as numpy arrays

## Gel Permeation Chromatography (GPC)

### GPCData

Parse GPC data from Tosoh instrument files.

```python
from polychemtools.processing import GPCData

# Load from file using class method
gpc = GPCData.from_file('tosoh', 'path/to/gpc_data.txt')

# Access data
retention_times = gpc.retention_times
intensities = gpc.intensities  # 2D array, each column is a trace
num_traces = len(gpc)
```

**Class Methods:**
- `from_file(instrument, file_path)`: Load GPC data from file

**Parameters:**
- `instrument` (str): Instrument type. Supported: `'tosoh'`
- `file_path` (str): Path to the GPC data file

**Attributes:**
- `retention_times` (np.ndarray): 1D array of retention times
- `intensities` (np.ndarray): 2D array where each column is a trace

**Methods:**
- `__len__()`: Returns number of traces in file

## Differential Scanning Calorimetry (DSC)

### DSCData

Parse DSC data from TA Instruments Trios CSV files.

```python
from polychemtools.processing import DSCData

dsc = DSCData('trios', 'path/to/experiment.csv')

# Get information about the data
print(f'Number of ramps: {len(dsc)}')
print(f'Total data points: {len(dsc.temperatures)}')
```

**Parameters:**
- `instrument` (str): Instrument type. Supported: `'trios'`
- `file_path` (str): Path to the DSC CSV file

**Attributes:**
- `temperatures` (np.ndarray): 1D array of temperature values (degrees C)
- `heat_flows` (np.ndarray): 1D array of heat flow values (W/g)
- `ramp_indices` (np.ndarray): Array of indices where heating/cooling ramps start

### Methods

#### get_ramp_data

Extract temperature and heat flow data for a specific ramp.

```python
# Get second heating curve (last ramp, reversed for ascending temperature)
temps, flows = dsc.get_ramp_data(ramp_index=-1, reverse=True)

# Get first heating curve
temps, flows = dsc.get_ramp_data(ramp_index=0, reverse=False)

# Get cooling curve (typically second ramp)
temps, flows = dsc.get_ramp_data(ramp_index=1)
```

**Parameters:**
- `ramp_index` (int): Index of the ramp to extract. Negative indices count from end.
- `reverse` (bool): If True, reverse the data arrays (useful for analysis)

**Returns:** Tuple of (temperatures, heat_flows) as numpy arrays

## Exceptions

The processing module defines the following exceptions:

- `UnsupportedInstrumentError`: Raised when an unsupported instrument type is specified
- `MultiplePeaksFoundError`: Raised when multiple peaks are found within the tolerance window (GC only)
