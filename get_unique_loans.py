# -*- coding: utf-8 -*-
# Script to get unique loan headers from credit history report
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

def get_unique_headers_ordered(text):
    headers = []
    seen = set()
    for match in re.finditer(r'^\d+\.\s+(.+)$', text, re.MULTILINE):
        header = match.group(1)
        if header not in seen:
            seen.add(header)
            headers.append({
                'text': header,
                'start_pos': match.start(),
                'end_pos': match.end()
            })
    return headers

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
    report_file = f"{default_folder}/{partial_file_name}_unique_loans_report_{timestamp}.txt"

    # Read and process PDF
    text = read_pdf(pdf_file, start_page, end_page)
    
    # Capture headers only 
    headers = get_unique_headers_ordered(text)
   
    print(f"Found {len(headers)} unique headers:")
    report_content = [] 

    for i, header in enumerate(headers, 1):
        print(f"{i}. {header['text']} (position {header['start_pos']}-{header['end_pos']})")
        report_content.append(header['text'])
  
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_content))

    print(f"Report saved to: {report_file}")

if __name__ == "__main__":
    main()