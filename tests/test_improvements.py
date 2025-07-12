"""
Test the improved AI analysis system
"""
import os
import sys
import logging
from app import app, db
from models import Job, Candidate

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_improved_system():
    """Test the improved analysis system"""
    
    with app.app_context():
        # Get job and candidates
        job = Job.query.first()
        if not job:
            print("❌ No job found")
            return
            
        # Get pending candidates
        pending_candidates = Candidate.query.filter_by(analysis_status='pending').limit(5).all()
        
        if not pending_candidates:
            print("❌ No pending candidates found")
            return
            
        print(f"✅ Found {len(pending_candidates)} pending candidates")
        
        # Test parallel processing
        candidate_ids = [c.id for c in pending_candidates]
        
        print(f"🚀 Testing parallel processing with {len(candidate_ids)} candidates")
        
        # Start parallel analysis
        from parallel_processor import start_parallel_analysis
        thread = start_parallel_analysis(candidate_ids)
        
        print("✅ Parallel analysis started")
        
        # Monitor progress
        import time
        from parallel_processor import get_processing_status
        
        for i in range(30):  # Monitor for 30 seconds
            status = get_processing_status(candidate_ids)
            print(f"Status: {status}")
            
            if status['processing'] == 0 and status['pending'] == 0:
                print("🎉 All candidates processed!")
                break
                
            time.sleep(1)
        
        # Check results
        print("\n📊 Final Results:")
        for candidate in pending_candidates:
            db.session.refresh(candidate)
            print(f"  - {candidate.name}: {candidate.analysis_status}, Score: {candidate.ai_score}")

if __name__ == "__main__":
    test_improved_system()