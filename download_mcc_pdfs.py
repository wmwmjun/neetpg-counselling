import os
import urllib.request
import urllib.error
import time

def download_file(url, output_path):
    if os.path.exists(output_path):
        return True
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    retries = 3
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as response:
                content_type = response.info().get_content_type()
                if content_type == 'application/pdf':
                    with open(output_path, 'wb') as f:
                        f.write(response.read())
                    return True
                else:
                    body = response.read().decode('utf-8', errors='ignore')
                    if 'Requested Resource not found' in body:
                        return False
            time.sleep(1)
        except Exception as e:
            time.sleep(2)
    return False

def main():
    institutes_file = 'mcc_institutes.txt'
    profile_dir = 'data/mcc_profiles'
    bond_dir = 'data/mcc_bonds'
    
    os.makedirs(profile_dir, exist_ok=True)
    os.makedirs(bond_dir, exist_ok=True)
    
    with open(institutes_file, 'r') as f:
        lines = f.readlines()
    
    total = len(lines)
    print(f"Total institutes to process: {total}")
    
    for idx, line in enumerate(lines):
        try:
            code = line.split('|')[0].strip()
            
            # Profile PDF
            profile_url = f"https://mcc.admissions.nic.in/Counseling/Handler/ViewInstituteProfileDetailsDynamic.ashx?boardId=140012521&InstituteId={code}"
            profile_path = os.path.join(profile_dir, f"{code}_profile.pdf")
            download_file(profile_url, profile_path)
            
            # Bond PDF
            bond_url = f"https://mcc.admissions.nic.in/Counseling/Handler/ViewInstituteProfileDynamic.ashx?boardId=140012521&InstituteId={code}&Type=BM"
            bond_path = os.path.join(bond_dir, f"{code}_bond.pdf")
            download_file(bond_url, bond_path)
            
            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1}/{total}...")
            
            time.sleep(0.3) # Rate limit
            
        except Exception as e:
            print(f"Error processing {line.strip()}: {e}")

if __name__ == "__main__":
    main()
