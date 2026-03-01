"""
add_historical.py — NEET PG 2023 & 2024 counselling data import (全ラウンド自動)

使い方:
  python3 add_historical.py            # 全年度・全ラウンドを処理
  python3 add_historical.py --year 2024   # 2024年分のみ
  npm run update-historical

PDFは pdfs/ フォルダに保存される。
ダウンロード済みのPDFは再ダウンロードしない。

2023: Round1, Round2, Stray Round, Special Stray Round
2024: Round1, Round2, Stray Round, Special Stray Round
※ Round3 (Mop-up) は公式PDFが見つからないためスキップ
"""

import json
import re
import os
import sys
import subprocess
import time
import urllib.request
import urllib.error
from collections import defaultdict

# ---------------------------------------------------------------------------
# 依存パッケージの自動インストール
# ---------------------------------------------------------------------------

def ensure(pkg):
    try:
        __import__(pkg)
    except ImportError:
        print(f"  Installing {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

ensure("cffi")
ensure("pdfplumber")
import pdfplumber  # noqa: E402

# ---------------------------------------------------------------------------
# ラウンド設定
# ---------------------------------------------------------------------------

BASE_URL = "https://cdnbbsr.s3waas.gov.in/s3e0f7a4d0ef9b84b83b693bbf3feb8e6e/uploads"

ROUND_CONFIGS = [
    # ——— 2023 ———
    {
        "id":    "2023_R1",
        "label": "2023 Round 1",
        "pdf":   "pdfs/round1_2023.pdf",
        "url":   f"{BASE_URL}/2023/08/2023080855.pdf",
    },
    {
        "id":    "2023_R2",
        "label": "2023 Round 2",
        "pdf":   "pdfs/round2_2023.pdf",
        "url":   f"{BASE_URL}/2023/08/2023083188.pdf",
    },
    {
        "id":    "2023_R4",
        "label": "2023 Stray Vacancy Round",
        "pdf":   "pdfs/stray_2023.pdf",
        "url":   f"{BASE_URL}/2023/10/2023101632-1.pdf",
    },
    {
        "id":    "2023_R5",
        "label": "2023 Special Stray Round",
        "pdf":   "pdfs/specstray_2023.pdf",
        "url":   f"{BASE_URL}/2023/11/2023112564.pdf",
    },
    # ——— 2024 ———
    {
        "id":    "2024_R1",
        "label": "2024 Round 1",
        "pdf":   "pdfs/round1_2024.pdf",
        "url":   f"{BASE_URL}/2024/11/2024112085.pdf",
    },
    {
        "id":    "2024_R2",
        "label": "2024 Round 2",
        "pdf":   "pdfs/round2_2024.pdf",
        "url":   f"{BASE_URL}/2024/12/2024121225.pdf",
    },
    {
        "id":    "2024_R4",
        "label": "2024 Stray Vacancy Round",
        "pdf":   "pdfs/stray_2024.pdf",
        "url":   f"{BASE_URL}/2025/02/2025021923.pdf",
    },
    {
        "id":    "2024_R5",
        "label": "2024 Special Stray Round",
        "pdf":   "pdfs/specstray_2024.pdf",
        "url":   f"{BASE_URL}/2025/03/2025031272.pdf",
    },
]

RANKS_FILE = "src/data/closingRanks.json"

# ---------------------------------------------------------------------------
# 正規化マップ
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

def download_pdf(url, dest_path):
    """PDFをダウンロード（プロキシをバイパス）。既存ファイルはスキップ。"""
    if os.path.exists(dest_path):
        print(f"    Already exists: {dest_path}")
        return True

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    urllib.request.install_opener(opener)

    for attempt in range(1, 5):
        try:
            print(f"    Downloading (attempt {attempt}): {os.path.basename(dest_path)}...")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=90) as resp:
                content_type = resp.info().get_content_type()
                if content_type == "application/pdf":
                    data = resp.read()
                    with open(dest_path, "wb") as f:
                        f.write(data)
                    print(f"    Saved {len(data):,} bytes → {dest_path}")
                    return True
                else:
                    body = resp.read().decode("utf-8", errors="ignore")[:200]
                    print(f"    Unexpected content-type '{content_type}': {body}")
                    return False
        except Exception as e:
            wait = 2 ** attempt
            print(f"    Error: {e}. Retrying in {wait}s...")
            time.sleep(wait)

    print(f"    Download failed after 4 attempts: {dest_path}")
    return False

