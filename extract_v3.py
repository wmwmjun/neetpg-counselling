import pdfplumber
import pandas as pd
import json
import re
from tqdm import tqdm
import os
from concurrent.futures import ProcessPoolExecutor

# User-provided comprehensive state list
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
    return re.sub(' +', ' ', text.replace('\n', ' ')).strip()

def get_state_from_address(inst_text):
    text_lower = inst_text.lower()
    if "dadra" in text_lower or "daman" in text_lower:
        return "Dadra and Nagar Haveli and Daman and Diu"
    if "andaman" in text_lower or "nicobar" in text_lower:
        return "Andaman and Nicobar Islands"
    if "jammu" in text_lower or "kashmir" in text_lower:
        return "Jammu and Kashmir"
    for state in TARGET_STATES:
        if state.lower() in text_lower:
            return state
    return "Others"

def process_page_v3(args):
    pdf_path, page_num, round_id = args
    rows = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num]
            table = page.extract_table()
            if not table: return []
            
            records = []
            current_record = None
            for row in table:
                if not row: continue
                # New record starts with a digit in the first column
                if row[0] and str(row[0]).strip().isdigit():
                    if current_record: records.append(current_record)
                    current_record = [str(c) if c else "" for c in row]
                elif current_record:
                    # Merge wrapping rows
                    for i in range(min(len(row), len(current_record))):
                        if row[i]: current_record[i] += " " + str(row[i])
            if current_record: records.append(current_record)
            
            for rec in records:
                try:
                    if round_id == "2025_R1":
                        # R1: S.No | Rank | Quota | Inst | Course | Allotted Cat | Cat | Remarks
                        rank = int(clean_text(rec[1]))
                        quota = clean_text(rec[2])
                        inst_raw = clean_text(rec[3])
                        course_raw = clean_text(rec[4])
                        allotted_category = clean_text(rec[5])
                        state = get_state_from_address(inst_raw)
                        rows.append({
                            "rank": rank, "quota": quota, "institute": inst_raw.split(',')[0].strip(),
                            "course": clean_text(course_raw), "category": allotted_category, "state": state, "round": round_id
                        })
                    else:
                        # R2/R3 [12 columns]: 
                        # 0: SNo, 1: Prev Quota, 2: Prev Inst, 3: Prev Course, 4: Status, 
                        # 5: New Quota, 6: New Inst, 7: New Course, 8: Allotted Cat, 9: Candidate Cat, 10: Rank, 11: Remarks
                        rank_str = clean_text(rec[10])
                        if not rank_str.isdigit(): continue
                        rank = int(rank_str)
                        
                        remarks = clean_text(rec[11])
                        # If Fresh Allotted or Upgraded, take columns 5-8
                        if "Fresh Allotted" in remarks or "Upgraded" in remarks:
                            quota = clean_text(rec[5])
                            inst_raw = clean_text(rec[6])
                            course_raw = clean_text(rec[7])
                            allotted_category = clean_text(rec[8])
                        # If No Upgradation or Reported, take columns 1-3 if they exist
                        elif "No Upgradation" in remarks or "Reported" in remarks or "Did not opt" in remarks:
                            quota = clean_text(rec[1])
                            inst_raw = clean_text(rec[2])
                            course_raw = clean_text(rec[3])
                            allotted_category = clean_text(rec[8]) # Usually cat still in 8 or not shown
                            if not quota or quota == "-": continue # Not an active allotment
                        else:
                            continue
                            
                        if not inst_raw or inst_raw == "-": continue
                        
                        state = get_state_from_address(inst_raw)
                        rows.append({
                            "rank": rank, "quota": quota, "institute": inst_raw.split(',')[0].strip(),
                            "course": clean_text(course_raw), "category": allotted_category, "state": state, "round": round_id
                        })
                except: continue
    except: pass
    return rows

def main():
    files = {"2025_R1": "round1_2025.pdf", "2025_R2": "round2_2025.pdf", "2025_R3": "round3_2025.pdf"}
    all_allotted = []
    for round_id, pdf_path in files.items():
        if not os.path.exists(pdf_path): continue
        print(f"Processing {round_id}...")
        with pdfplumber.open(pdf_path) as pdf:
            start_page = 2 if round_id == "2025_R1" else 5
            args_list = [(pdf_path, i, round_id) for i in range(start_page, len(pdf.pages))]
            with ProcessPoolExecutor(max_workers=8) as executor:
                for page_rows in tqdm(executor.map(process_page_v3, args_list), total=len(args_list)):
                    all_allotted.extend(page_rows)

    df = pd.DataFrame(all_allotted)
    print(f"Extracted {len(df)} total entries.")
    
    # Mizoram check
    miz = df[df['state'] == 'Mizoram']
    print(f"Found {len(miz)} entries for Mizoram.")
    
    # Aggregation
    registry = df[['institute', 'course', 'quota', 'category', 'state']].drop_duplicates()
    results = []
    for _, seat in tqdm(registry.iterrows(), total=len(registry), desc="Aggregating"):
        mask = (df['institute'] == seat['institute']) & \
               (df['course'] == seat['course']) & \
               (df['quota'] == seat['quota']) & \
               (df['category'] == seat['category'])
        seat_data = df[mask]
        ranks = {"2025_R1": None, "2025_R2": None, "2025_R3": None}
        for rnd in ranks.keys():
            rnd_data = seat_data[seat_data['round'] == rnd]
            if not rnd_data.empty:
                ranks[rnd] = int(rnd_data['rank'].max())
        
        results.append({
            "id": len(results) + 1, "institute": seat['institute'], "state": seat['state'],
            "course": seat['course'], "quota": seat['quota'], "category": seat['category'],
            "fee": "-", "stipend": "-", "bondPenalty": "-", "bondYears": "-", "ranks": ranks
        })

    with open("src/data/closingRanks.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} aggregated entries.")

if __name__ == "__main__":
    main()
