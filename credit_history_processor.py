#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Credit History Processor
Combines PDF text extraction with AI-powered loan parameter extraction
"""

import sys
import re
import json
import csv
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional, Iterator
from pathlib import Path
import time
from dataclasses import dataclass, asdict
import logging

from PyPDF2 import PdfReader
from pydantic import BaseModel, Field, field_validator
from mistralai import Mistral
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('credit_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Paragraph:
    """Represents an extracted paragraph from PDF"""
    id: int
    content: str
    page_number: int
    extracted_at: datetime
    processed: bool = False
    processing_error: Optional[str] = None

class Loan(BaseModel):
    """Represents extracted loan information"""
    paragraph_id: int = Field(..., description="ID of the source paragraph")
    bank_name: str = Field(..., description="Full name of the bank or credit institution")
    deal_date: Optional[date] = Field(None, description="Date when the loan agreement was signed")
    deal_type: Optional[str] = Field(None, description="Type of the loan agreement")
    loan_type: Optional[str] = Field(None, description="Category of the loan")
    card_usage: Optional[bool] = Field(None, description="Whether a payment card is used")
    loan_amount: Optional[float] = Field(None, description="Principal amount of the loan")
    loan_currency: Optional[str] = Field(None, description="Currency of the loan")
    termination_date: Optional[date] = Field(None, description="Date when the loan was terminated")
    actual_termination_date: Optional[date] = Field(None, description="Actual termination date when loan was closed")  
    loan_status: Optional[str] = Field(None, description="Current status of the loan")
    extracted_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('deal_date', 'termination_date', mode='before')
    def parse_date(cls, value):
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%d-%m-%Y").date()
            except ValueError:
                return None
        return None

class CreditHistoryProcessor:
    def __init__(self, mistral_api_key: str, db_path: str = "credit_history.db"):
        """Initialize the processor"""
        self.db_path = db_path
        self.mistral_client = Mistral(api_key=mistral_api_key)
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS paragraphs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE,
                    processing_error TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS loans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paragraph_id INTEGER,
                    bank_name TEXT,
                    deal_date TEXT,
                    deal_type TEXT,
                    loan_type TEXT,
                    card_usage BOOLEAN,
                    loan_amount REAL,
                    loan_currency TEXT,
                    termination_date TEXT,
                    loan_status TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (paragraph_id) REFERENCES paragraphs (id)
                )
            """)
            conn.commit()
    
    def visitor_body(self, text, cm, tm, fontDict, fontSize):
        """Filter out headers/footers based on y-coordinate"""
        y = tm[5]
        if 50 < y < 720:  # Ignore header/footer
            return text
        return ""
    
        
    # Improved function for extraction 
        
    def extract_paragraphs_from_pdf(self, pdf_path: str, start_page: int, end_page: int) -> int:
        """Extract full loan entries from PDF including all details"""
        logger.info(f"Extracting paragraphs from {pdf_path} (pages {start_page}-{end_page})")
        
        # Pattern to identify loan headers
        header_pattern = r'''
            ^\d+\.\s+                      # Number and dot
            (.+?)                          # Bank name
            \s+-\s+                        # Separator
            (?:Договор\s+займа\s*\(кредита\)
            |Поручительство\s+по\s+займу\s*\(кредиту\)
            |Потребит\.кредит
            |Кредитная\s+карта
            |Микрокредит)
            \s*(?:-\s*([^-]+))?
            '''
        
        extracted_count = 0
        
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            
            for page_num in range(start_page - 1, min(end_page, len(reader.pages))):
                page = reader.pages[page_num]
                text = page.extract_text(visitor_text=self.visitor_body)
                
                if not text.strip():
                    continue
                
                # Find all header positions first
                headers = list(re.finditer(header_pattern, text, re.VERBOSE | re.MULTILINE | re.IGNORECASE))
                
                # Extract full content between headers
                for i, match in enumerate(headers):
                    start_pos = match.start()
                    
                    # Determine end position (next header or end of text)
                    end_pos = headers[i+1].start() if i+1 < len(headers) else len(text)
                    
                    full_content = text[start_pos:end_pos].strip()
                    
                    # Clean up but preserve structure
                    full_content = re.sub(r'\s+', ' ', full_content)
                    full_content = full_content.replace('\n', ' ')
                    
                    # Debug print content and length
                    print(f"Extracted: {full_content}, {len(full_content)}")
                    
                    if len(full_content) > 100:  # Increased minimum length
                        self._store_paragraph(full_content, page_num + 1)
                        extracted_count += 1
                        logger.debug(f"Extracted loan entry ({len(full_content)} chars): {full_content[:100]}...")
                
                if (page_num + 1) % 50 == 0:
                    logger.info(f"Processed page {page_num + 1}")
        
        logger.info(f"Extracted {extracted_count} full loan entries")
        return extracted_count

        
    
    def _store_paragraph(self, content: str, page_number: int):
        """Store paragraph in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO paragraphs (content, page_number) VALUES (?, ?)",
                (content, page_number)
            )
            conn.commit()
    
    def get_unprocessed_paragraphs(self) -> Iterator[Paragraph]:
        """Get all unprocessed paragraphs from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM paragraphs WHERE processed = FALSE ORDER BY id"
            )
            
            for row in cursor:
                yield Paragraph(
                    id=row['id'],
                    content=row['content'],
                    page_number=row['page_number'],
                    extracted_at=datetime.fromisoformat(row['extracted_at']),
                    processed=row['processed'],
                    processing_error=row['processing_error']
                )
    
    def extract_loan_parameters(self, paragraph: Paragraph) -> Optional[Loan]:
        """Extract loan parameters using Mistral AI"""
        
        system_prompt = """You are an expert financial data parser that extracts loan information from Russian credit reports. 
        The input text represents a flattened table with these characteristics:
        1. Field names appear in the text followed by their values at specific offsets
        2. Each field has a consistent positional offset from its label
        3. Values may contain multiple words/numbers

        Extraction Rules:
        1. Use these exact field mappings and offsets:
           | Russian Label                  | English Field       | Value Offset | Example Value               |
           |--------------------------------|---------------------|--------------|-----------------------------|
           | "Полное наименование"          | bank_name           | +3           | "АО Райффайзенбанк"         |
           | "Дата сделки"                  | deal_date           | +6           | "18-05-2024"                |
           | "Тип сделки"                   | deal_type           | +6           | "Договор займа (кредита)"   |
           | "Вид займа (кредита)"          | loan_type           | +6           | "Иной заем (кредит)"        |
           | "Использование платежной карты"| card_usage          | +6           | "Да" → true                 |
           | "Сумма и валюта"               | loan_amount         | +6           | "50000,00 RUB"              |
           | "Дата прекращения по условиям" | termination_date    | +6           | "31-12-9999" → null         |
           | "Дата фактического прекращения"| actual_termination  | +6           | "Н/Д" → null                |

        2. Value extraction process:
           a. Locate the Russian label in text
           b. Count N words/tokens after it (based on offset)
           c. Capture the value at that position

        Required Output Format (JSON):
        {
          "bank_name": "string",
          "deal_date": "DD-MM-YYYY",
          "deal_type": "string",
          "loan_type": "string",
          "card_usage": boolean,
          "loan_amount": "number,currency",
          "termination_date": "DD-MM-YYYY or null",
          "actual_termination_date": "DD-MM-YYYY or null"
        }

        Special Cases:
        1. For termination dates:
           - "31-12-9999" → null (active loan)
           - "Н/Д" → null
        2. For boolean fields:
           - "Да" → true
           - "Нет" → false
        3. Preserve original formatting for:
           - Bank names (keep Russian characters)
           - Loan amounts ("50000,00 RUB")

        Example Input 1:
        "Полное наименование ОГРН/ИНН Вид Акционерное общество Райффайзенбанк ... Дата сделки Тип сделки Вид займа (кредита) Использование платежной карты Сумма и валюта Дата прекращения по условиям сделки 18-05-2024 Договор займа (кредита) Иной заем (кредит) Да 50000,00 RUB 31-12-9999"

        Example Output 1:
        {
          "bank_name": "Акционерное общество Райффайзенбанк",
          "deal_date": "18-05-2024",
          "deal_type": "Договор займа (кредита)",
          "loan_type": "Иной заем (кредит)",
          "card_usage": true,
          "loan_amount": "50000,00 RUB",
          "termination_date": null,
          "actual_termination_date": null
        }

        Example Input 2:
        "Полное наименование ОГРН/ИНН Вид ПАО Сбербанк 1027700132195 7707083893 ... Дата сделки Тип сделки Вид займа (кредита) Использование платежной карты Сумма и валюта Дата прекращения по условиям сделки 15-01-2023 Потребительский кредит Нет 120000,00 RUB 15-01-2025"

        Example Output 2:
        {
          "bank_name": "ПАО Сбербанк",
          "deal_date": "15-01-2023",
          "deal_type": "Потребительский кредит",
          "loan_type": "Потребительский кредит",
          "card_usage": false,
          "loan_amount": "120000,00 RUB",
          "termination_date": "15-01-2025",
          "actual_termination_date": null
        }

        Now parse the following input text and return ONLY valid JSON:
        """
        
        try:
            response = self.mistral_client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": paragraph.content
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0
            )
            
            json_str = response.choices[0].message.content
            
            # Debug print
            print(f"json from LLM:{json_str}")
            
            # Clean the response if needed
            if json_str.startswith('[') and json_str.endswith(']'):
                json_str = json_str[1:-1]
            
            loan_data = json.loads(json_str)
            loan_data['paragraph_id'] = paragraph.id
            
            # Process amount/currency if present
            if 'loan_amount' in loan_data and loan_data['loan_amount']:
                amount_str = loan_data['loan_amount']
                
                # Extract currency (last 3 characters)
                if len(amount_str) >= 3:
                    loan_data['loan_currency'] = amount_str[-3:].strip()
                    
                    # Convert amount to float (handle both , and . as decimal separator)
                    amount_part = amount_str[:-3].strip()
                    amount_part = amount_part.replace(',', '.')  # Convert comma to dot
                    try:
                        loan_data['loan_amount'] = float(amount_part)
                    except ValueError:
                        loan_data['loan_amount'] = None
                        loan_data['loan_currency'] = None
                else:
                    loan_data['loan_amount'] = None
                    loan_data['loan_currency'] = None
            
            # Convert date strings and handle special cases
            date_fields = {
                'deal_date': "%d-%m-%Y",
                'termination_date': "%d-%m-%Y",
                'actual_termination_date': "%d-%m-%Y"
            }
            
            
            for field, fmt in date_fields.items():
                if field in loan_data and loan_data[field]:
                    if isinstance(loan_data[field], str) and loan_data[field].upper() == 'Н/Д':
                        loan_data[field] = None
                    elif isinstance(loan_data[field], str) and loan_data[field] == "31-12-9999":
                        loan_data[field] = None
                        loan_data['original_termination'] = "31-12-9999"  # Store original for status determination
                    else:
                        try:
                            loan_data[field] = datetime.strptime(loan_data[field], fmt).date()
                        except (ValueError, TypeError):
                            loan_data[field] = None
                            
                        
            
            # Create Loan object
            loan = Loan(**loan_data)
            
            
            # Determine status according to business rules
            if not loan.loan_status:
                if hasattr(loan, 'original_termination') and loan.original_termination == "31-12-9999":
                    loan.loan_status = "Active"
                elif loan.termination_date and not loan.actual_termination_date:
                    loan.loan_status = "Active"
                elif loan.termination_date and loan.actual_termination_date:
                    loan.loan_status = "Closed"
                else:
                    loan.loan_status = "Active"
                        
                
            return loan
            
        except Exception as e:
            logger.error(f"Error processing paragraph {paragraph.id}: {str(e)}")
            return None
    
    def process_paragraphs(self, batch_size: int = 10, delay: float = 1.0):
        """Process all unprocessed paragraphs in batches"""
        logger.info("Starting paragraph processing...")
        
        paragraphs = list(self.get_unprocessed_paragraphs())
        total_paragraphs = len(paragraphs)
        
        if total_paragraphs == 0:
            logger.info("No unprocessed paragraphs found")
            return
        
        logger.info(f"Processing {total_paragraphs} paragraphs in batches of {batch_size}")
        
        processed_count = 0
        success_count = 0
        
        for i in range(0, total_paragraphs, batch_size):
            batch = paragraphs[i:i + batch_size]
            
            for paragraph in batch:
                try:
                    loan = self.extract_loan_parameters(paragraph)
                    
                    if loan:
                        self._store_loan(loan)
                        success_count += 1
                        logger.info(f"Successfully processed paragraph {paragraph.id}")
                    else:
                        self._mark_paragraph_error(paragraph.id, "Failed to extract loan parameters")
                    
                    processed_count += 1
                    
                    # Progress update
                    if processed_count % 10 == 0:
                        logger.info(f"Progress: {processed_count}/{total_paragraphs} ({processed_count/total_paragraphs*100:.1f}%)")
                    
                    # Rate limiting
                    time.sleep(delay)
                    
                except Exception as e:
                    logger.error(f"Error processing paragraph {paragraph.id}: {str(e)}")
                    self._mark_paragraph_error(paragraph.id, str(e))
                    processed_count += 1
            
            logger.info(f"Completed batch {i//batch_size + 1}")
        
        logger.info(f"Processing complete. Successfully processed {success_count}/{total_paragraphs} paragraphs")
    
    def _store_loan(self, loan: Loan):
        """Store extracted loan information in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO loans (
                    paragraph_id, bank_name, deal_date, deal_type, loan_type,
                    card_usage, loan_amount, loan_currency, termination_date, loan_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                loan.paragraph_id, loan.bank_name, 
                loan.deal_date.isoformat() if loan.deal_date else None,
                loan.deal_type, loan.loan_type, loan.card_usage,
                loan.loan_amount, loan.loan_currency,
                loan.termination_date.isoformat() if loan.termination_date else None,
                loan.loan_status
            ))
            
            # Mark paragraph as processed
            conn.execute(
                "UPDATE paragraphs SET processed = TRUE WHERE id = ?",
                (loan.paragraph_id,)
            )
            conn.commit()
    
    def _mark_paragraph_error(self, paragraph_id: int, error_message: str):
        """Mark paragraph as processed with error"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE paragraphs SET processed = TRUE, processing_error = ? WHERE id = ?",
                (error_message, paragraph_id)
            )
            conn.commit()
    
    def export_to_csv(self, output_path: str):
        """Export all extracted loan data to CSV"""
        logger.info(f"Exporting loan data to {output_path}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    l.id, l.paragraph_id, l.bank_name, l.deal_date, l.deal_type,
                    l.loan_type, l.card_usage, l.loan_amount, l.loan_currency,
                    l.termination_date, l.loan_status, l.extracted_at,
                    p.page_number
                FROM loans l
                JOIN paragraphs p ON l.paragraph_id = p.id
                ORDER BY l.id
            """)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'id', 'paragraph_id', 'page_number', 'bank_name', 'deal_date',
                    'deal_type', 'loan_type', 'card_usage', 'loan_amount',
                    'loan_currency', 'termination_date', 'loan_status', 'extracted_at'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in cursor:
                    # Convert row to dictionary with proper field mapping
                    row_dict = {
                        'id': row[0],
                        'paragraph_id': row[1],
                        'bank_name': row[2],
                        'deal_date': row[3],
                        'deal_type': row[4],
                        'loan_type': row[5],
                        'card_usage': row[6],
                        'loan_amount': row[7],
                        'loan_currency': row[8],
                        'termination_date': row[9],
                        'loan_status': row[10],
                        'extracted_at': row[11],
                        'page_number': row[12]
                    }
                    writer.writerow(row_dict)
        
        logger.info(f"CSV export completed: {output_path}")
    
    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        with sqlite3.connect(self.db_path) as conn:
            total_paragraphs = conn.execute("SELECT COUNT(*) FROM paragraphs").fetchone()[0]
            processed_paragraphs = conn.execute("SELECT COUNT(*) FROM paragraphs WHERE processed = TRUE").fetchone()[0]
            total_loans = conn.execute("SELECT COUNT(*) FROM loans").fetchone()[0]
            error_paragraphs = conn.execute("SELECT COUNT(*) FROM paragraphs WHERE processing_error IS NOT NULL").fetchone()[0]
            
            return {
                'total_paragraphs': total_paragraphs,
                'processed_paragraphs': processed_paragraphs,
                'total_loans': total_loans,
                'error_paragraphs': error_paragraphs,
                'success_rate': (processed_paragraphs - error_paragraphs) / total_paragraphs if total_paragraphs > 0 else 0
            }

def main():
    """Main execution function"""
    if len(sys.argv) < 4:
        print("Usage: python credit_history_processor.py <pdf_file> <start_page> <end_page> [output_csv]")
        print("Example: python credit_history_processor.py ./data/credit_history.pdf 1 100 output.csv")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    start_page = int(sys.argv[2])
    end_page = int(sys.argv[3])
    output_csv = sys.argv[4] if len(sys.argv) > 4 else f"loans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Check for API key
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("Error: MISTRAL_API_KEY environment variable not set")
        sys.exit(1)
    
    # Initialize processor
    processor = CreditHistoryProcessor(api_key)
    
    try:
        # Step 1: Extract paragraphs from PDF
        logger.info("Step 1: Extracting paragraphs from PDF")
        extracted_count = processor.extract_paragraphs_from_pdf(pdf_file, start_page, end_page)
        
        if extracted_count == 0:
            logger.warning("No paragraphs extracted. Check PDF content and page range.")
            return
        
        # Step 2: Process paragraphs with AI
        logger.info("Step 2: Processing paragraphs with AI")
        processor.process_paragraphs(batch_size=5, delay=1.0)  # Conservative settings
        
        # Step 3: Export to CSV
        logger.info("Step 3: Exporting to CSV")
        processor.export_to_csv(output_csv)
        
        # Show statistics
        stats = processor.get_statistics()
        logger.info("Processing Statistics:")
        logger.info(f"  Total paragraphs: {stats['total_paragraphs']}")
        logger.info(f"  Processed paragraphs: {stats['processed_paragraphs']}")
        logger.info(f"  Extracted loans: {stats['total_loans']}")
        logger.info(f"  Errors: {stats['error_paragraphs']}")
        logger.info(f"  Success rate: {stats['success_rate']:.1%}")
        
        print(f"\nProcessing complete! Results saved to: {output_csv}")
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 