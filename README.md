## A Python Package for Mass Spectrometry
Developed by Akshay Jay.  
Use case: create an `mzml_repo` object. After providing a Zenodo database ID, the object stores the name, URL, and size of all files in the database.

Requesting a scan from the file will provide the scan's mz and intensity values along with other metadata. If not already in memory, calling `get_scan()` will store the byte offsets of that scan and all scans that come after it.

## How to Use the Class

- `all_files`: dictionary storing the name (key) and size (value) of each file in the database.  
- `all_scans`: dictionary of tuples where each key is a file name and the value is a tuple containing:  
    1. `scan_dict`: a dictionary with keys as scan numbers and values as byte offsets  
    2. `first_scan`: the first scan number in the file  
    3. `max_scan`: the last scan number in the file  
    4. `file_url`: the file's URL  
    5. `file_size`: the file's size in bytes  

E.g. to access the `scan_dict` for a file, use `all_scans[file_name][0]`.  
The `populate_all_scans()` method populates the `scan_dict` for a given file.  
Toggle between partial and full indexing via the `partial_indexing` attribute.  
### get_scan()
The `get_scan()` method retrieves a specific scan from the file and returns it as a dictionary.  
Data structure returned by `get_scan()` is a dictionary with keys:  
- `'mz'`: m/z values (`numpy` array)  
- `'intensities'`: normalized intensity values (`numpy` array)  
- `'RT-time'`: retention time (float or `'N/A'`)  
- `'charge'`: charge state (int or `'N/A'`)  
- `'collision energy'`: collision energy (float or `'N/A'`)  
- `'ms level'`: MS level (int or `'N/A'`)  

`get_scan()` depends on `populate_all_scans()` since it retrieves the desired scan's byte offset from `all_scans`.

## Valid Formats

The class is able to parse the following `idRef` formats:  
- `idRef="SPECTRUM_XXXX"`  
- `idRef="controllerType=X controllerNumber=X scan=XXXX"`

## Example Usage

```python
import zenodo_mzml_repo

database = 10211590
test_repo = zenodo_mzml_repo.mzml_repo(database)
test_repo.partial_indexing = False
file_name = list(test_repo.all_files.keys())[0]
scan1 = test_repo.get_scan(file_name, 421)
scan2 = test_repo.get_scan(file_name, 1685)
scan3 = test_repo.get_scan(file_name, 8645)
scan4 = test_repo.get_scan(file_name, 255)
print("Scan 1's retention time: " + str(scan1['RT-time']))
print("Scan 2's charge state: " + str(scan2['charge']))
print("Scan 3's collision energy: " + str(scan3['collision energy']))
print("Scan 4's MS level: " + str(scan4['ms level']))
```

## Runtime

Based on 5 tests from 4 Zenodo databases.  
Using a wired connection with ~100Mbps.  
Average file size: 55 MB

### First Scan in a File

- Average runtime: 12.08 seconds  
- Median runtime: 10.29 seconds

### All Successive Scans in the File

- Average Runtime: 0.78 seconds  
- Median Runtime: 0.83 seconds  
(Data table coming soon)