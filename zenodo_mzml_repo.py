import re
import requests
import numpy as np
from pyteomics import mzml
import matplotlib.pyplot as plt
import scipy.signal as signal
import time

###
# Documentation:
# all_files stores the size of each file in the database
# all_scans is a dictionary of tuples where each key is a file name and the value is a tuple containing:
#     1. scan_dict: a dictionary with keys as scan numbers and values as byte offsets
#     2. first_scan: the first scan number in the file
#     3. max_scan: the last scan number in the file
#     4. file_url: the file's URL
#     5. file_size: the file's size in bytes
# E.g. to access the scan_dict for a file, use all_scans[file_name][0].
# The populate_all_scans() method populates the scan_dict for a given file.
# Toggle between partial and full indexing via the partial_indexing attribute.
# The get_scan() method retrieves a specific scan from the file and returns it as a dictionary.
# get_scan() depends on populate_all_scans() since it retrieves the desired scan's byte offset from all_scans
# Data structure returned by get_scan() is a dictionary with keys:
# 'mz': m/z values (numpy array)
# 'intensities': normalized intensity values (numpy array)
# 'rt time': retention time (float or 'N/A')
# 'charge': charge state (int or 'N/A')
# 'collision energy': collision energy (float or 'N/A')
# 'ms level': MS level (int or 'N/A')
###


