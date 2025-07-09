#!/usr/bin/env python3
"""
Background processor for AI analysis with improved performance
"""
import threading
import time
import logging
from datetime import datetime
from app import app, db
from models import Candidate
from ai_service import analyze_resume

# Global variables to track processing
processing_threads = {}
processing_status = {}

def process_candidate_background(candidate_id):
    """
    Process a single candidate in the background
    """
    try:
        with app.app_context():
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                logging.error(f"Candidate {candidate_id} not found")
                return
            
            # Update status to processing
            candidate.analysis_status = 'processing'
            db.session.commit()
            
            logging.info(f"Starting background analysis for candidate {candidate_id}: {candidate.name}")
            
            # Perform AI analysis
            analysis_result = analyze_resume(candidate.file_path, candidate.file_type, candidate.job)
            
            # Update candidate with results
            candidate.ai_score = analysis_result['score']
            candidate.ai_summary = analysis_result['summary']
            candidate.ai_analysis = analysis_result['analysis']
            candidate.set_skills_list(analysis_result['skills'])
            candidate.analysis_status = 'completed'
            candidate.analyzed_at = datetime.utcnow()
            
            db.session.commit()
            
            logging.info(f"Background analysis completed for candidate {candidate_id} with score {analysis_result['score']}")
            
    except Exception as e:
        logging.error(f"Error in background processing for candidate {candidate_id}: {str(e)}")
        try:
            with app.app_context():
                candidate = Candidate.query.get(candidate_id)
                if candidate:
                    candidate.analysis_status = 'failed'
                    candidate.ai_summary = f'Erro na análise: {str(e)}'
                    db.session.commit()
        except Exception as db_error:
            logging.error(f"Failed to update candidate status: {str(db_error)}")
    
    finally:
        # Remove from processing threads
        if candidate_id in processing_threads:
            del processing_threads[candidate_id]

def start_background_analysis(candidate_ids):
    """
    Start background analysis for multiple candidates
    """
    started_count = 0
    
    for candidate_id in candidate_ids:
        if candidate_id not in processing_threads:
            # Create and start thread
            thread = threading.Thread(
                target=process_candidate_background,
                args=(candidate_id,),
                daemon=True
            )
            thread.start()
            processing_threads[candidate_id] = thread
            started_count += 1
            
            # Small delay to prevent overwhelming the API
            time.sleep(0.5)
    
    logging.info(f"Started {started_count} background analysis threads")
    return started_count

def get_processing_status(candidate_ids):
    """
    Get processing status for candidates
    """
    with app.app_context():
        status_counts = {
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0
        }
        
        for candidate_id in candidate_ids:
            candidate = Candidate.query.get(candidate_id)
            if candidate:
                status = candidate.analysis_status
                if status in status_counts:
                    status_counts[status] += 1
        
        return status_counts

def cleanup_stale_threads():
    """
    Clean up finished threads
    """
    completed_threads = []
    
    for candidate_id, thread in processing_threads.items():
        if not thread.is_alive():
            completed_threads.append(candidate_id)
    
    for candidate_id in completed_threads:
        del processing_threads[candidate_id]
    
    return len(completed_threads)

def get_active_threads():
    """
    Get count of active processing threads
    """
    return len(processing_threads)

if __name__ == "__main__":
    # Test the background processor
    with app.app_context():
        pending_candidates = Candidate.query.filter_by(analysis_status='pending').all()
        candidate_ids = [c.id for c in pending_candidates]
        
        if candidate_ids:
            print(f"Starting background processing for {len(candidate_ids)} candidates")
            start_background_analysis(candidate_ids)
            
            # Monitor progress
            while get_active_threads() > 0:
                status = get_processing_status(candidate_ids)
                print(f"Status: {status}")
                time.sleep(5)
            
            print("All processing completed!")
        else:
            print("No pending candidates found")