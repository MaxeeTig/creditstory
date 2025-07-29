#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of Credit History Processor
Demonstrates programmatic usage of the processor
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from credit_history_processor import CreditHistoryProcessor
import config

def example_basic_processing():
    """Example of basic processing workflow"""
    print("=== Basic Processing Example ===")
    
    # Check for API key
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("Error: MISTRAL_API_KEY not set")
        return False
    
    # Initialize processor
    processor = CreditHistoryProcessor(api_key, "example_credit_history.db")
    
    # Example PDF path (replace with your actual file)
    pdf_file = "./data/credit_history.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"PDF file not found: {pdf_file}")
        print("Please place your credit history PDF in the data/ directory")
        return False
    
    try:
        # Step 1: Extract paragraphs (example: pages 1-10)
        print("Step 1: Extracting paragraphs...")
        extracted_count = processor.extract_paragraphs_from_pdf(pdf_file, 1, 10)
        
        if extracted_count == 0:
            print("No paragraphs extracted. Check PDF content.")
            return False
        
        print(f"Extracted {extracted_count} paragraphs")
        
        # Step 2: Process with AI (small batch for example)
        print("Step 2: Processing with AI...")
        processor.process_paragraphs(batch_size=2, delay=1.0)
        
        # Step 3: Export to CSV
        print("Step 3: Exporting to CSV...")
        output_file = f"example_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        processor.export_to_csv(output_file)
        
        # Show statistics
        stats = processor.get_statistics()
        print("\nProcessing Statistics:")
        print(f"  Total paragraphs: {stats['total_paragraphs']}")
        print(f"  Processed paragraphs: {stats['processed_paragraphs']}")
        print(f"  Extracted loans: {stats['total_loans']}")
        print(f"  Success rate: {stats['success_rate']:.1%}")
        
        print(f"\nResults saved to: {output_file}")
        return True
        
    except Exception as e:
        print(f"Processing failed: {e}")
        return False

def example_custom_configuration():
    """Example with custom configuration"""
    print("\n=== Custom Configuration Example ===")
    
    # Set custom environment variables
    os.environ["BATCH_SIZE"] = "3"
    os.environ["API_DELAY"] = "2.0"
    os.environ["CREDIT_DB_PATH"] = "custom_credit_history.db"
    
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("Error: MISTRAL_API_KEY not set")
        return False
    
    # Initialize with custom database
    processor = CreditHistoryProcessor(api_key, "custom_credit_history.db")
    
    print("Custom configuration applied:")
    print(f"  Batch size: {config.BATCH_SIZE}")
    print(f"  API delay: {config.API_DELAY}")
    print(f"  Database: {config.DATABASE_PATH}")
    
    return True

def example_database_queries():
    """Example of querying the database directly"""
    print("\n=== Database Query Example ===")
    
    import sqlite3
    
    db_path = "credit_history.db"
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        print("Run processing first to create database")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Get total counts
            total_paragraphs = conn.execute("SELECT COUNT(*) FROM paragraphs").fetchone()[0]
            total_loans = conn.execute("SELECT COUNT(*) FROM loans").fetchone()[0]
            
            print(f"Database contains:")
            print(f"  Total paragraphs: {total_paragraphs}")
            print(f"  Total loans: {total_loans}")
            
            # Get sample loans
            cursor = conn.execute("""
                SELECT bank_name, loan_amount, loan_currency, loan_status
                FROM loans 
                LIMIT 5
            """)
            
            print("\nSample loans:")
            for row in cursor:
                print(f"  {row[0]}: {row[1]} {row[2]} ({row[3]})")
        
        return True
        
    except Exception as e:
        print(f"Database query failed: {e}")
        return False

def example_resume_processing():
    """Example of resuming processing from where it left off"""
    print("\n=== Resume Processing Example ===")
    
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("Error: MISTRAL_API_KEY not set")
        return False
    
    processor = CreditHistoryProcessor(api_key)
    
    # Get unprocessed paragraphs
    unprocessed = list(processor.get_unprocessed_paragraphs())
    
    if unprocessed:
        print(f"Found {len(unprocessed)} unprocessed paragraphs")
        print("Resuming processing...")
        
        # Process remaining paragraphs
        processor.process_paragraphs(batch_size=3, delay=1.5)
        
        # Export updated results
        output_file = f"resumed_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        processor.export_to_csv(output_file)
        
        print(f"Resume processing complete. Results: {output_file}")
        return True
    else:
        print("No unprocessed paragraphs found")
        return True

def main():
    """Run all examples"""
    print("Credit History Processor - Usage Examples")
    print("=" * 50)
    
    examples = [
        ("Basic Processing", example_basic_processing),
        ("Custom Configuration", example_custom_configuration),
        ("Database Queries", example_database_queries),
        ("Resume Processing", example_resume_processing)
    ]
    
    for name, example_func in examples:
        print(f"\nRunning: {name}")
        try:
            success = example_func()
            if success:
                print(f"✓ {name} completed successfully")
            else:
                print(f"✗ {name} failed")
        except Exception as e:
            print(f"✗ {name} failed with error: {e}")
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nTo run the processor directly:")
    print("python credit_history_processor.py <pdf_file> <start_page> <end_page>")

if __name__ == "__main__":
    main() 