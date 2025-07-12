#!/usr/bin/env python3
"""
Test script to verify AI processing functionality
"""
import os
import sys
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_api_connection():
    """Test the DeepSeek API connection"""
    try:
        from ai_service import openai, DEEPSEEK_API_KEY
        
        print("Testing API connection...")
        print(f"API Key present: {'Yes' if DEEPSEEK_API_KEY else 'No'}")
        
        if not DEEPSEEK_API_KEY:
            print("ERROR: No API key found in environment variables")
            return False
        
        # Test simple API call
        response = openai.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "Hello, respond with 'API test successful'"}],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"API Response: {result}")
        return "API test successful" in result.lower()
        
    except Exception as e:
        print(f"ERROR: API test failed: {str(e)}")
        return False

def test_file_processing():
    """Test file processing functionality"""
    try:
        from services.file_processor import extract_text_from_file
        
        print("\nTesting file processing...")
        
        # Create a simple test file
        test_content = """João Silva
Email: joao@email.com
Telefone: (11) 99999-9999

Experiência:
- Desenvolvedor Python - 3 anos
- Analista de Sistemas - 2 anos

Formação:
- Ciências da Computação - Universidade de São Paulo
"""
        
        test_file = "test_resume.txt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Test text extraction
        text = extract_text_from_file(test_file, 'txt')
        print(f"Extracted text length: {len(text)} characters")
        
        # Clean up
        os.remove(test_file)
        
        return len(text) > 0
        
    except Exception as e:
        print(f"ERROR: File processing test failed: {str(e)}")
        return False

def test_database_connection():
    """Test database connection and candidate retrieval"""
    try:
        from app import app, db
        from models import Candidate
        
        print("\nTesting database connection...")
        
        with app.app_context():
            # Test database connection
            candidate_count = Candidate.query.count()
            print(f"Total candidates in database: {candidate_count}")
            
            # Get pending candidates
            pending_candidates = Candidate.query.filter_by(analysis_status='pending').all()
            print(f"Pending candidates: {len(pending_candidates)}")
            
            # Show some candidate details
            if pending_candidates:
                candidate = pending_candidates[0]
                print(f"Sample candidate: {candidate.name} (ID: {candidate.id})")
                print(f"File path: {candidate.file_path}")
                print(f"File exists: {os.path.exists(candidate.file_path)}")
            
            return True
            
    except Exception as e:
        print(f"ERROR: Database test failed: {str(e)}")
        return False

def test_full_analysis():
    """Test complete analysis workflow"""
    try:
        from app import app, db
        from models import Candidate, Job
        from ai_service import analyze_resume
        
        print("\nTesting full analysis workflow...")
        
        with app.app_context():
            # Get a pending candidate
            candidate = Candidate.query.filter_by(analysis_status='pending').first()
            
            if not candidate:
                print("No pending candidates found for testing")
                return False
            
            print(f"Testing with candidate: {candidate.name}")
            
            # Get job information
            job = candidate.job
            print(f"Job: {job.title}")
            
            # Test analysis
            print("Starting AI analysis...")
            result = analyze_resume(candidate.file_path, candidate.file_type, job)
            
            print(f"Analysis result: {result}")
            return True
            
    except Exception as e:
        print(f"ERROR: Full analysis test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("=== AI Processing Test Suite ===")
    
    tests = [
        ("API Connection", test_api_connection),
        ("File Processing", test_file_processing),
        ("Database Connection", test_database_connection),
        ("Full Analysis", test_full_analysis)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            success = test_func()
            results.append((test_name, success))
            print(f"Result: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"Result: FAIL - {str(e)}")
    
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)