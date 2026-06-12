"""
COSMIC-2 spaceWeather Level2 Downloader
========================================
Downloads files from:
  https://data.cosmic.ucar.edu/gnss-ro/cosmic2/provisional/spaceWeather/level2/

Usage examples:
  # Download all files for a specific year/DOY
  python cosmic2_download.py --year 2024 --doy 001

  # Download a range of DOYs
  python cosmic2_download.py --year 2024 --doy 001 --doy-end 010

  # Download an entire year
  python cosmic2_download.py --year 2024

  # Dry-run (list files without downloading)
  python cosmic2_download.py --year 2024 --doy 001 --dry-run

  # Extract .tar.gz after download
  python cosmic2_download.py --year 2024 --doy 001 --extract

  # Custom output directory
  python cosmic2_download.py --year 2024 --doy 001 --outdir ./data
"""

import argparse
import tarfile
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://data.cosmic.ucar.edu/gnss-ro/cosmic2/provisional/spaceWeather/level2"


def list_links(url: str, session: requests.Session) -> list[str]:
    """Return all href links from an Apache-style directory listing."""
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("?") or href.startswith("/") and href != "/":
            continue
        if href == "../":
            continue
        links.append(href)
    return links


def download_file(url: str, dest: Path, session: requests.Session) -> bool:
    """Stream-download a file. Returns True on success."""
    try:
        with session.get(url, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    f.write(chunk)
        return True
    except requests.RequestException as e:
        print(f"  [ERROR] {e}")
        return False


def extract_tar(path: Path, outdir: Path):
    """Extract a .tar.gz file into outdir."""
    print(f"  Extracting {path.name} ...")
    with tarfile.open(path, "r:gz") as tar:
        tar.extractall(path=outdir)


def process_doy(year: int, doy: int, outdir: Path, session: requests.Session,
                dry_run: bool, extract: bool):
    doy_str = f"{doy:03d}"
    url = f"{BASE_URL}/{year}/{doy_str}/"
    print(f"\n[{year}/DOY {doy_str}] Listing {url}")

    try:
        files = list_links(url, session)
    except requests.HTTPError as e:
        print(f"  [SKIP] HTTP {e.response.status_code}")
        return

    if not files:
        print("  No files found.")
        return

    for fname in files:
        file_url = url + fname
        dest = outdir / str(year) / doy_str / fname

        if dest.exists():
            print(f"  [SKIP] {fname} (already exists)")
            continue

        if dry_run:
            print(f"  [DRY-RUN] {file_url}")
            continue

        print(f"  Downloading {fname} ...", end=" ", flush=True)
        ok = download_file(file_url, dest, session)
        if ok:
            print("done")
            if extract and fname.endswith(".tar.gz"):
                extract_tar(dest, dest.parent)
        else:
            print("FAILED")

        time.sleep(0.2)  # be polite to the server


def main():
    parser = argparse.ArgumentParser(description="Download COSMIC-2 spaceWeather level2 data.")
    parser.add_argument("--year", type=int, required=True, help="Year (e.g. 2024)")
    parser.add_argument("--doy", type=int, default=None,
                        help="Day of year to start (1–366). Omit to download whole year.")
    parser.add_argument("--doy-end", type=int, default=None,
                        help="Last DOY (inclusive). Defaults to --doy if not set.")
    parser.add_argument("--outdir", type=Path, default=Path("./cosmic2_data"),
                        help="Root output directory (default: ./cosmic2_data)")
    parser.add_argument("--dry-run", action="store_true",
                        help="List files without downloading")
    parser.add_argument("--extract", action="store_true",
                        help="Extract .tar.gz files after download")
    args = parser.parse_args()

    # Determine DOY range
    if args.doy is None:
        # Fetch available DOYs from the year listing
        session = requests.Session()
        year_url = f"{BASE_URL}/{args.year}/"
        print(f"Fetching year listing: {year_url}")
        doy_links = list_links(year_url, session)
        doys = []
        for link in doy_links:
            stripped = link.rstrip("/")
            if stripped.isdigit():
                doys.append(int(stripped))
        doys.sort()
        if not doys:
            print("No DOY directories found.")
            return
        print(f"Found {len(doys)} DOY directories.")
    else:
        session = requests.Session()
        doy_end = args.doy_end if args.doy_end else args.doy
        doys = list(range(args.doy, doy_end + 1))

    for doy in doys:
        process_doy(args.year, doy, args.outdir, session,
                    dry_run=args.dry_run, extract=args.extract)

    print("\nDone.")


if __name__ == "__main__":
    main()
