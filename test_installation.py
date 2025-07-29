#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify installation and basic functionality
"""

import sys
import os
from datetime import datetime

def test_imports():
    """Test that all required packages can be imported"""
    print("Testing imports...")
    
    try:
        import PyPDF2
        print("✓ PyPDF2 imported successfully")
    except ImportError as e:
        print(f"✗ PyPDF2 import failed: {e}")
        return False
    
    try:
        import pydantic
        print("✓ Pydantic imported successfully")
    except ImportError as e:
        print(f"✗ Pydantic import failed: {e}")
        return False
    
    try:
        import mistralai
        print("✓ Mistral AI imported successfully")
    except ImportError as e:
        print(f"✗ Mistral AI import failed: {e}")
        return False
    
    try:
        import sqlite3
        print("✓ SQLite3 imported successfully")
    except ImportError as e:
        print(f"✗ SQLite3 import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        import config
        print("✓ Configuration loaded successfully")
        print(f"  - Database path: {config.DATABASE_PATH}")
        print(f"  - Mistral model: {config.MISTRAL_MODEL}")
        print(f"  - Batch size: {config.BATCH_SIZE}")
        return True
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False

def test_api_key():
    """Test API key availability"""
    print("\nTesting API key...")
    
    api_key = os.environ.get("MISTRAL_API_KEY")
    if api_key:
        print("✓ MISTRAL_API_KEY environment variable is set")
        print(f"  - Key length: {len(api_key)} characters")
        return True
    else:
        print("✗ MISTRAL_API_KEY environment variable is not set")
        print("  Please set it with: export MISTRAL_API_KEY='your_key_here'")
        return False

def test_database_creation():
    """Test database creation"""
    print("\nTesting database creation...")
    
    try:
        import sqlite3
        from config import DATABASE_PATH
        
        # Create a test database
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    test_data TEXT
                )
            """)
            conn.execute("INSERT INTO test_table (test_data) VALUES (?)", ("test",))
            result = conn.execute("SELECT test_data FROM test_table").fetchone()
            
            if result and result[0] == "test":
                print("✓ Database creation and operations successful")
                # Clean up
                conn.execute("DROP TABLE test_table")
                return True
            else:
                print("✗ Database test failed")
                return False
                
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_mistral_connection():
    """Test Mistral API connection"""
    print("\nTesting Mistral API connection...")
    
    try:
        from mistralai import Mistral
        from config import MISTRAL_MODEL
        
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            print("✗ Skipping API test - no API key")
            return False
        
        client = Mistral(api_key=api_key)
        
        # Test with a simple request
        response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=[
                {"role": "user", "content": "Say 'Hello, World!'"}
            ],
            max_tokens=10
        )
        
        if response.choices and response.choices[0].message.content:
            print("✓ Mistral API connection successful")
            print(f"  - Response: {response.choices[0].message.content}")
            return True
        else:
            print("✗ Mistral API test failed - no response")
            return False
            
    except Exception as e:
        print(f"✗ Mistral API test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Credit History Processor - Installation Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_api_key,
        test_database_creation,
        test_mistral_connection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Installation is complete.")
        print("\nYou can now run the credit history processor:")
        print("python credit_history_processor.py <pdf_file> <start_page> <end_page>")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nCommon solutions:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Set API key: export MISTRAL_API_KEY='your_key_here'")
        print("3. Check file permissions for database creation")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 