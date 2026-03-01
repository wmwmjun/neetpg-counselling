"""
Add Round 4 (Stray Vacancy Round) data to closingRanks.json.

Usage:
  1. Download the NEET PG 2025 Stray Vacancy Round allotment PDF from:
     https://cdnbbsr.s3waas.gov.in/s3e0f7a4d0ef9b84b83b693bbf3feb8e6e/uploads/2026/02/20260223177387794.pdf
  2. Save it as: round4_2025.pdf  (in this directory)
  3. Run: python3 add_round4.py
"""

import json
import re
import os
from collections import defaultdict

try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    import subprocess
    subprocess.check_call(["pip3", "install", "pdfplumber"])
    import pdfplumber

ROUND_ID = "2025_R4"
PDF_PATH = "round4_2025.pdf"
RANKS_FILE = "src/data/closingRanks.json"
NAME_TO_CODE_FILE = "name_to_code.json"

TARGET_STATES = [
    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
    "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand", "Karnataka",
    "Kerala", "Ladakh", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
]


def clean_text(text):
    if not text:
        return ""
    return re.sub(r' +', ' ', str(text).replace('\n', ' ')).strip()


def get_state(text):
    text_lower = text.lower()
    if any(x in text_lower for x in ["aizawl", "zoram medical"]):
        return "Mizoram"
    if any(x in text_lower for x in ["gangtok", "sikkim"]):
        return "Sikkim"
    if any(x in text_lower for x in ["imphal", "manipur"]):
        return "Manipur"
    if any(x in text_lower for x in ["shillong", "meghalaya"]):
        return "Meghalaya"
    if any(x in text_lower for x in ["agartala", "tripura"]):
        return "Tripura"
    if any(x in text_lower for x in ["kohima", "dimapur", "nagaland"]):
        return "Nagaland"
    if any(x in text_lower for x in ["itanagar", "arunachal"]):
        return "Arunachal Pradesh"
    if any(x in text_lower for x in ["puducherry", "pondicherry", "jipmer"]):
        return "Puducherry"
    for state in TARGET_STATES:
        if state.lower() in text_lower:
            return state
    if "dadra" in text_lower or "daman" in text_lower:
        return "Dadra and Nagar Haveli and Daman and Diu"
    if "andaman" in text_lower or "nicobar" in text_lower:
        return "Andaman and Nicobar Islands"
    return "Others"


def parse_page(page):
    """Extract allotment rows from a single PDF page."""
    rows = []
    table = page.extract_table()
    if not table:
        return rows

    # Merge wrapped rows
    records = []
    current = None
    for row in table:
        if not row:
            continue
        first = str(row[0]).strip() if row[0] else ""
        if first.isdigit():
            if current:
                records.append(current)
            current = [str(c) if c else "" for c in row]
        elif current:
            for i in range(min(len(row), len(current))):
                if row[i]:
                    current[i] += " " + str(row[i])
    if current:
        records.append(current)

    for rec in records:
        try:
            # Probe column layout from number of columns
            ncols = len(rec)

            # --- Layout A: Stray Vacancy simple (similar to R1) ---
            # SNo(0), Rank(1), Quota(2), Inst(3), Course(4), AllottedCat(5), Cat(6), Remarks(7)
            if ncols >= 7:
                rank_str = clean_text(rec[1])
                if rank_str.isdigit():
                    rank = int(rank_str)
                    quota = clean_text(rec[2])
                    inst = clean_text(rec[3])
                    course = clean_text(rec[4])
                    cat = clean_text(rec[6]) if ncols > 6 else clean_text(rec[5])
                    if inst and inst not in ("-", ""):
                        rows.append({
                            "rank": rank, "quota": quota,
                            "inst": inst, "course": course, "cat": cat
                        })
                        continue

            # --- Layout B: Stray Vacancy complex (similar to R3) ---
            # Rank(0), Quota(1), Inst(2), Course(3), Status(4), PrevQuota(5), PrevInst(6),
            # PrevCourse(7), PrevCat(8), NewQuota(9), NewInst(10), NewCourse(11), NewCat(12), ..., Remarks
            if ncols >= 10:
                rank_str = clean_text(rec[0])
                if rank_str.isdigit():
                    rank = int(rank_str)
                    remarks = clean_text(rec[-1]).lower()
                    if "fresh allotted" in remarks or "upgraded" in remarks:
                        quota = clean_text(rec[9]) if ncols > 9 else clean_text(rec[5])
                        inst = clean_text(rec[10]) if ncols > 10 else clean_text(rec[6])
                        course = clean_text(rec[11]) if ncols > 11 else clean_text(rec[7])
                        cat = clean_text(rec[12]) if ncols > 12 else clean_text(rec[8])
                    elif any(k in remarks for k in ["no upgradation", "reported", "did not opt", "not allotted"]):
                        quota = clean_text(rec[1])
                        inst = clean_text(rec[2])
                        course = clean_text(rec[3])
                        cat = clean_text(rec[8]) if ncols > 8 else ""
                    else:
                        continue

                    if inst and inst not in ("-", ""):
                        rows.append({
                            "rank": rank, "quota": quota,
                            "inst": inst, "course": course, "cat": cat
                        })

        except Exception:
            continue

    return rows


