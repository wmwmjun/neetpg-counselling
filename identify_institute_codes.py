import json
import difflib

def clean_name(name):
    name = name.lower()
    # Remove common suffixes and punctuation
    name = name.replace(',', ' ').replace('.', ' ').replace('-', ' ')
    # Remove extra spaces
    return " ".join(name.split())

def main():
    mcc_file = 'mcc_institutes.txt'
    ranks_file = 'src/data/closingRanks.json'
    output_file = 'name_to_code.json'
    
    mcc_map = {}
    with open(mcc_file, 'r') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 2:
                code = parts[0]
                name = parts[1]
                mcc_map[code] = name
                
    with open(ranks_file, 'r') as f:
        ranks_data = json.load(f)
        
    unique_names = sorted(list({r['institute'] for r in ranks_data}))
    print(f"Total unique institutes in ranks data: {len(unique_names)}")
    
    name_to_code = {}
    mcc_names_clean = {clean_name(name): code for code, name in mcc_map.items()}
    mcc_names_list = list(mcc_names_clean.keys())
    
    for name in unique_names:
        cname = clean_name(name)
        
        # 1. Direct Match
        if cname in mcc_names_clean:
            name_to_code[name] = mcc_names_clean[cname]
            continue
            
        # 2. Substring Match (is rank name inside MCC name?)
        found = False
        for mcc_cname in mcc_names_list:
            if cname in mcc_cname:
                name_to_code[name] = mcc_names_clean[mcc_cname]
                found = True
                break
        if found: continue
        
        # 3. Fuzzy Match
        matches = difflib.get_close_matches(cname, mcc_names_list, n=1, cutoff=0.7)
        if matches:
            name_to_code[name] = mcc_names_clean[matches[0]]
            continue
            
        print(f"Could not map: {name}")

    with open(output_file, 'w') as f:
        json.dump(name_to_code, f, indent=2)
    
    print(f"Mapped {len(name_to_code)}/{len(unique_names)} names.")

if __name__ == "__main__":
    main()
