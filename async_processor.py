#!/usr/bin/env python3
"""
Optimized async processor for AI analysis with better error handling
"""
import os
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://postgres.bndkpowgvagtlxwmthma:5585858Vini%40@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'

from app import app, db
from models import Candidate
from file_processor import extract_text_from_file

# Configure OpenAI client with shorter timeout
client = OpenAI(
    api_key="sk-08e53165834948c8b96fe8ec44a12baf",
    base_url="https://api.deepseek.com/v1",
    timeout=15  # Shorter timeout
)

def get_db_session():
    """Get a database session for the current thread"""
    return db.session

def process_single_candidate(candidate_id):
    """
    Process a single candidate's resume with AI analysis
    This function runs in a separate thread
    """
    try:
        with app.app_context():
            candidate = db.session.get(Candidate, candidate_id)
            if not candidate:
                print(f"Candidate {candidate_id} not found")
                return False
            
            print(f"Processing {candidate.name}...")
            
            # Update status
            candidate.analysis_status = 'processing'
            db.session.commit()
            
            # Extract resume text
            resume_text = extract_text_from_file(candidate.file_path, candidate.file_type)
            
            # Truncate text for faster processing
            if len(resume_text) > 1000:
                resume_text = resume_text[:1000]
            
            # STEP 1: Get quick score with very simple prompt
            try:
                score_response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{
                        "role": "user",
                        "content": f"Rate this resume for '{candidate.job.title}' job from 0-10. Only respond with number like: 7.5\n\nResume: {resume_text[:400]}"
                    }],
                    max_tokens=5,
                    temperature=0.1
                )
                
                score_text = score_response.choices[0].message.content.strip()
                
                # Extract numeric score
                import re
                score_match = re.search(r'(\d+\.?\d*)', score_text)
                if score_match:
                    score = float(score_match.group(1))
                    if score > 10:
                        score = score / 10  # Handle cases like 85 -> 8.5
                else:
                    score = 5.0
                
                print(f"  Score: {score}")
                
            except Exception as e:
                print(f"  Score error: {e}")
                score = 5.0
            
            # STEP 2: Get brief analysis
            try:
                analysis_response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{
                        "role": "user",
                        "content": f"Brief summary of {candidate.name} for {candidate.job.title} position (max 50 words):\n\n{resume_text[:400]}"
                    }],
                    max_tokens=100,
                    temperature=0.3
                )
                
                analysis = analysis_response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"  Analysis error: {e}")
                analysis = f"Candidato para {candidate.job.title}. Score: {score}/10"
            
            # Update candidate in database
            candidate.ai_score = score
            candidate.ai_summary = analysis
            candidate.ai_analysis = f"Análise automática: Score {score}/10. {analysis}"
            candidate.analysis_status = 'completed'
            candidate.analyzed_at = datetime.utcnow()
            
            db.session.commit()
            
            print(f"✓ Completed: {candidate.name} - Score: {score}")
            return True
            
    except Exception as e:
        print(f"✗ Error processing candidate {candidate_id}: {str(e)}")
        
        # Mark as failed
        try:
            with app.app_context():
                candidate = db.session.get(Candidate, candidate_id)
                if candidate:
                    candidate.analysis_status = 'failed'
                    candidate.ai_summary = f'Processing error: {str(e)}'
                    candidate.ai_score = 0.0
                    db.session.commit()
        except:
            pass
        
        return False

def process_candidates_parallel(candidate_ids, max_workers=5):
    """
    Process multiple candidates in parallel using ThreadPoolExecutor
    
    Args:
        candidate_ids: List of candidate IDs to process
        max_workers: Maximum number of parallel threads (default: 5)
    
    Returns:
        Dictionary with success/failure counts
    """
    results = {'success': 0, 'failed': 0}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {executor.submit(process_single_candidate, cid): cid for cid in candidate_ids}
        
        # Process results as they complete
        for future in as_completed(futures):
            candidate_id = futures[future]
            try:
                success = future.result()
                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
                print(f"Exception for candidate {candidate_id}: {e}")
    
    return results

def start_background_processing(candidate_ids):
    """
    Start background processing of candidates in a separate thread
    This doesn't block the main application
    """
    def background_worker():
        print(f"Starting background processing for {len(candidate_ids)} candidates...")
        results = process_candidates_parallel(candidate_ids, max_workers=3)
        print(f"Background processing completed: {results['success']} success, {results['failed']} failed")
    
    thread = threading.Thread(target=background_worker, daemon=True)
    thread.start()
    return thread

def get_processing_status(candidate_ids):
    """
    Get the current processing status of candidates
    
    Returns:
        Dictionary with status counts
    """
    try:
        with app.app_context():
            candidates = Candidate.query.filter(Candidate.id.in_(candidate_ids)).all()
            
            status_counts = {
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0
            }
            
            for candidate in candidates:
                status_counts[candidate.analysis_status] += 1
            
            return status_counts
    except Exception as e:
        print(f"Error getting processing status: {e}")
        return {'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0}

def cleanup_stale_processing():
    """
    Clean up candidates that have been stuck in 'processing' status for too long
    This should be called periodically to handle crashed processes
    """
    try:
        with app.app_context():
            # Find candidates that have been processing for more than 5 minutes
            from datetime import datetime, timedelta
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            
            stale_candidates = Candidate.query.filter(
                Candidate.analysis_status == 'processing',
                Candidate.analyzed_at < cutoff_time
            ).all()
            
            for candidate in stale_candidates:
                candidate.analysis_status = 'pending'
            
            db.session.commit()
            
            if stale_candidates:
                print(f"Cleaned up {len(stale_candidates)} stale processing candidates")
                
    except Exception as e:
        print(f"Error cleaning up stale processing: {e}")

if __name__ == "__main__":
    # Test processing
    with app.app_context():
        candidates = Candidate.query.all()
        if candidates:
            candidate_ids = [c.id for c in candidates]
            print(f"Processing {len(candidate_ids)} candidates...")
            
            # Clean up any stale processing
            cleanup_stale_processing()
            
            # Process candidates
            results = process_candidates_parallel(candidate_ids, max_workers=2)
            print(f"Results: {results}")
        else:
            print("No candidates found")