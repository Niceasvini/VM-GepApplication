#!/usr/bin/env python3
"""
Test the bulk upload frontend functionality
"""
import os
import json
import tempfile
import logging
from werkzeug.test import Client
from werkzeug.wrappers import Response

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://postgres.bndkpowgvagtlxwmthma:5585858Vini%40@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'

from app import app
from models import Job, Candidate

def test_bulk_upload_endpoint():
    """Test the bulk upload endpoint directly"""
    print("=== TESTING BULK UPLOAD ENDPOINT ===")
    
    with app.test_client() as client:
        # First login (we need to be authenticated)
        login_response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        print(f"Login response: {login_response.status_code}")
        
        # Create test files
        test_files = [
            ('Test1.txt', 'João Silva\nDesenvolvedor Python\n3 anos'),
            ('Test2.txt', 'Maria Santos\nDesenvolvedor Full Stack\n4 anos'),
            ('Test3.txt', 'Pedro Costa\nEngenheiro de Software\n5 anos')
        ]
        
        # Prepare files for upload
        files_data = []
        for filename, content in test_files:
            files_data.append(('files', (filename, content.encode('utf-8'), 'text/plain')))
        
        print(f"Uploading {len(files_data)} files...")
        
        # Test the bulk upload endpoint
        response = client.post('/bulk-upload/1', 
                             data=dict(files_data),
                             content_type='multipart/form-data')
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.get_data(as_text=True)}")
        
        if response.status_code == 200:
            try:
                data = json.loads(response.get_data(as_text=True))
                print(f"Success: {data.get('success')}")
                print(f"Processed: {data.get('processed_count')}")
                print(f"Candidate IDs: {data.get('candidate_ids')}")
                print(f"Errors: {data.get('errors')}")
                
                if data.get('success'):
                    print("✅ BULK UPLOAD ENDPOINT WORKING!")
                    return True
                else:
                    print("❌ BULK UPLOAD FAILED")
                    return False
            except json.JSONDecodeError:
                print("❌ Invalid JSON response")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False

def test_bulk_upload_page():
    """Test if the bulk upload page loads correctly"""
    print("\n=== TESTING BULK UPLOAD PAGE ===")
    
    with app.test_client() as client:
        # Login first
        client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        
        # Test the bulk upload page
        response = client.get('/jobs/1/bulk-upload')
        print(f"Page response: {response.status_code}")
        
        if response.status_code == 200:
            html = response.get_data(as_text=True)
            
            # Check for key elements
            checks = [
                'bulk-upload-form' in html,
                'bulk-files' in html,
                'Iniciar Processamento' in html,
                '/bulk-upload/1' in html
            ]
            
            print(f"Form present: {checks[0]}")
            print(f"File input present: {checks[1]}")  
            print(f"Submit button present: {checks[2]}")
            print(f"Correct action URL: {checks[3]}")
            
            if all(checks):
                print("✅ BULK UPLOAD PAGE WORKING!")
                return True
            else:
                print("❌ BULK UPLOAD PAGE MISSING ELEMENTS")
                return False
        else:
            print(f"❌ Page load failed: {response.status_code}")
            return False

if __name__ == "__main__":
    with app.app_context():
        # Test both page and endpoint
        page_ok = test_bulk_upload_page()
        endpoint_ok = test_bulk_upload_endpoint()
        
        if page_ok and endpoint_ok:
            print("\n🎉 ALL TESTS PASSED - PROBLEM IS IN JAVASCRIPT!")
        else:
            print("\n❌ BACKEND ISSUES FOUND")