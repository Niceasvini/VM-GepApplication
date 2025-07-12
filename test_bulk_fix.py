"""
Test the fixed bulk upload functionality
"""
import os
import sys
import logging
from app import app, db
from models import Job, Candidate

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_bulk_upload_fix():
    """Test the fixed bulk upload database handling"""
    
    with app.app_context():
        # Get or create a test job
        job = Job.query.first()
        if not job:
            print("❌ No job found. Create a job first.")
            return
            
        print(f"✅ Testing with job: {job.title}")
        
        # Test database connection
        try:
            test_candidate = Candidate(
                name="Test Candidate",
                email="test@example.com",
                phone="123456789",
                filename="test.pdf",
                file_path="/tmp/test.pdf",
                file_type="pdf",
                job_id=job.id,
                status='pending',
                analysis_status='pending'
            )
            
            db.session.add(test_candidate)
            db.session.flush()  # Get ID without committing
            candidate_id = test_candidate.id
            db.session.commit()
            
            print(f"✅ Database connection working. Test candidate ID: {candidate_id}")
            
            # Clean up
            db.session.delete(test_candidate)
            db.session.commit()
            print("✅ Test cleanup completed")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            db.session.rollback()
            
        # Test API endpoint
        with app.test_client() as client:
            response = client.get(f'/api/jobs/{job.id}/processing_status')
            if response.status_code == 200:
                print("✅ API endpoint working")
                data = response.get_json()
                print(f"   Status counts: {data.get('status_counts', {})}")
            else:
                print(f"❌ API endpoint failed: {response.status_code}")

if __name__ == "__main__":
    test_bulk_upload_fix()