"""
add_round4.py — 完全自動: ダウンロード → 抽出 → 正規化 → マージ → 統計更新
使い方: python3 add_round4.py   または   npm run update-r4
"""

import json
import re
import os
import sys
import subprocess
from collections import defaultdict

# ---------------------------------------------------------------------------
# 依存パッケージの自動インストール
# ---------------------------------------------------------------------------

def ensure(pkg):
    try:
        __import__(pkg)
    except ImportError:
        print(f"Installing {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

ensure("cffi")
ensure("pdfplumber")

import pdfplumber  # noqa: E402

# ---------------------------------------------------------------------------
# 設定
# ---------------------------------------------------------------------------

ROUND_ID  = "2025_R4"
PDF_URL   = (
    "https://cdnbbsr.s3waas.gov.in"
    "/s3e0f7a4d0ef9b84b83b693bbf3feb8e6e"
    "/uploads/2026/02/20260223177387794.pdf"
)
PDF_PATH      = "round4_2025.pdf"
RANKS_FILE    = "src/data/closingRanks.json"

# ---------------------------------------------------------------------------
# 正規化マップ (normalize_data.py より import)
# ---------------------------------------------------------------------------

from normalize_data import COURSE_MAP, QUOTA_MAP_SIMPLE, CATEGORY_MAP, normalize_quota  # noqa: E402

TARGET_STATES = [
    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
    "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand", "Karnataka",
    "Kerala", "Ladakh", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"
]

# ---------------------------------------------------------------------------
# ダウンロード
# ---------------------------------------------------------------------------

def download_pdf():
    """PDF を直接ダウンロード (プロキシをバイパス)。既存ファイルはスキップ。"""
    if os.path.exists(PDF_PATH):
        print(f"  {PDF_PATH} already exists, skipping download.")
        return True

    import urllib.request
    import urllib.error
    import time

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # ProxyHandler({}) で環境変数プロキシを無視して直接接続
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    urllib.request.install_opener(opener)

    for attempt in range(1, 5):
        try:
            print(f"  Downloading PDF (attempt {attempt})...")
            req = urllib.request.Request(PDF_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                content_type = resp.info().get_content_type()
                if content_type == "application/pdf":
                    data = resp.read()
                    with open(PDF_PATH, "wb") as f:
                        f.write(data)
                    print(f"  Saved {len(data):,} bytes → {PDF_PATH}")
                    return True
                else:
                    body = resp.read().decode("utf-8", errors="ignore")[:300]
                    print(f"  Unexpected content-type '{content_type}': {body}")
                    return False
        except Exception as e:
            wait = 2 ** attempt
            print(f"  Download failed ({e}), retrying in {wait}s...")
            time.sleep(wait)

    print("  All download attempts failed.")
    return False

# ---------------------------------------------------------------------------
# テキストユーティリティ
# ---------------------------------------------------------------------------

def clean_text(text):
    if not text:
        return ""
    return re.sub(r" +", " ", str(text).replace("\n", " ")).strip()


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

# ---------------------------------------------------------------------------
# PDF パース
# ---------------------------------------------------------------------------

def parse_page(page):
    """1ページ分のテーブルから allotment 行を抽出する。"""
    rows = []
    table = page.extract_table()
    if not table:
        return rows

    # 複数行に分割されたセルを結合
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
            ncols = len(rec)

            # --- Layout A: Simple (R1 / Stray Vacancy 形式) 8 列 ---
            # SNo(0), Rank(1), Quota(2), Inst(3), Course(4), AllottedCat(5), CandidateCat(6), Remarks(7)
            if ncols >= 7:
                rank_str = clean_text(rec[1])
                if rank_str.isdigit():
                    rank  = int(rank_str)
                    quota = clean_text(rec[2])
                    inst  = clean_text(rec[3])
                    course = clean_text(rec[4])
                    # Col 5 = Allotted Category (seat category), Col 6 = Candidate Category
                    allotted_cat  = clean_text(rec[5])
                    candidate_cat = clean_text(rec[6]) if ncols > 6 else allotted_cat
                    if inst and inst not in ("-", ""):
                        rows.append({"rank": rank, "quota": quota,
                                     "inst": inst, "course": course,
                                     "cat": allotted_cat, "candidate_cat": candidate_cat})
                        continue

            # --- Layout B: Complex (R2 形式 12列 / R3 形式 16列) ---
            if ncols >= 10:
                rank_str = clean_text(rec[0])
                if rank_str.isdigit():
                    rank    = int(rank_str)
                    remarks = clean_text(rec[-1]).lower()
                    if "fresh allotted" in remarks or "upgraded" in remarks:
                        if ncols >= 16:
                            # R3 format (16 cols): NewQuota(9), NewInst(10), NewCourse(11), AllottedCat(12), CandidateCat(13)
                            quota  = clean_text(rec[9])
                            inst   = clean_text(rec[10])
                            course = clean_text(rec[11])
                            allotted_cat  = clean_text(rec[12])
                            candidate_cat = clean_text(rec[13]) if ncols > 13 else allotted_cat
                        else:
                            # R2 format (12 cols): NewQuota(5), NewInst(6), NewCourse(7), AllottedCat(8), CandidateCat(9)
                            quota  = clean_text(rec[5])
                            inst   = clean_text(rec[6])
                            course = clean_text(rec[7])
                            allotted_cat  = clean_text(rec[8])
                            candidate_cat = clean_text(rec[9]) if ncols > 9 else allotted_cat
                    elif any(k in remarks for k in [
                            "no upgradation", "reported", "did not opt", "not allotted"]):
                        quota  = clean_text(rec[1])
                        inst   = clean_text(rec[2])
                        course = clean_text(rec[3])
                        # Category blank in PDF — keep as "-", will be resolved by lookup
                        allotted_cat  = "-"
                        candidate_cat = "-"
                    else:
                        continue

                    if inst and inst not in ("-", ""):
                        rows.append({"rank": rank, "quota": quota,
                                     "inst": inst, "course": course,
                                     "cat": allotted_cat, "candidate_cat": candidate_cat})

        except Exception:
            continue

    return rows


def extract_r4():
    """PDF 全ページを解析して allotment 行リストを返す。"""
    all_rows = []
    with pdfplumber.open(PDF_PATH) as pdf:
        total = len(pdf.pages)
        print(f"  {total} pages found")
        # 最初の数ページ (表紙・説明) をスキップ
        for i, page in enumerate(pdf.pages[2:], start=2):
            rows = parse_page(page)
            all_rows.extend(rows)
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{total} pages, {len(all_rows)} rows so far...")
    return all_rows

# ---------------------------------------------------------------------------
# マージ
# ---------------------------------------------------------------------------

def merge_into_json(all_rows):
    """抽出した行を正規化して closingRanks.json にマージする。"""

    # (inst_name, course, quota, allotted_cat, state) → [[rank, candidate_cat], ...]
    r4_map = defaultdict(list)
    for row in all_rows:
        inst = row["inst"]
        inst_name = inst.split(",")[0].strip()
        state = get_state(inst)

        # 正規化
        norm_course = COURSE_MAP.get(row["course"], row["course"])
        norm_quota  = normalize_quota(row["quota"], norm_course)
        norm_cat    = CATEGORY_MAP.get(row["cat"], row["cat"])  # allotted category
        norm_ccat   = CATEGORY_MAP.get(row.get("candidate_cat", row["cat"]), row.get("candidate_cat", row["cat"]))

        key = (inst_name, norm_course, norm_quota, norm_cat, state)
        r4_map[key].append([row["rank"], norm_ccat])

    for key in r4_map:
        r4_map[key].sort(key=lambda x: x[0])

    print(f"  Unique (inst, course, quota, cat) groups: {len(r4_map)}")

    with open(RANKS_FILE) as f:
        ranks_data = json.load(f)

    # 既存レコードのインデックス構築
    existing_index = {}
    for item in ranks_data:
        key = (item["institute"], item["course"], item["quota"], item["category"], item["state"])
        existing_index[key] = item

    matched     = 0
    new_entries = 0

    for key, rank_list in r4_map.items():
        inst_name, course, quota, cat, state = key
        if key in existing_index:
            existing_index[key].setdefault("ranks", {})[ROUND_ID] = rank_list
            matched += 1
        else:
            new_entry = {
                "id": len(ranks_data) + new_entries + 1,
                "institute":   inst_name,
                "state":       state,
                "course":      course,
                "quota":       quota,
                "category":    cat,
                "fee":         "-",
                "stipend":     "-",
                "bondPenalty": "-",
                "bondYears":   "-",
                "ranks": {
                    "2025_R1": [], "2025_R2": [], "2025_R3": [],
                    ROUND_ID: rank_list
                }
            }
            ranks_data.append(new_entry)
            new_entries += 1

    print(f"  Matched to existing entries: {matched}")
    print(f"  New entries added: {new_entries}")

    with open(RANKS_FILE, "w") as f:
        json.dump(ranks_data, f, indent=2)
    print(f"  Saved {len(ranks_data)} total records → {RANKS_FILE}")

# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main():
    print("=== NEET PG 2025 Round 4 Auto-Import ===\n")

    # 1. ダウンロード
    print("[1/3] Downloading PDF...")
    if not download_pdf():
        print(
            "\nDownload failed. Please download manually from:\n"
            f"  {PDF_URL}\n"
            f"and save as: {PDF_PATH}\n"
            "Then re-run this script."
        )
        sys.exit(1)

    # 2. 抽出
    print(f"\n[2/3] Extracting allotment data from {PDF_PATH}...")
    all_rows = extract_r4()
    print(f"  Total R4 allotments extracted: {len(all_rows)}")

    if not all_rows:
        print("  No data extracted. The PDF may use a different column layout.")
        sys.exit(1)

    # 3. マージ & 統計更新
    print(f"\n[3/3] Merging into {RANKS_FILE} and updating stats...")
    merge_into_json(all_rows)

    # generate_stats.py を実行して branchStats / instituteStats を再生成
    stats_script = "generate_stats.py"
    if os.path.exists(stats_script):
        print(f"\n  Running {stats_script}...")
        subprocess.check_call([sys.executable, stats_script])
    else:
        print(f"\n  ('{stats_script}' not found — skipping stats regeneration)")

    print("\n=== Done! Round 4 data imported successfully. ===")


if __name__ == "__main__":
    main()
