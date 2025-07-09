#!/usr/bin/env python3
"""
Process all pending candidates and show real-time progress
"""
import time
import threading
from datetime import datetime
from app import app, db
from models import Candidate
from simple_processor import process_candidate_simple

def process_all_with_progress():
    """Process all pending candidates with real-time progress"""
    with app.app_context():
        # Get all pending candidates
        candidates = Candidate.query.filter_by(analysis_status='pending').all()
        
        if not candidates:
            print("✓ No pending candidates found")
            return
        
        print(f"🚀 Starting processing of {len(candidates)} candidates...")
        print("=" * 60)
        
        success_count = 0
        failed_count = 0
        
        for i, candidate in enumerate(candidates, 1):
            print(f"\n[{i}/{len(candidates)}] Processing: {candidate.name}")
            print(f"Job: {candidate.job.title}")
            print(f"File: {candidate.filename}")
            
            start_time = time.time()
            
            try:
                # Process candidate
                success = process_candidate_simple(candidate.id)
                
                end_time = time.time()
                duration = end_time - start_time
                
                if success:
                    # Get updated candidate data
                    candidate = Candidate.query.get(candidate.id)
                    print(f"✓ SUCCESS - Score: {candidate.ai_score}/10 (took {duration:.1f}s)")
                    success_count += 1
                else:
                    print(f"✗ FAILED (took {duration:.1f}s)")
                    failed_count += 1
                    
            except Exception as e:
                print(f"✗ ERROR: {str(e)}")
                failed_count += 1
            
            # Show progress
            progress = (i / len(candidates)) * 100
            print(f"Progress: {progress:.1f}% ({i}/{len(candidates)})")
            print("-" * 40)
        
        print("\n" + "=" * 60)
        print("🎉 PROCESSING COMPLETE!")
        print(f"✓ Successful: {success_count}")
        print(f"✗ Failed: {failed_count}")
        print(f"📊 Success rate: {(success_count/len(candidates)*100):.1f}%")
        
        # Show results summary
        print("\n📋 RESULTS SUMMARY:")
        print("=" * 60)
        
        processed_candidates = Candidate.query.filter_by(analysis_status='completed').all()
        processed_candidates.sort(key=lambda x: x.ai_score or 0, reverse=True)
        
        for candidate in processed_candidates:
            print(f"{candidate.name}: {candidate.ai_score}/10 - {candidate.job.title}")
        
        return success_count, failed_count

def run_background_processing():
    """Run processing in background thread"""
    def worker():
        try:
            process_all_with_progress()
        except Exception as e:
            print(f"Background processing error: {e}")
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    process_all_with_progress()