# ---------------------------------------------------------------------------
# テキスト/状態ユーティリティ
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
# PDFパース
# ---------------------------------------------------------------------------

def parse_page(page):
    """1ページからallotment行を抽出（R1形式8列 / R3形式16列の両方に対応）。"""
    rows = []
    table = page.extract_table()
    if not table:
        return rows

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

            # Layout A: 8列 (Round 1 / 2 形式)
            # SNo(0), Rank(1), Quota(2), Inst(3), Course(4), AllottedCat(5), Cat(6), Remarks(7)
            if ncols >= 7:
                rank_str = clean_text(rec[1])
                if rank_str.isdigit():
                    rank   = int(rank_str)
                    quota  = clean_text(rec[2])
                    inst   = clean_text(rec[3])
                    course = clean_text(rec[4])
                    cat    = clean_text(rec[6]) if ncols > 6 else clean_text(rec[5])
                    if inst and inst not in ("-", ""):
                        rows.append({"rank": rank, "quota": quota,
                                     "inst": inst, "course": course, "cat": cat})
                        continue

            # Layout B: 10+列 (Stray / Mop-up 形式)
            if ncols >= 10:
                rank_str = clean_text(rec[0])
                if rank_str.isdigit():
                    rank    = int(rank_str)
                    remarks = clean_text(rec[-1]).lower()
                    if "fresh allotted" in remarks or "upgraded" in remarks:
                        quota  = clean_text(rec[9])  if ncols > 9  else clean_text(rec[5])
                        inst   = clean_text(rec[10]) if ncols > 10 else clean_text(rec[6])
                        course = clean_text(rec[11]) if ncols > 11 else clean_text(rec[7])
                        cat    = clean_text(rec[12]) if ncols > 12 else clean_text(rec[8])
                    elif any(k in remarks for k in [
                            "no upgradation", "reported", "did not opt", "not allotted"]):
                        quota  = clean_text(rec[1])
                        inst   = clean_text(rec[2])
                        course = clean_text(rec[3])
                        cat    = clean_text(rec[8]) if ncols > 8 else ""
                    else:
                        continue

                    if inst and inst not in ("-", ""):
                        rows.append({"rank": rank, "quota": quota,
                                     "inst": inst, "course": course, "cat": cat})

        except Exception:
            continue

    return rows


def extract_pdf(pdf_path):
    """PDF全ページを解析してallotment行リストを返す。"""
    all_rows = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        print(f"    {total} pages")
        for i, page in enumerate(pdf.pages[2:], start=2):
            rows = parse_page(page)
            all_rows.extend(rows)
            if (i + 1) % 100 == 0:
                print(f"    Processed {i + 1}/{total} pages, {len(all_rows)} rows...")
    return all_rows

# ---------------------------------------------------------------------------
# マージ
# ---------------------------------------------------------------------------

def merge_round(all_rows, round_id, ranks_data):
    """抽出した行を正規化してranks_dataにマージする（既存エントリのranks[round_id]に追加）。"""
    r_map = defaultdict(list)
    for row in all_rows:
        inst = row["inst"]
        inst_name = inst.split(",")[0].strip()
        state = get_state(inst)

        norm_course = COURSE_MAP.get(row["course"], row["course"])
        norm_quota  = normalize_quota(row["quota"], norm_course)
        norm_cat    = CATEGORY_MAP.get(row["cat"], row["cat"])

        key = (inst_name, norm_course, norm_quota, norm_cat, state)
        r_map[key].append(row["rank"])

    for key in r_map:
        r_map[key].sort()

    print(f"    Unique (inst, course, quota, cat) groups: {len(r_map)}")

    # 既存インデックス
    existing_index = {}
    for item in ranks_data:
        key = (item["institute"], item["course"], item["quota"], item["category"], item["state"])
        existing_index[key] = item

    matched     = 0
    new_entries = 0

    for key, rank_list in r_map.items():
        inst_name, course, quota, cat, state = key
        if key in existing_index:
            existing_index[key].setdefault("ranks", {})[round_id] = rank_list
            matched += 1
        else:
            new_entry = {
                "id":          len(ranks_data) + new_entries + 1,
                "institute":   inst_name,
                "state":       state,
                "course":      course,
                "quota":       quota,
                "category":    cat,
                "fee":         "-",
                "stipend":     "-",
                "bondPenalty": "-",
                "bondYears":   "-",
                "ranks":       {round_id: rank_list},
            }
            ranks_data.append(new_entry)
            new_entries += 1

    print(f"    Matched: {matched}, New entries: {new_entries}")
    return ranks_data


