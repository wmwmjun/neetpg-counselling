import pdfplumber
import json
import re
import os
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

TARGET_STATES = [
    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
    "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand", "Karnataka",
    "Kerala", "Ladakh", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
]

def clean_text(text):
    if not text: return ""
    return re.sub(' +', ' ', str(text).replace('\n', ' ')).strip()

def get_state(text):
    text_lower = text.lower()
    if any(x in text_lower for x in ["aizawl", "zoram medical", "civil hospital dawrpui"]):
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


def _merge_rows(table):
    """Merge multi-line cells within a table into single records."""
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
    return records


# ---------------------------------------------------------------------------
# Page-level workers (run in separate processes)
# ---------------------------------------------------------------------------

def _process_r1_page(args):
    """
    Round 1 (8 cols):
      SNo(0) | Rank(1) | Quota(2) | Inst(3) | Course(4) | AllottedCat(5) | CandidateCat(6) | Remarks(7)
    Returns rows with allotted_cat and candidate_cat.
    """
    pdf_path, page_num = args
    rows = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            table = pdf.pages[page_num].extract_table()
            if not table:
                return rows
            for rec in _merge_rows(table):
                try:
                    if len(rec) < 7:
                        continue
                    rank_str = clean_text(rec[1])
                    if not rank_str.isdigit():
                        continue
                    inst = clean_text(rec[3])
                    if not inst or inst == "-":
                        continue
                    rows.append({
                        "rank":          int(rank_str),
                        "quota":         clean_text(rec[2]),
                        "inst":          inst,
                        "course":        clean_text(rec[4]),
                        "allotted_cat":  clean_text(rec[5]),   # Allotted Category (seat)
                        "candidate_cat": clean_text(rec[6]) if len(rec) > 6 else clean_text(rec[5]),
                        "needs_lookup":  False,
                    })
                except Exception:
                    continue
    except Exception:
        pass
    return rows


def _process_r2_page(args):
    """
    Round 2 — visually 12 cols on all pages:
      Rank(0) | PrevQuota(1) | PrevInst(2) | PrevCourse(3) | Status(4) |
      NewQuota(5) | NewInst(6) | NewCourse(7) | AllottedCat(8) | CandidateCat(9) | ChoiceNo(10) | Remarks(11)

    NOTE: pdfplumber inserts a spurious blank col[6] on page 1 only (13-col artifact).
    We strip it so all rows normalise to 12 cols before processing.
    """
    pdf_path, page_num = args
    rows = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            table = pdf.pages[page_num].extract_table()
            if not table:
                return rows
            for rec in _merge_rows(table):
                try:
                    # Normalise 13-col pdfplumber artifact (blank col[6] on page 1)
                    if len(rec) == 13 and not clean_text(rec[6]):
                        rec = rec[:6] + rec[7:]
                    if len(rec) < 12:
                        continue
                    rank_str = clean_text(rec[0])
                    if not rank_str.isdigit():
                        continue
                    rank = int(rank_str)
                    remarks = clean_text(rec[11]).lower()

                    if "fresh allotted" in remarks or "upgraded" in remarks:
                        inst = clean_text(rec[6])
                        if not inst or inst == "-":
                            continue
                        rows.append({
                            "rank":          rank,
                            "quota":         clean_text(rec[5]),
                            "inst":          inst,
                            "course":        clean_text(rec[7]),
                            "allotted_cat":  clean_text(rec[8]),
                            "candidate_cat": clean_text(rec[9]) if len(rec) > 9 else clean_text(rec[8]),
                            "needs_lookup":  False,
                        })
                    elif any(x in remarks for x in ["no upgradation", "reported", "did not opt",
                                                     "not allotted", "available", "fill up"]):
                        inst = clean_text(rec[2])
                        if not inst or inst == "-":
                            continue
                        rows.append({
                            "rank":          rank,
                            "quota":         clean_text(rec[1]),
                            "inst":          inst,
                            "course":        clean_text(rec[3]),
                            "allotted_cat":  None,
                            "candidate_cat": None,
                            "needs_lookup":  True,
                        })
                except Exception:
                    continue
    except Exception:
        pass
    return rows


def _process_r3_page(args):
    """
    Round 3 (16 cols):
      Rank(0) | R1Quota(1) | R1Inst(2) | R1Course(3) | R1Status(4) |
      R2Quota(5) | R2Inst(6) | R2Course(7) | R2Status(8) |
      NewQuota(9) | NewInst(10) | NewCourse(11) | AllottedCat(12) | CandidateCat(13) | ChoiceNo(14) | Remarks(15)

    For Fresh/Upgraded: allotted_cat from col 12, candidate_cat from col 13.
    For No-Upgradation/Reported/etc: mark needs_lookup=True (resolved from R2 or R1).
    """
    pdf_path, page_num = args
    rows = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            table = pdf.pages[page_num].extract_table()
            if not table:
                return rows
            for rec in _merge_rows(table):
                try:
                    if len(rec) < 16:
                        continue
                    rank_str = clean_text(rec[0])
                    if not rank_str.isdigit():
                        continue
                    rank = int(rank_str)
                    remarks = clean_text(rec[15]).lower()

                    if "fresh allotted" in remarks or "upgraded" in remarks:
                        inst = clean_text(rec[10])
                        if not inst or inst == "-":
                            continue
                        rows.append({
                            "rank":          rank,
                            "quota":         clean_text(rec[9]),
                            "inst":          inst,
                            "course":        clean_text(rec[11]),
                            "allotted_cat":  clean_text(rec[12]),
                            "candidate_cat": clean_text(rec[13]) if len(rec) > 13 else clean_text(rec[12]),
                            "needs_lookup":  False,
                        })
                    elif any(x in remarks for x in ["no upgradation", "reported", "did not opt",
                                                     "not allotted", "available", "fill up"]):
                        # Use most recent institute: R2 if present, else R1
                        r2_inst = clean_text(rec[6])
                        if r2_inst and r2_inst != "-":
                            inst, quota, course = r2_inst, clean_text(rec[5]), clean_text(rec[7])
                        else:
                            inst, quota, course = clean_text(rec[2]), clean_text(rec[1]), clean_text(rec[3])
                        if not inst or inst == "-":
                            continue
                        rows.append({
                            "rank":          rank,
                            "quota":         quota,
                            "inst":          inst,
                            "course":        course,
                            "allotted_cat":  None,
                            "candidate_cat": None,
                            "needs_lookup":  True,
                        })
                except Exception:
                    continue
    except Exception:
        pass
    return rows


