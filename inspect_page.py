import pdfplumber

def inspect_page(pdf_path, page_num):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num - 1]
        print(f"--- TEXT PAGE {page_num} ---")
        print(page.extract_text())
        print("\n--- TABLE PAGE {page_num} ---")
        table = page.extract_table()
        if table:
            for row in table:
                print(row)

if __name__ == "__main__":
    inspect_page("round2_2025.pdf", 705)
