#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to see what's being extracted from PDF
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

def debug_pdf_extraction(pdf_path: str, start_page: int, end_page: int):
    """Debug PDF extraction to see what we're getting"""
    print(f"Debugging PDF extraction from {pdf_path} (pages {start_page}-{end_page})")
    
    # Test different regex patterns
    patterns = [
        r'\d+\.\s+(.+?)\s+-\s+Договор займа\s*\(кредита\)\s*-\s*(.+?)(?=\s*\d+\.|\Z)',
        r'\d+\.\s+(.+?)\s*-\s*Договор займа\s*\(кредита\)\s*(.+?)(?=\s*\d+\.|\Z)',
        r'(\d+\.\s+[А-Я][^.]*?банк[^.]*?)(.+?)(?=\d+\.|\Z)',
        r'(\d+\.\s+[А-Я][^.]*?кредит[^.]*?)(.+?)(?=\d+\.|\Z)',
        # New pattern to match exactly what we want
        r'\d+\.\s+([^-\n]+?)\s*-\s*Договор займа\s*\(кредита\)\s*-\s*([^-\n]+?)(?=\s*\d+\.|\Z)',
        # Simple pattern to find numbered entries
        r'\d+\.\s+([^.\n]+?банк[^.\n]*?)(?=\s*\d+\.|\Z)',
    ]
    
    with open(pdf_path, 'rb') as f:
        reader = PdfReader(f)
        
        for page_num in range(start_page - 1, min(end_page, len(reader.pages))):
            page = reader.pages[page_num]
            text = page.extract_text(visitor_text=visitor_body)
            
            if not text.strip():
                print(f"Page {page_num + 1}: No text extracted")
                continue
            
            print(f"\n{'='*60}")
            print(f"PAGE {page_num + 1}")
            print(f"{'='*60}")
            print("RAW TEXT:")
            print(text[:1000] + "..." if len(text) > 1000 else text)
            print(f"\nText length: {len(text)} characters")
            
            # Test each pattern
            for i, pattern in enumerate(patterns):
                print(f"\n--- Pattern {i+1}: {pattern} ---")
                matches = list(re.finditer(pattern, text, re.DOTALL | re.IGNORECASE))
                print(f"Found {len(matches)} matches")
                
                for j, match in enumerate(matches[:3]):  # Show first 3 matches
                    print(f"  Match {j+1}:")
                    print(f"    Full match: {match.group(0)[:200]}...")
                    if len(match.groups()) >= 2:
                        print(f"    Group 1: {match.group(1)}")
                        print(f"    Group 2: {match.group(2)}")
                    print()
            
            # Look for specific patterns like "1. АО"
            print("--- Looking for numbered entries ---")
            numbered_entries = re.findall(r'\d+\.\s+([^.\n]+)', text)
            print(f"Found {len(numbered_entries)} numbered entries:")
            for entry in numbered_entries[:5]:  # Show first 5
                print(f"  {entry.strip()}")
            
            # Stop after first page for debugging
            break

def main():
    if len(sys.argv) < 4:
        print("Usage: python debug_extraction.py <pdf_file> <start_page> <end_page>")
        print("Example: python debug_extraction.py ./data/credit_history.pdf 1 1")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    start_page = int(sys.argv[2])
    end_page = int(sys.argv[3])
    
    debug_pdf_extraction(pdf_file, start_page, end_page)

if __name__ == "__main__":
    main() 