# ---------------------------------------------------------------------------
# Main extraction logic
# ---------------------------------------------------------------------------

def extract_round(pdf_path, page_worker, start_page, label):
    """Parallel page extraction for one round."""
    if not os.path.exists(pdf_path):
        print(f"  {pdf_path} not found, skipping.")
        return []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
    args = [(pdf_path, i) for i in range(start_page, total)]
    all_rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for page_rows in tqdm(ex.map(page_worker, args), total=len(args), desc=label):
            all_rows.extend(page_rows)
    return all_rows


def resolve_lookups(rows, rank_lookup):
    """Fill in allotted_cat/candidate_cat for needs_lookup rows from a rank lookup table."""
    resolved = []
    for row in rows:
        if row["needs_lookup"]:
            entry = rank_lookup.get(row["rank"])
            if entry:
                row = dict(row)
                row["allotted_cat"]  = entry["allotted_cat"]
                row["candidate_cat"] = entry["candidate_cat"]
                # Also update quota/inst/course from looked-up entry for accuracy
                row["quota"]  = entry["quota"]
                row["inst"]   = entry["inst"]
                row["course"] = entry["course"]
            else:
                # Cannot resolve — skip row
                continue
        if row.get("allotted_cat"):
            resolved.append(row)
    return resolved


def build_rank_lookup(rows):
    """rank → most recent allotment row (later rows overwrite earlier for same rank)."""
    lookup = {}
    for row in rows:
        if not row.get("needs_lookup") and row.get("allotted_cat"):
            lookup[row["rank"]] = row
    return lookup


def main():
    # ── Phase 1: Parallel extraction of all PDFs ──────────────────────────
    print("Extracting Round 1 (parallel)...")
    r1_raw = extract_round("round1_2025.pdf", _process_r1_page, 1, "R1")
    print(f"  R1 raw rows: {len(r1_raw)}")

    rank_to_r1 = build_rank_lookup(r1_raw)

    print("Extracting Round 2 (parallel)...")
    r2_raw = extract_round("round2_2025.pdf", _process_r2_page, 1, "R2")
    print(f"  R2 raw rows: {len(r2_raw)}")

    r2_rows = resolve_lookups(r2_raw, rank_to_r1)
    print(f"  R2 resolved rows: {len(r2_rows)}")

    # For R3 lookup: upgraded R2 entries take priority over R1
    rank_to_r2 = build_rank_lookup(r2_rows)
    rank_to_r2_or_r1 = {**rank_to_r1, **rank_to_r2}  # R2 overwrites R1

    print("Extracting Round 3 (parallel)...")
    r3_raw = extract_round("round3_2025.pdf", _process_r3_page, 3, "R3")
    print(f"  R3 raw rows: {len(r3_raw)}")

    r3_rows = resolve_lookups(r3_raw, rank_to_r2_or_r1)
    print(f"  R3 resolved rows: {len(r3_rows)}")

    total = len(r1_raw) + len(r2_rows) + len(r3_rows)
    print(f"\nTotal rows: {total}")

    # ── Phase 2: Aggregate by (inst_name, course, quota, allotted_cat, state) ──
    from collections import defaultdict

    groups = defaultdict(lambda: {"2025_R1": [], "2025_R2": [], "2025_R3": []})

    for rnd, rows in [("2025_R1", r1_raw), ("2025_R2", r2_rows), ("2025_R3", r3_rows)]:
        for row in rows:
            inst_name = row["inst"].split(",")[0].strip()
            state = get_state(row["inst"])
            key = (inst_name, row["course"], row["quota"], row["allotted_cat"], state)
            groups[key][rnd].append([row["rank"], row["candidate_cat"]])

    # Sort each round's ranks
    for key, rounds in groups.items():
        for rnd in rounds:
            rounds[rnd].sort(key=lambda x: x[0])

    results = []
    for i, ((inst, course, quota, allotted_cat, state), ranks) in enumerate(groups.items(), start=1):
        results.append({
            "id": i,
            "institute": inst,
            "state": state,
            "course": course,
            "quota": quota,
            "category": allotted_cat,
            "fee": "-",
            "stipend": "-",
            "bondPenalty": "-",
            "bondYears": "-",
            "ranks": ranks
        })

    with open("src/data/closingRanks.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(results)} entries to src/data/closingRanks.json")


if __name__ == "__main__":
    main()