def main():
    if not os.path.exists(PDF_PATH):
        print(f"ERROR: {PDF_PATH} not found.")
        print("Download from:")
        print("  https://cdnbbsr.s3waas.gov.in/s3e0f7a4d0ef9b84b83b693bbf3feb8e6e/uploads/2026/02/20260223177387794.pdf")
        print(f"and save as: {PDF_PATH}")
        return

    print(f"Reading {PDF_PATH}...")
    all_rows = []
    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        print(f"  {total} pages found")
        # Skip first few pages (usually cover/instructions); start at page index 2
        for i, page in enumerate(pdf.pages[2:], start=2):
            rows = parse_page(page)
            all_rows.extend(rows)
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{total} pages, {len(all_rows)} rows so far...")

    print(f"Total R4 allotments extracted: {len(all_rows)}")
    if not all_rows:
        print("No data extracted. The PDF might have a different column layout.")
        print("Check inspect_page.py to examine the page structure.")
        return

    # Build lookup: (inst_name, course, quota, cat, state) → [ranks]
    r4_map = defaultdict(list)
    for row in all_rows:
        inst = row["inst"]
        inst_name = inst.split(',')[0].strip()
        state = get_state(inst)
        key = (inst_name, row["course"], row["quota"], row["cat"], state)
        r4_map[key].append(row["rank"])

    # Sort ranks per group
    for key in r4_map:
        r4_map[key].sort()

    print(f"Unique (inst, course, quota, cat) groups: {len(r4_map)}")

    # Merge into closingRanks.json
    with open(RANKS_FILE) as f:
        ranks_data = json.load(f)

    matched = 0
    new_entries = 0

    # Build existing key index
    existing_index = {}
    for item in ranks_data:
        key = (item["institute"], item["course"], item["quota"], item["category"], item["state"])
        existing_index[key] = item

    for key, rank_list in r4_map.items():
        inst_name, course, quota, cat, state = key
        if key in existing_index:
            existing_index[key].setdefault("ranks", {})[ROUND_ID] = rank_list
            matched += 1
        else:
            # New entry not seen in R1-R3
            new_entry = {
                "id": len(ranks_data) + new_entries + 1,
                "institute": inst_name,
                "state": state,
                "course": course,
                "quota": quota,
                "category": cat,
                "fee": "-",
                "stipend": "-",
                "bondPenalty": "-",
                "bondYears": "-",
                "ranks": {
                    "2025_R1": [], "2025_R2": [], "2025_R3": [],
                    ROUND_ID: rank_list
                }
            }
            ranks_data.append(new_entry)
            new_entries += 1

    print(f"Matched to existing entries: {matched}")
    print(f"New entries added: {new_entries}")

    with open(RANKS_FILE, 'w') as f:
        json.dump(ranks_data, f, indent=2)
    print(f"Saved {len(ranks_data)} total records to {RANKS_FILE}")
    print("\nNext: run 'python3 generate_stats.py' to update branchStats.json and instituteStats.json")


if __name__ == "__main__":
    main()
