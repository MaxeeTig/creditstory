#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple loan entry extractor - similar to test_read1.py approach
"""

import sys
import re
from PyPDF2 import PdfReader

def visitor_body(text, cm, tm, fontDict, fontSize):
    """Filter out headers/footers based on y-coordinate"""
    y = tm[5]
    if 50 < y < 720:  # Ignore header/footer
        return text
    return ""

def extract_loan_entries(pdf_path: str, start_page: int, end_page: int):
    """Extract individual loan entries from PDF"""
    print(f"Extracting loan entries from {pdf_path} (pages {start_page}-{end_page})")
    
    # Pattern to extract just the header line with bank and loan type
    pattern = r'\d+\.\s+(.+?)\s+-\s+Договор займа\s*\(кредита\)\s+-\s+([^\n]+)'
    
    entries = []
    
    with open(pdf_path, 'rb') as f:
        reader = PdfReader(f)
        
        for page_num in range(start_page - 1, min(end_page, len(reader.pages))):
            page = reader.pages[page_num]
            text = page.extract_text(visitor_text=visitor_body)
            
            if not text.strip():
                continue
            
            print(f"\nProcessing page {page_num + 1}")
            print(f"Text length: {len(text)} characters")
            
            # Find matches
            matches = re.finditer(pattern, text, re.DOTALL)
            
            for match in matches:
                bank = match.group(1).replace('\n', ' ').strip()
                loan_type = match.group(2).replace('\n', ' ').strip()
                
                # Also extract the full content for this loan entry
                full_match_start = match.start()
                # Find the next numbered entry or end of text
                next_match = re.search(r'\n\d+\.\s+', text[full_match_start:])
                if next_match:
                    full_content = text[full_match_start:full_match_start + next_match.start()]
                else:
                    full_content = text[full_match_start:]
                
                entry = {
                    'page': page_num + 1,
                    'bank': bank,
                    'loan_type': loan_type,
                    'full_content': full_content.strip(),
                    'header_line': match.group(0).strip()
                }
                
                entries.append(entry)
                print(f"  Found: {bank} - {loan_type}")
    
    print(f"\nTotal entries found: {len(entries)}")
    return entries

def save_entries_to_file(entries, output_file):
    """Save extracted entries to a text file for inspection"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Extracted Loan Entries\n")
        f.write("=" * 50 + "\n\n")
        
        for i, entry in enumerate(entries, 1):
            f.write(f"Entry {i}:\n")
            f.write(f"Page: {entry['page']}\n")
            f.write(f"Header: {entry['header_line']}\n")
            f.write(f"Bank: {entry['bank']}\n")
            f.write(f"Loan Type: {entry['loan_type']}\n")
            f.write(f"Full Content Length: {len(entry['full_content'])} characters\n")
            f.write(f"Full Content Preview: {entry['full_content'][:300]}...\n")
            f.write("-" * 30 + "\n\n")

def main():
    if len(sys.argv) < 4:
        print("Usage: python simple_extractor.py <pdf_file> <start_page> <end_page>")
        print("Example: python simple_extractor.py ./data/credit_history.pdf 1 5")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    start_page = int(sys.argv[2])
    end_page = int(sys.argv[3])
    
    # Extract entries
    entries = extract_loan_entries(pdf_file, start_page, end_page)
    
    if entries:
        # Save to file for inspection
        output_file = f"extracted_entries_{start_page}_{end_page}.txt"
        save_entries_to_file(entries, output_file)
        print(f"\nEntries saved to: {output_file}")
        
        # Show summary
        print("\nSummary:")
        for entry in entries[:5]:  # Show first 5
            print(f"  {entry['bank']} - {entry['loan_type']}")
        if len(entries) > 5:
            print(f"  ... and {len(entries) - 5} more entries")
    else:
        print("No entries found. Check PDF content and page range.")

if __name__ == "__main__":
    main() 