import os
import re
import json
import subprocess
from glob import glob
# from tqdm import tqdm

def get_text_from_pdf(pdf_path, layout=True):
    try:
        cmd = ["pdftotext"]
        if layout:
            cmd.append("-layout")
        cmd.extend([pdf_path, "-"])
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        # print(f"Error parsing {pdf_path}: {e}")
        return ""

def extract_profile_info(text):
    info = {
        "admission_fee": "",
        "stipend_y1": "",
        "stipend_y2": "",
        "stipend_y3": ""
    }
    
    # Fee Extraction
    # Look for "Amount to be Paid at the time of Admission" followed by a number on the same line or next line
    fee_match = re.search(r"Amount to be Paid at the time of\s+(\d+)", text)
    if fee_match:
        info["admission_fee"] = fee_match.group(1)
    
    # Stipend Extraction
    s1_match = re.search(r"Stipend Paid to the students I st Year\s+(\d+)", text)
    if s1_match:
        info["stipend_y1"] = s1_match.group(1)
        
    s2_match = re.search(r"Stipend Paid to the students IInd Year\s+(\d+)", text)
    if s2_match:
        info["stipend_y2"] = s2_match.group(1)
        
    s3_match = re.search(r"Stipend Paid to the students IIIrd Year\s+(\d+)", text)
    if s3_match:
        info["stipend_y3"] = s3_match.group(1)
        
    return info

def word_to_num(text):
    mapping = {
        'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
        'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10'
    }
    return mapping.get(text.lower(), text)

def extract_bond_info(text, code=""):
    info = {
        "bond_years": "",
        "bond_penalty": ""
    }
    
    # Bond Years
    # Look for a number near "year" and "service/compulsory/bond"
    # Allow for things like "2 (two) years" or "one (1) year"
    year_matches = re.finditer(r"(\d+|one|two|three|four|five|six|seven|eight|9|10)\s*(?:\([^)]*\)\s*)?(?:year|yr)s?", text, re.IGNORECASE)
    for m in year_matches:
        context = text[max(0, m.start()-60):min(len(text), m.end()+60)].lower()
        if any(kw in context for kw in ["compulsory", "service", "bond", "period", "undertaking", "mandatory"]):
            info["bond_years"] = word_to_num(m.group(1))
            break
            
    # Bond Penalty - Proximity Matching
    amounts = []
    
    # 1. Lakhs pattern
    lakh_matches = re.finditer(r"(\d+(?:\.\d+)?)\s*lakhs?", text, re.IGNORECASE)
    for m in lakh_matches:
        context = text[max(0, m.start()-100):min(len(text), m.end()+100)].lower()
        if any(kw in context for kw in ["bond", "penalty", "service", "amount", "rs", "rupee"]):
            try:
                amounts.append(int(float(m.group(1).replace(',', '')) * 100000))
            except: pass
            
    # 2. Large numbers pattern
    # Look for numbers with commas or explicit currency marks
    digit_matches = re.finditer(r"(?:rs\.?|inr|rupees?|amount|penalty)\s*:?\s*(\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d{5,8}(?:\.\d+)?)", text, re.IGNORECASE)
    for m in digit_matches:
        val_str = m.group(1).replace(',', '')
        try:
            val = int(float(val_str))
            # Limit range to likely bond amounts (50k to 1 Crore)
            if 50000 <= val <= 10000000:
                context = text[max(0, m.start()-60):min(len(text), m.end()+60)].lower()
                # Must have a strong keyword in context
                if any(kw in context for kw in ["bond", "penalty", "service", "pay", "rupee", "rs"]):
                    # Avoid catching years or dates
                    if not any(kw in context for kw in ["year", "date", "2010", "2020", "2024", "2025"]):
                        amounts.append(val)
        except: pass
        
    if amounts:
        # print(f"DEBUG {code}: Amounts: {amounts}")
        # Prioritize values that are multiples of 50k or 1L as they are more likely to be bond amounts
        priority_amounts = [a for a in amounts if a % 50000 == 0]
        if priority_amounts:
            info["bond_penalty"] = str(max(priority_amounts))
        else:
            info["bond_penalty"] = str(max(amounts))
            
    return info

def main():
    profile_dir = 'data/mcc_profiles'
    bond_dir = 'data/mcc_bonds'
    output_file = 'mcc_data.json'
    
    all_data = {}
    
    profile_files = glob(os.path.join(profile_dir, '*_profile.pdf'))
    print(f"Parsing {len(profile_files)} profile PDFs...")
    
    for idx, pf in enumerate(profile_files):
        code = os.path.basename(pf).split('_')[0]
        text = get_text_from_pdf(pf, layout=True)
        info = extract_profile_info(text)
        
        if code not in all_data:
            all_data[code] = {}
        all_data[code].update(info)
        if (idx + 1) % 20 == 0:
            print(f"Parsed {idx + 1} profiles...")
        
    bond_files = glob(os.path.join(bond_dir, '*_bond.pdf'))
    print(f"Parsing {len(bond_files)} bond PDFs...")
    
    for idx, bf in enumerate(bond_files):
        code = os.path.basename(bf).split('_')[0]
        text = get_text_from_pdf(bf, layout=True)
        info = extract_bond_info(text, code=code)
        
        if code not in all_data:
            all_data[code] = {}
        all_data[code].update(info)
        if (idx + 1) % 20 == 0:
            print(f"Parsed {idx + 1} bonds...")
        
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2)
        
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
