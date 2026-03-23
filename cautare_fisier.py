import os
import sys
import argparse
from datetime import datetime

BASE_DIR = r"\\192.168.1.240\BT Redactional"
ANI = [str(an) for an in range(2015, 2027)]


def cauta_in_folder(search_dir, cuvinte_lower):
    files = []
    for root, dirs, filenames in os.walk(search_dir):
        for fname in filenames:
            if fname.lower().endswith(".pdf") and cuvinte_lower in fname.lower():
                files.append(os.path.join(root, fname))
    return files


def find_latest(cuvinte, recursive=False):
    cuvinte_lower = cuvinte.lower()
    files = []

    if recursive:
        print("\nCaut in folderele de ani: " + ", ".join(ANI))
        for an in ANI:
            folder = os.path.join(BASE_DIR, an)
            if os.path.isdir(folder):
                print("  -> " + an + "...", end=" ")
                gasite = cauta_in_folder(folder, cuvinte_lower)
                print(str(len(gasite)) + " gasite")
                files.extend(gasite)
            else:
                print("  -> " + an + " (inexistent, sarit)")
    else:
        for fname in os.listdir(BASE_DIR):
            fpath = os.path.join(BASE_DIR, fname)
            if os.path.isfile(fpath) and fname.lower().endswith(".pdf") and cuvinte_lower in fname.lower():
                files.append(fpath)

    if not files:
        print("\n[INFO] Niciun PDF gasit cu \"" + cuvinte + "\"\n")
        print("Sfat: incearca --recursive pentru a cauta si in subdirectoare.\n")
        return

    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    latest = files[0]

    mtime = os.path.getmtime(latest)
    size  = os.path.getsize(latest)
    date  = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

    print("\n[OK] Cel mai recent PDF (" + str(len(files)) + " gasite):")
    print("  Cale      : " + latest)
    print("  Data      : " + date)
    print("  Dimensiune: " + str(size) + " bytes (" + str(round(size / 1024, 1)) + " KB)\n")

    if len(files) > 1:
        print("  Toate fisierele gasite (descrescator dupa data):")
        for f in files:
            d = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
            print("    " + d + "  " + os.path.basename(f))
        print()


def main():
    parser = argparse.ArgumentParser(description="Gaseste cel mai recent PDF dupa cuvinte cheie.")
    parser.add_argument("cuvinte", help="Cuvinte cheie din numele fisierului")
    parser.add_argument("--recursive", "-r", action="store_true", help="Cauta in folderele 2015-2026")
    args = parser.parse_args()
    find_latest(args.cuvinte, args.recursive)


if __name__ == "__main__":
    main()