# -*- coding: utf-8 -*-
"""
Configuration file for Credit History Processor
"""

import os
from typing import List

# Database configuration
DATABASE_PATH = os.getenv("CREDIT_DB_PATH", "credit_history.db")

# Mistral AI configuration
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
MISTRAL_TEMPERATURE = float(os.getenv("MISTRAL_TEMPERATURE", "0"))

# Processing configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "5"))
API_DELAY = float(os.getenv("API_DELAY", "1.0"))  # Delay between API calls in seconds
MIN_PARAGRAPH_LENGTH = int(os.getenv("MIN_PARAGRAPH_LENGTH", "50"))

# PDF processing configuration
HEADER_FOOTER_Y_MIN = int(os.getenv("HEADER_FOOTER_Y_MIN", "50"))
HEADER_FOOTER_Y_MAX = int(os.getenv("HEADER_FOOTER_Y_MAX", "720"))

# Regex patterns for paragraph extraction
PARAGRAPH_PATTERNS = [
    r'\d+\.\s+(.+?)\s+-\s+Договор займа\s*\(кредита\)\s*-\s*(.+?)(?=\s*\d+\.|\Z)',
    r'\d+\.\s+(.+?)\s*-\s*Договор займа\s*\(кредита\)\s*(.+?)(?=\s*\d+\.|\Z)',
    r'(\d+\.\s+[А-Я][^.]*?банк[^.]*?)(.+?)(?=\d+\.|\Z)',
    r'(\d+\.\s+[А-Я][^.]*?кредит[^.]*?)(.+?)(?=\d+\.|\Z)',
    # Add more patterns as needed
]

# AI prompt template
AI_PROMPT_TEMPLATE = """Extract loan information as JSON with these exact field names: 
bank_name, deal_date (DD-MM-YYYY or null), deal_type, loan_type, 
card_usage (true/false or null), loan_amount (number or null), 
loan_currency (3 letters or null), termination_date (DD-MM-YYYY or null).
If a field cannot be determined, use null. Format must be valid JSON.

Example:
{
    "bank_name": "Bank Name",
    "deal_date": "01-01-2023",
    "deal_type": "Loan Type",
    "loan_type": "Loan Category",
    "card_usage": true,
    "loan_amount": 10000,
    "loan_currency": "RUB",
    "termination_date": "31-12-2025"
}"""

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "credit_processor.log")

# Output configuration
DEFAULT_OUTPUT_DIR = os.getenv("DEFAULT_OUTPUT_DIR", "./output")
CSV_ENCODING = os.getenv("CSV_ENCODING", "utf-8") 