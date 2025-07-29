# -*- coding: utf-8 -*-
import sys
import re
from PyPDF2 import PdfReader
from datetime import datetime

def visitor_body(text, cm, tm, fontDict, fontSize):
    y = tm[5]
    if 50 < y < 720:  # Ignore header/footer
        return text

def read_pdf(file_path, start_page, end_page):
    full_text = []
    with open(file_path, 'rb') as f:
        reader = PdfReader(f)
        for page_num in range(start_page - 1, min(end_page, len(reader.pages))):
            page = reader.pages[page_num]
            text = page.extract_text(visitor_text=visitor_body)
            if text:
                full_text.append(text)
    return '\n'.join(full_text)

def extract_bank_loan_info(text):
    pattern = r'\d+\.\s+(.+?)\s+-\s+Договор займа \(кредита\)\s+-\s+(.+?)(?=\s*\d+\.|\Z)'
    matches = re.finditer(pattern, text, re.DOTALL)
    return matches

def main():
    if len(sys.argv) < 4:
        print("Usage: python test_read1.py <partial_file_name> <start_page> <end_page>")
        print("Example: python test_read1.py credit_history 5 15")
        sys.exit(1)

    partial_file_name = sys.argv[1]
    start_page = int(sys.argv[2])
    end_page = int(sys.argv[3])

    default_folder = "./data"
    pdf_file = f"{default_folder}/{partial_file_name}.pdf"
    
    # Generate timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_text_file = f"{default_folder}/{partial_file_name}_raw_{timestamp}.txt"
    report_file = f"{default_folder}/{partial_file_name}_report_{timestamp}.txt"

    # Read and process PDF
    text = read_pdf(pdf_file, start_page, end_page)
    matches = extract_bank_loan_info(text)

    # Prepare report content
    report_content = []
    report_content.append(f"Credit History Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_content.append(f"Source: {pdf_file} (pages {start_page}-{end_page})")
    report_content.append("\nList of banks and loan types:")
    
    for i, match in enumerate(matches, 1):
        bank = match.group(1).replace('\n', ' ').strip()
        loan_type = match.group(2).replace('\n', ' ').strip()
        line = f"{i}. {bank}: {loan_type}"
        print(line)  # Print to console
        report_content.append(line)

    # Write output files
    with open(raw_text_file, "w", encoding="utf-8") as f:
        f.write(text)
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_content))

    print(f"\nRaw text saved to: {raw_text_file}")
    print(f"Report saved to: {report_file}")

if __name__ == "__main__":
    main()
