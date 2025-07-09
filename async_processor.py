import threading
import time
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from app import app, db
from models import Candidate
from ai_service import analyze_resume
from file_processor import extract_text_from_file

# Thread-local storage for database connections
thread_local = threading.local()

def get_db_session():
    """Get a database session for the current thread"""
    if not hasattr(thread_local, 'session'):
        thread_local.session = db.session
    return thread_local.session

def process_single_candidate(candidate_id):
    """
    Process a single candidate's resume with AI analysis
    This function runs in a separate thread
    """
    try:
        with app.app_context():
            # Get fresh candidate record
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                logging.error(f"Candidate {candidate_id} not found")
                return False
            
            # Check if already processed
            if candidate.analysis_status == 'completed':
                logging.info(f"Candidate {candidate_id} already processed")
                return True
            
            # Update status to processing
            candidate.analysis_status = 'processing'
            db.session.commit()
            
            logging.info(f"Starting AI analysis for candidate {candidate_id}: {candidate.name}")
            
            # Get job information
            job = candidate.job
            
            # Analyze resume
            analysis_result = analyze_resume(candidate.file_path, candidate.file_type, job)
            
            # Update candidate with results
            candidate.ai_score = analysis_result['score']
            candidate.ai_summary = analysis_result['summary']
            candidate.ai_analysis = analysis_result['analysis']
            candidate.set_skills_list(analysis_result['skills'])
            candidate.analysis_status = 'completed'
            candidate.analyzed_at = datetime.utcnow()
            
            db.session.commit()
            
            logging.info(f"Successfully analyzed candidate {candidate_id}: {candidate.name} - Score: {candidate.ai_score}")
            return True
            
    except Exception as e:
        logging.error(f"Error processing candidate {candidate_id}: {str(e)}")
        try:
            with app.app_context():
                candidate = Candidate.query.get(candidate_id)
                if candidate:
                    candidate.analysis_status = 'failed'
                    db.session.commit()
        except Exception as db_error:
            logging.error(f"Error updating candidate status: {str(db_error)}")
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
    if not candidate_ids:
        return {'success': 0, 'failed': 0, 'total': 0}
    
    logging.info(f"Starting parallel processing of {len(candidate_ids)} candidates with {max_workers} workers")
    
    results = {'success': 0, 'failed': 0, 'total': len(candidate_ids)}
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_candidate = {
            executor.submit(process_single_candidate, candidate_id): candidate_id 
            for candidate_id in candidate_ids
        }
        
        # Process completed tasks
        for future in as_completed(future_to_candidate):
            candidate_id = future_to_candidate[future]
            try:
                success = future.result()
                if success:
                    results['success'] += 1
                    logging.info(f"Successfully processed candidate {candidate_id}")
                else:
                    results['failed'] += 1
                    logging.error(f"Failed to process candidate {candidate_id}")
            except Exception as e:
                results['failed'] += 1
                logging.error(f"Exception processing candidate {candidate_id}: {str(e)}")
    
    logging.info(f"Parallel processing completed. Success: {results['success']}, Failed: {results['failed']}")
    return results

def start_background_processing(candidate_ids):
    """
    Start background processing of candidates in a separate thread
    This doesn't block the main application
    """
    def background_worker():
        try:
            logging.info(f"Background processing started for {len(candidate_ids)} candidates")
            print(f"DEBUG: Background processing started for {len(candidate_ids)} candidates")
            process_candidates_parallel(candidate_ids)
            logging.info("Background processing completed")
            print("DEBUG: Background processing completed")
        except Exception as e:
            logging.error(f"Background processing error: {str(e)}")
            print(f"DEBUG: Background processing error: {str(e)}")
    
    # Start background thread
    background_thread = threading.Thread(target=background_worker)
    background_thread.daemon = True  # Thread will die when main program exits
    background_thread.start()
    
    logging.info("Background processing thread started")
    return background_thread

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
        logging.error(f"Error getting processing status: {str(e)}")
        return {'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0}

def cleanup_stale_processing():
    """
    Clean up candidates that have been stuck in 'processing' status for too long
    This should be called periodically to handle crashed processes
    """
    try:
        with app.app_context():
            # Find candidates that have been processing for more than 10 minutes
            cutoff_time = datetime.utcnow() - timedelta(minutes=10)
            
            stale_candidates = Candidate.query.filter(
                Candidate.analysis_status == 'processing',
                Candidate.uploaded_at < cutoff_time
            ).all()
            
            for candidate in stale_candidates:
                candidate.analysis_status = 'failed'
                logging.warning(f"Marked candidate {candidate.id} as failed due to stale processing")
            
            if stale_candidates:
                db.session.commit()
                logging.info(f"Cleaned up {len(stale_candidates)} stale processing candidates")
                
    except Exception as e:
        logging.error(f"Error cleaning up stale processing: {str(e)}")