def dedup(ranks_data):
    """(institute, course, quota, category, state) をキーに重複を統合する。"""
    merged = {}
    order  = []

    for item in ranks_data:
        key = (item["institute"], item["course"], item["quota"], item["category"], item["state"])
        if key not in merged:
            merged[key] = {k: v for k, v in item.items()}
            merged[key]["ranks"] = dict(item.get("ranks", {}))
            order.append(key)
        else:
            ex = merged[key]
            for rnd, rlist in item.get("ranks", {}).items():
                if rlist:
                    ex["ranks"].setdefault(rnd, [])
                    ex["ranks"][rnd] = sorted(set(ex["ranks"][rnd]) | set(rlist))
            for field in ("fee", "stipend", "bondPenalty", "bondYears"):
                if ex[field] in ("-", "", None) and item.get(field) not in ("-", "", None):
                    ex[field] = item[field]

    result = []
    for i, key in enumerate(order, start=1):
        merged[key]["id"] = i
        result.append(merged[key])
    return result

# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main():
    # コマンドライン引数: --year 2024 など
    filter_year = None
    if "--year" in sys.argv:
        idx = sys.argv.index("--year")
        if idx + 1 < len(sys.argv):
            filter_year = sys.argv[idx + 1]

    configs = ROUND_CONFIGS
    if filter_year:
        configs = [c for c in ROUND_CONFIGS if c["id"].startswith(filter_year)]
        if not configs:
            print(f"No rounds found for year '{filter_year}'")
            sys.exit(1)

    print(f"=== NEET PG Historical Data Import ({', '.join(c['id'] for c in configs)}) ===\n")

    with open(RANKS_FILE) as f:
        ranks_data = json.load(f)
    print(f"Loaded {len(ranks_data)} existing records from {RANKS_FILE}\n")

    failed_rounds = []

    for cfg in configs:
        round_id = cfg["id"]
        label    = cfg["label"]
        pdf_path = cfg["pdf"]
        url      = cfg["url"]

        print(f"--- [{round_id}] {label} ---")

        # 1. ダウンロード
        if not download_pdf(url, pdf_path):
            print(f"  SKIP: download failed. Place PDF manually at: {pdf_path}")
            failed_rounds.append(round_id)
            continue

        # 2. 抽出
        print(f"  Extracting data from {pdf_path}...")
        try:
            all_rows = extract_pdf(pdf_path)
        except Exception as e:
            print(f"  ERROR extracting {pdf_path}: {e}")
            failed_rounds.append(round_id)
            continue

        print(f"  Total rows extracted: {len(all_rows)}")
        if not all_rows:
            print("  No data extracted — check PDF format.")
            failed_rounds.append(round_id)
            continue

        # 3. マージ
        print(f"  Merging into {RANKS_FILE}...")
        ranks_data = merge_round(all_rows, round_id, ranks_data)
        print()

    # 4. 重複排除 & 保存
    before = len(ranks_data)
    ranks_data = dedup(ranks_data)
    after = len(ranks_data)
    print(f"Dedup: {before} → {after} records ({before - after} merged)")

    with open(RANKS_FILE, "w") as f:
        json.dump(ranks_data, f, indent=2)
    print(f"Saved {after} records → {RANKS_FILE}\n")

    # 5. 統計再生成
    stats_script = "generate_stats.py"
    if os.path.exists(stats_script):
        print(f"Running {stats_script}...")
        subprocess.check_call([sys.executable, stats_script])

    print("\n=== Done! ===")

    if failed_rounds:
        print(f"\n⚠  Failed rounds (download blocked): {', '.join(failed_rounds)}")
        print("Place the PDFs manually in the pdfs/ folder and re-run.")


if __name__ == "__main__":
    main()
