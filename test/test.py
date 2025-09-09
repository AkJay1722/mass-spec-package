import sys
sys.path.append("..")

from zenodo_mzml_repo import mzml_repo

def test_usi():
    usi = "mzspec:ZENODO-10211590:D141_POS.mzML:scan:422"

    zenodo_id = usi.split(":")[1].split("-")[1]
    filename = usi.split(":")[2]
    scan = usi.split(":")[4]

    zenodo_obj = mzml_repo(zenodo_id)
    zenodo_obj.partial_indexing = False
    scan_obj = zenodo_obj.get_scan(filename, int(scan))

    intensity_list = scan_obj["intensities"]
    mz_list = scan_obj["mz"]
    charge = scan_obj["charge"]
    precursor_mz = scan_obj["precursor_mz"]

    print(charge)
    print(precursor_mz)



def main():
    test_usi()

if __name__ == "__main__":
    main()