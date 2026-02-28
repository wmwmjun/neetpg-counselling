import pdfplumber
import sys

def find_rank(pdf_path, rank_to_find):
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            table = page.extract_table()
            if not table:
                continue
            for row in table:
                if row and str(row[0]).strip() == str(rank_to_find):
                    print(f"Page {i}: {row}")
                    return True
    return False

if __name__ == "__main__":
    pdf_file = "round2_2025.pdf"
    rank = "7879"
    if not find_rank(pdf_file, rank):
        print(f"Rank {rank} not found in {pdf_file}")
