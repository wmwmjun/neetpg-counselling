import pdfplumber
import re
import sys

def debug_state_extraction(pdf_path, state_name):
    print(f"Searching for {state_name} in {pdf_path}...")
    with pdfplumber.open(pdf_path) as pdf:
        found_count = 0
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text: continue
            
            if state_name.lower() in text.lower():
                print(f"Found {state_name} on page {i+1}")
                # Print a snippet
                lines = text.split('\n')
                for line in lines:
                    if state_name.lower() in line.lower():
                        print(f"  Line: {line.strip()}")
                found_count += 1
                if found_count > 5: break

if __name__ == "__main__":
    debug_state_extraction("round2_2025.pdf", "Mizoram")
    debug_state_extraction("round3_2025.pdf", "Mizoram")
