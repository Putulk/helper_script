"""
open_media_urls.py
------------------
Opens MediaUrl from CSV in Chrome, skipping rows where
MakeName + ModelName combination has already been seen.

Usage:
    python open_media_urls.py
"""

import csv
import time
import subprocess
import platform
import os
import sys

# ─── CONFIG ───────────────────────────────────────────────────────────────────
CSV_FILE        = "/Users/gupta/Downloads/4W_RENEWAL_EXPIRY_whatsapp_T16_2026-03-05-1_final 2.csv"
MEDIA_COL       = "MediaUrl"
MAKE_COL        = "MakeName"
MODEL_COL       = "ModelName"
DELAY           = 0.5   # seconds between opening each tab
SKIP_EMPTY      = True  # skip rows with empty MediaUrl
# ──────────────────────────────────────────────────────────────────────────────


def get_chrome_command() -> list:
    system = platform.system()
    if system == "Windows":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        for p in candidates:
            if os.path.exists(p):
                return [p]
        return ["chrome"]
    elif system == "Darwin":  # macOS
        return ["open", "-a", "Google Chrome"]
    else:  # Linux
        for cmd in ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]:
            if subprocess.call(["which", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                return [cmd]
        return ["google-chrome"]


def get_col(fieldnames, col_name):
    """Case-insensitive column lookup."""
    col_map = {h.strip().lower(): h for h in fieldnames}
    matched = col_map.get(col_name.strip().lower())
    if not matched:
        print(f"❌ Column '{col_name}' not found in CSV.")
        print(f"   Available columns: {list(fieldnames)}")
        sys.exit(1)
    return matched


def read_unique_urls(csv_file: str) -> list:
    if not os.path.isfile(csv_file):
        print(f"❌ File not found:\n   {csv_file}")
        sys.exit(1)

    results = []          # list of dicts: {url, make, model}
    seen_combos = set()   # tracks (make, model) pairs already added
    skipped_dup = 0
    skipped_empty = 0

    with open(csv_file, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            print("❌ CSV appears to be empty.")
            sys.exit(1)

        media_col = get_col(reader.fieldnames, MEDIA_COL)
        make_col  = get_col(reader.fieldnames, MAKE_COL)
        model_col = get_col(reader.fieldnames, MODEL_COL)

        for row in reader:
            url   = (row[media_col]  or "").strip()
            make  = (row[make_col]   or "").strip()
            model = (row[model_col]  or "").strip()

            if SKIP_EMPTY and not url:
                skipped_empty += 1
                continue

            combo = (make.lower(), model.lower())

            if combo in seen_combos:
                skipped_dup += 1
                print(f"  ⏭️  Skipped duplicate  [{make} + {model}]  →  {url}")
                continue

            seen_combos.add(combo)
            results.append({"url": url, "make": make, "model": model})

    print(f"\n  📊 Total rows processed : {len(results) + skipped_dup + skipped_empty}")
    print(f"  ✅ Unique Make+Model URLs: {len(results)}")
    print(f"  ⏭️  Skipped (duplicate)  : {skipped_dup}")
    print(f"  ⚪ Skipped (empty URL)   : {skipped_empty}\n")

    return results


def open_in_chrome(records: list):
    chrome = get_chrome_command()
    print(f"🌐 Chrome : {' '.join(chrome)}")
    print(f"🔗 Opening {len(records)} unique URL(s)...\n")

    for i, rec in enumerate(records, 1):
        url = rec["url"]
        try:
            subprocess.Popen(chrome + [url])
            print(f"  [{i}/{len(records)}] ✅ [{rec['make']} {rec['model']}]  →  {url}")
            if DELAY > 0 and i < len(records):
                time.sleep(DELAY)
        except Exception as e:
            print(f"  [{i}/{len(records)}] ❌ Failed — {e}")

    print("\n✅ Done!")


if __name__ == "__main__":
    print(f"📄 Reading: {CSV_FILE}\n")
    records = read_unique_urls(CSV_FILE)

    if not records:
        print("⚠️  No URLs to open.")
        sys.exit(0)

    open_in_chrome(records)