class mzml_repo:
   def __init__(self, databaseNum):
      self.database_num = databaseNum
      self.all_files = {}
      self.all_scans = {}
      self.partial_indexing = True
      self.get_files()

   def get_files(self):
      if self.all_files != {}:
         print("File names already retrieved.")
         return
      request_url = f"https://zenodo.org/api/records/{self.database_num}"
      response = requests.get(request_url)
      response.raise_for_status()
      data = response.json()

      # Loop through the files to find a .mzML file
      self.all_files = {file['key']: file['size'] for file in data['files'] if file['key'].endswith('.mzML')}
      print("Available files:")
      for file, size in self.all_files.items():
         if size < 1024:
            size_str = f"{size} bytes"
         elif size < 1024**2:
            size_str = f"{size / 1024:.2f} KB"
         elif size < 1024**3:
            size_str = f"{size / 1024**2:.2f} MB"
         else:
            size_str = f"{size / 1024**3:.2f} GB"
         print(f"{file} ({size_str})")

   # Create an entry in all_scans for each file and a list of its offsets
   def populate_all_scans_full(self, file_name):
      if file_name not in list(self.all_files.keys()):
         raise ValueError("File not found in the database.")
      file_url = f"https://zenodo.org/record/{self.database_num}/files/{file_name}"
      file_size = self.all_files[file_name]
      if not file_url:
         raise ValueError("No .mzML file found in the provided Zenodo database.")

      start_byte = file_size - 250000
      end_byte = file_size - 1
      headers = {"Range": f"bytes={start_byte}-{end_byte}"}
      response = requests.get(file_url, headers=headers, stream=True)
      response.raise_for_status()

      with open("indexed_part.mzML", "wb") as f:
         for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

      while True:
         with open("indexed_part.mzML", "r", encoding="utf-8") as f:
            text = f.read()

         if "</mzML>" in text:
            break

         start_byte = max(0, start_byte - 250000)
         headers = {"Range": f"bytes={start_byte}-{end_byte}"}
         response = requests.get(file_url, headers=headers, stream=True)
         response.raise_for_status()

         with open("indexed_part.mzML", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
               f.write(chunk)

      # If text contains <offset idRef="abcd scan=123">456</offset> then matches stores ('123', '456')
      matches = re.findall(r'<offset idRef="[^"]*?(\d+)">(\d+)</offset>', text)
      # scan_dict stores [123] = 456
      scan_dict = {int(scan_id): int(offset) for scan_id, offset in matches}
      first_scan = list(scan_dict.keys())[0] if scan_dict else None
      max_scan = list(scan_dict.keys())[-1] if scan_dict else None
      print(f"First scan: {first_scan}, Max scan: {max_scan}")
      if max_scan is None:
         raise ValueError("No key containing a scan number found in scan_dict")
      self.all_scans[file_name] = (scan_dict, first_scan, max_scan, file_url, file_size)
   
   # Create an entry in all_scans for each file and a list of its offsets, but only up until the given scan number is read
   def populate_all_scans_partial(self, file_name, scan_number):
      if file_name not in list(self.all_files.keys()):
         raise ValueError("File not found in the database.")
      file_url = f"https://zenodo.org/record/{self.database_num}/files/{file_name}"
      file_size = self.all_files[file_name]
      if not file_url:
         raise ValueError("No .mzML file found in the provided Zenodo database.")
      
      start_byte = file_size - 250000
      end_byte = file_size - 1
      headers = {"Range": f"bytes={start_byte}-{end_byte}"}
      response = requests.get(file_url, headers=headers, stream=True)
      response.raise_for_status()

      with open("indexed_part.mzML", "wb") as f:
         for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
      
      with open("indexed_part.mzML", "r", encoding="utf-8") as f:
            text = f.read()
      # If text contains <offset idRef="abcd scan=123">456</offset> then matches stores ('123', '456')
      matches = re.findall(r'<offset idRef="[^"]*?(\d+)">(\d+)</offset>', text)
      # scan_dict stores [123] = 456
      scan_dict = {int(scan_id): int(offset) for scan_id, offset in matches}
      while scan_number not in scan_dict:
         if "</mzML>" in text:
            break
         start_byte = max(0, start_byte - 250000)
         headers = {"Range": f"bytes={start_byte}-{end_byte}"}
         response = requests.get(file_url, headers=headers, stream=True)
         response.raise_for_status()

         with open("indexed_part.mzML", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
               f.write(chunk)
         with open("indexed_part.mzML", "r", encoding="utf-8") as f:
            text = f.read()
         new_matches = re.findall(r'<offset idRef="[^"]*?(\d+)">(\d+)</offset>', text)
         new_matches.extend(matches)
         matches = new_matches
         scan_dict = {int(scan_id): int(offset) for scan_id, offset in matches}

      first_scan = list(scan_dict.keys())[0] if scan_dict else None
      max_scan = list(scan_dict.keys())[-1] if scan_dict else None
      print(f"First scan: {first_scan}, Max scan: {max_scan}")
      if max_scan is None:
         raise ValueError("No key containing a scan found in scan_dict")
      if not(self.all_scans.get(file_name) and self.all_scans[file_name][1] <= first_scan):
         self.all_scans[file_name] = (scan_dict, first_scan, max_scan, file_url, file_size)
   
   def populate_all_scans(self, file_name, scan_number):
      if self.partial_indexing:
         self.populate_all_scans_partial(file_name, scan_number)
      else:
         self.populate_all_scans_full(file_name)

   # If a file is in all_scans already, return the scan. If not, call populate_all_scans first.
   def get_scan(self, file_name, given_scan):
      start_time = time.time()  # Start the timer

      given_scan = int(given_scan)
      if(file_name not in list(self.all_files.keys())):
         raise ValueError("File not found in the database.")
      if (file_name not in self.all_scans) or (given_scan not in self.all_scans[file_name][0]):
         print(f"Scan {given_scan} not found in all_scans for {file_name}.\nPopulating all scans...")
         self.populate_all_scans(file_name, given_scan)

      scan_dict = self.all_scans[file_name][0]
      scan_numbers = list(scan_dict.keys())
      max_scan = self.all_scans[file_name][2]
      file_url = self.all_scans[file_name][3]
      file_size = self.all_scans[file_name][4]
      desired_scan = str(given_scan)
      if desired_scan.startswith('0'):
         desired_scan = desired_scan.lstrip('0')
      if(desired_scan.isdigit() and (0 <= int(desired_scan) <= max_scan)):
         if int(desired_scan) not in scan_numbers:
            print(f"Scan {desired_scan} not found. Please try again.")
            return
      else:
         print(f"Not a valid scan number. Please try again.")
         return
      next_scan_number = None
      for scan_num in scan_numbers[1:]:
         if scan_num > int(desired_scan):
            next_scan_number = scan_num
            break
      end_scan_id = next_scan_number
      scan_start = scan_dict[given_scan]
      scan_end = scan_dict[end_scan_id] - 10 if end_scan_id else file_size - 1

      # Request the specific scan range from the server
      headers = {"Range": f"bytes={scan_start}-{scan_end}"}
      response = requests.get(file_url, headers=headers, stream=True)
      response.raise_for_status()

      with open("target_scan.mzML", "wb") as f:
         for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
      print(f"Downloaded scan {desired_scan}")

      # If searching the last index, ensure the file cuts off exactly at </spectrum>
      if not end_scan_id:
         with open("target_scan.mzML", "rb+") as f:
            f.seek(0, 2)  # Move to the end of the file
            target_size = f.tell()
            f.seek(0)  # Move back to the start of the file
            content = f.read(target_size).decode("utf-8", errors="ignore")
            last_spectrum_end = content.rfind("</spectrum>")
            if last_spectrum_end != -1:
                  f.seek(last_spectrum_end + len("</spectrum>"))
                  f.truncate()

      with mzml.read("target_scan.mzML") as reader:
         for spectrum in reader:
            mz_values = spectrum['m/z array']
            intensity_values = spectrum['intensity array']
            retention_time = spectrum.get('scanList', {}).get('scan', [{}])[0].get('scan start time', 'N/A')
            charge_state = spectrum.get('precursorList', {}).get('precursor', [{}])[0].get('selectedIonList', {}).get('selectedIon', [{}])[0].get('charge state', 'N/A')
            collision_energy = spectrum.get('precursorList', {}).get('precursor', [{}])[0].get('activation', {}).get('collision energy', 'N/A')
            ms_level = spectrum.get('ms level', 'N/A')
            precursor_mz = 'N/A'
            if 'precursorList' in spectrum:
               precursors = spectrum['precursorList'].get('precursor', [])
               if precursors:
                  selected_ions = precursors[0].get('selectedIonList', {}).get('selectedIon', [])
                  if selected_ions:
                        precursor_mz = selected_ions[0].get('selected ion m/z', 'N/A')

            # max_intensity = max(intensity_values)
            # normalized_intensities = intensity_values / max_intensity
            filtered_mz = mz_values # Can add a filtering option here if desired
            # filtered_intensity = normalized_intensities

      # Return scan as a dictionary
      scan_data = {
         'mz': filtered_mz,
         'precursor_mz': precursor_mz,
         'intensities': intensity_values,
         'rt time': retention_time,
         'charge': charge_state,
         'collision energy': collision_energy,
         'ms level': ms_level
      }

      end_time = time.time()  # End the timer
      print(f"Time taken to retrieve scan {given_scan}: {end_time - start_time:.2f} seconds")  # Print runtime

      return scan_data