import pdfplumber
import pandas as pd
import json
import re
from tqdm import tqdm
import os
from concurrent.futures import ProcessPoolExecutor

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

def get_state(text):
    text_lower = text.lower()
    
    # Direct mapping for known institutes that often lack state name
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
    
    # Special cases
    if "dadra" in text_lower or "daman" in text_lower: return "Dadra and Nagar Haveli and Daman and Diu"
    if "andaman" in text_lower or "nicobar" in text_lower: return "Andaman and Nicobar Islands"
    
    return "Others"

def process_page_final(args):
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
                if row[0] and str(row[0]).strip().isdigit():
                    if current_record: records.append(current_record)
                    current_record = [str(c) if c else "" for c in row]
                elif current_record:
                    # Merge wrapping lines
                    for i in range(min(len(row), len(current_record))):
                        if row[i]: current_record[i] += " " + str(row[i])
            if current_record: records.append(current_record)
            
            for rec in records:
                try:
                    # Mapping based on Round ID
                    if round_id == "2025_R1":
                        # R1 usually 8 cols: SNo, Rank, Quota, Inst, Course, AllottedCat, Cat, Remarks
                        if len(rec) >= 8:
                            rank = int(clean_text(rec[1]))
                            quota = clean_text(rec[2])
                            inst = clean_text(rec[3])
                            course = clean_text(rec[4])
                            cat = clean_text(rec[5])
                            rows.append({"rank": rank, "quota": quota, "inst": inst, "course": course, "cat": cat, "round": round_id})
                    else:
                        # R2/R3/R4 are 12 cols
                        remarks = clean_text(rec[11]).lower()
                        rank_str = clean_text(rec[10])
                        if not rank_str.isdigit(): continue
                        rank = int(rank_str)

                        # Decision: Which columns have the LATEST allotment?
                        if "fresh allotted" in remarks or "upgraded" in remarks:
                            # Use cols 5, 6, 7, 8
                            quota, inst, course, cat = clean_text(rec[5]), clean_text(rec[6]), clean_text(rec[7]), clean_text(rec[8])
                        elif any(x in remarks for x in ["no upgradation", "reported", "did not opt", "not allotted", "available"]):
                            # Use cols 1, 2, 3, 8 (column 8 is usually the category)
                            quota, inst, course, cat = clean_text(rec[1]), clean_text(rec[2]), clean_text(rec[3]), clean_text(rec[8])
                        else:
                            continue # Skip empty/not joined if no prior seat

                        if not inst or inst == "-": continue
                        rows.append({"rank": rank, "quota": quota, "inst": inst, "course": course, "cat": cat, "round": round_id})
                except: continue
    except: pass
    return rows

def main():
    rounds = {"2025_R1": "round1_2025.pdf", "2025_R2": "round2_2025.pdf", "2025_R3": "round3_2025.pdf"}
    all_data = []
    for rnd, path in rounds.items():
        if not os.path.exists(path): continue
        print(f"Extracting {rnd}...")
        with pdfplumber.open(path) as pdf:
            start = 2 if rnd == "2025_R1" else 5
            args = [(path, i, rnd) for i in range(start, len(pdf.pages))]
            with ProcessPoolExecutor(max_workers=8) as ex:
                for p_rows in tqdm(ex.map(process_page_final, args), total=len(args)):
                    all_data.extend(p_rows)

    df = pd.DataFrame(all_data)
    print(f"Total rows extracted: {len(df)}")
    
    # Process attributes
    df['state'] = df['inst'].apply(get_state)
    df['inst_name'] = df['inst'].apply(lambda x: x.split(',')[0].strip())
    df['course_name'] = df['course'].apply(clean_text)
    
    # Mizoram Check
    miz = df[df['state'] == 'Mizoram']
    print(f"Mizoram records found: {len(miz)}")
    
    # Aggregation
    registry = df[['inst_name', 'course_name', 'quota', 'cat', 'state']].drop_duplicates()
    results = []
    
    # Pre-filter to speed up aggregation
    df_grouped = df.groupby(['inst_name', 'course_name', 'quota', 'cat', 'state'])
    
    for (inst, course, quota, cat, state), group in tqdm(df_grouped, desc="Aggregating"):
        ranks = {"2025_R1": [], "2025_R2": [], "2025_R3": []}
        
        for r in ranks.keys():
            r_data = group[group['round'] == r]
            if not r_data.empty:
                # Store all ranks, sorted
                ranks[r] = sorted([int(x) for x in r_data['rank'].tolist()])
        
        results.append({
            "id": len(results) + 1,
            "institute": inst,
            "state": state,
            "course": course,
            "quota": quota,
            "category": cat,
            "fee": "-",
            "stipend": "-",
            "bondPenalty": "-",
            "bondYears": "-",
            "ranks": ranks
        })

    with open("src/data/closingRanks.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} entries to JSON.")

if __name__ == "__main__":
    main()
