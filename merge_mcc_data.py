import json
import os

def format_amount(amount):
    if amount is None or amount == "" or amount == "0":
        return "-"
    try:
        val = int(amount)
        if val == 0: return "-"
        return f"{val:,}"
    except:
        return amount

def main():
    mcc_data_file = 'mcc_data.json'
    name_to_code_file = 'name_to_code.json'
    ranks_file = 'src/data/closingRanks.json'
    output_file = 'src/data/closingRanks.json' # Overwrite
    
    if not os.path.exists(mcc_data_file) or not os.path.exists(name_to_code_file):
        print("Missing mapping files.")
        return
        
    with open(mcc_data_file, 'r') as f:
        mcc_data = json.load(f)
        
    with open(name_to_code_file, 'r') as f:
        name_to_code = json.load(f)
        
    with open(ranks_file, 'r') as f:
        ranks_data = json.load(f)
        
    updated_count = 0
    for record in ranks_data:
        inst_name = record.get('institute')
        code = name_to_code.get(inst_name)
        
        if code and code in mcc_data:
            data = mcc_data[code]
            
            # Update fields if data exists and is not None
            if data.get('admission_fee'):
                record['fee'] = format_amount(data['admission_fee'])
            
            # We'll use Stipend Y1 as the default stipend for now
            if data.get('stipend_y1'):
                record['stipend'] = format_amount(data['stipend_y1'])
            
            if data.get('bond_penalty'):
                record['bondPenalty'] = format_amount(data['bond_penalty'])
            
            if data.get('bond_years'):
                record['bondYears'] = data['bond_years']
            
            updated_count += 1
            
    with open(output_file, 'w') as f:
        json.dump(ranks_data, f, indent=2)
        
    print(f"Updated {updated_count} records in {output_file}")

if __name__ == "__main__":
    main()
