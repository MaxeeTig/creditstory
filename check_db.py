#!/usr/bin/env python3
import sqlite3

# Check database contents
with sqlite3.connect('credit_history.db') as conn:
    print("=== PARAGRAPHS TABLE ===")
    cursor = conn.execute("SELECT id, content[:100], page_number, processed FROM paragraphs")
    for row in cursor:
        print(f"ID: {row[0]}, Page: {row[2]}, Processed: {row[3]}")
        print(f"Content: {row[1]}...")
        print()
    
    print("=== LOANS TABLE ===")
    cursor = conn.execute("SELECT * FROM loans")
    for row in cursor:
        print(f"Loan ID: {row[0]}")
        print(f"Paragraph ID: {row[1]}")
        print(f"Bank: {row[2]}")
        print(f"Deal Date: {row[3]}")
        print(f"Deal Type: {row[4]}")
        print(f"Loan Type: {row[5]}")
        print(f"Card Usage: {row[6]}")
        print(f"Amount: {row[7]}")
        print(f"Currency: {row[8]}")
        print(f"Termination: {row[9]}")
        print(f"Status: {row[10]}")
        print() 