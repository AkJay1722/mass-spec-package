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
- `'rt time'`: retention time (float or `'N/A'`)  
- `'charge'`: charge state (int or `'N/A'`)  
- `'collision energy'`: collision energy (float or `'N/A'`)  
- `'ms level'`: MS level (int or `'N/A'`)
- `'precursor mz'`: Precursor m/z value (float or `'N/A'`)

`get_scan()` depends on `populate_all_scans()` since it retrieves the desired scan's byte offset from `all_scans`.

## Valid Formats

The class is able to parse the following `idRef` formats:  
- `idRef="SPECTRUM_XXXX"`  
- `idRef="controllerType=X controllerNumber=X scan=XXXX"`

## Example Usage

The following example pulls from this Zenodo database: https://zenodo.org/records/7824517  
Uses this file: subset_dq_00086_11cell_90min_hrMS2_A9.mzML  
And this scan number: 16799
```python
import zenodo_mzml_repo

database = 7824517
test_repo = zenodo_mzml_repo.mzml_repo(database)
test_repo.partial_indexing = True
file_name = 'subset_dq_00086_11cell_90min_hrMS2_A9.mzML'
scan1 = test_repo.get_scan(file_name, '16799') # Scan number can be str or int

print("Scan 1's retention time: " + str(scan1['rt time']))
print("Scan 1's charge: " + str(scan1['charge']))
print("Scan 1's collision energy: " + str(scan1['collision energy']))
print("Scan 1's MS level: " + str(scan1['ms level']))
print("Scan 1's precursor m/z: " + str(scan1['precursor_mz']))
print("First 10 values of scan 1's m/z array: " + str(scan1['m/z array'][:10]))
print("First 10 values of scan 1's intensity array: " + str(scan1['intensity array'][:10]))
```
This code should produce the following:
```bash
Available files:
subset_dq_00086_11cell_90min_hrMS2_A9.mzML (1.90 MB)
subset_dq_00084_11cell_90min_hrMS2_A5.mzML (1.47 MB)
subset_dq_00087_11cell_90min_hrMS2_A11.mzML (1.77 MB)
Scan 16799 not found in all_scans for subset_dq_00086_11cell_90min_hrMS2_A9.mzML.
Populating all scans...
First scan: 3381, Max scan: 38682
Downloaded scan 16799
Time taken to retrieve scan 16799: 2.68 seconds
Scan 1's retention time: 2484.495791584002
Scan 1's charge: 4
Scan 1's collision energy: 35.0
Scan 1's MS level: 2
Scan 1's precursor m/z: 508.044647216797
First 10 values of scan 1's m/z array: [100.10274506 100.51384735 101.07068634 101.09996796 102.05473328
 102.21772003 104.05259705 110.06845856 110.07099915 112.08670044]
First 10 values of scan 1's intensity array: [  876.2010498    811.77313232  4443.26025391  2841.00219727
  1590.89794922   841.73175049  1415.2277832   1670.71008301
 29214.15820312  1161.09606934]
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
