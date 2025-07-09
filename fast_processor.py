#!/usr/bin/env python3
"""
Fast parallel processor for AI analysis with optimized performance
"""
import threading
import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from app import app, db
from models import Candidate
from ai_service import analyze_resume

# Configuration
MAX_WORKERS = 4  # Reduced for better performance
DELAY_BETWEEN_REQUESTS = 0.3  # Small delay to prevent API overload

def process_candidate_fast(candidate_id):
    """
    Process a single candidate with optimized speed
    """
    try:
        with app.app_context():
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                logging.error(f"Candidate {candidate_id} not found")
                return False
            
            # Update status to processing
            candidate.analysis_status = 'processing'
            db.session.commit()
            
            logging.info(f"Fast analysis started for candidate {candidate_id}: {candidate.name}")
            
            # Perform optimized AI analysis
            start_time = time.time()
            analysis_result = analyze_resume(candidate.file_path, candidate.file_type, candidate.job)
            end_time = time.time()
            
            # Update candidate with results
            candidate.ai_score = analysis_result['score']
            candidate.ai_summary = analysis_result['summary']
            candidate.ai_analysis = analysis_result['analysis']
            candidate.set_skills_list(analysis_result['skills'])
            candidate.analysis_status = 'completed'
            candidate.analyzed_at = datetime.utcnow()
            
            db.session.commit()
            
            processing_time = round(end_time - start_time, 2)
            logging.info(f"Fast analysis completed for candidate {candidate_id} in {processing_time}s with score {analysis_result['score']}")
            
            return True
            
    except Exception as e:
        logging.error(f"Error in fast processing for candidate {candidate_id}: {str(e)}")
        try:
            with app.app_context():
                candidate = Candidate.query.get(candidate_id)
                if candidate:
                    candidate.analysis_status = 'failed'
                    candidate.ai_summary = f'Erro na análise: {str(e)}'
                    db.session.commit()
        except Exception as db_error:
            logging.error(f"Failed to update candidate status: {str(db_error)}")
        return False

def process_candidates_parallel_fast(candidate_ids):
    """
    Process multiple candidates in parallel with optimized performance
    """
    if not candidate_ids:
        return {'success': 0, 'failed': 0, 'total': 0}
    
    logging.info(f"Starting fast parallel processing of {len(candidate_ids)} candidates with {MAX_WORKERS} workers")
    
    success_count = 0
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_candidate = {
            executor.submit(process_candidate_fast, candidate_id): candidate_id 
            for candidate_id in candidate_ids
        }
        
        # Process results as they complete
        for future in as_completed(future_to_candidate):
            candidate_id = future_to_candidate[future]
            try:
                result = future.result()
                if result:
                    success_count += 1
                    logging.info(f"Successfully processed candidate {candidate_id}")
                else:
                    failed_count += 1
                    logging.error(f"Failed to process candidate {candidate_id}")
            except Exception as e:
                failed_count += 1
                logging.error(f"Exception processing candidate {candidate_id}: {str(e)}")
            
            # Small delay between processing completions
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    result = {
        'success': success_count,
        'failed': failed_count,
        'total': len(candidate_ids)
    }
    
    logging.info(f"Fast parallel processing completed: {result}")
    return result

def start_fast_background_processing(candidate_ids):
    """
    Start fast background processing in a separate thread
    """
    def fast_background_worker():
        try:
            logging.info(f"Fast background processing started for {len(candidate_ids)} candidates")
            process_candidates_parallel_fast(candidate_ids)
            logging.info("Fast background processing completed")
        except Exception as e:
            logging.error(f"Fast background processing error: {str(e)}")
    
    # Start in daemon thread
    thread = threading.Thread(target=fast_background_worker, daemon=True)
    thread.start()
    
    return thread

def get_fast_processing_status(candidate_ids):
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

def reset_stale_candidates():
    """
    Reset candidates that are stuck in processing status
    """
    with app.app_context():
        # Find candidates stuck in processing for more than 10 minutes
        from datetime import datetime, timedelta
        ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
        
        stale_candidates = Candidate.query.filter(
            Candidate.analysis_status == 'processing',
            Candidate.uploaded_at < ten_minutes_ago
        ).all()
        
        reset_count = 0
        for candidate in stale_candidates:
            candidate.analysis_status = 'pending'
            reset_count += 1
            logging.info(f"Reset stale candidate {candidate.id}: {candidate.name}")
        
        db.session.commit()
        return reset_count

if __name__ == "__main__":
    # Test the fast processor
    with app.app_context():
        # Reset any stale candidates first
        reset_count = reset_stale_candidates()
        print(f"Reset {reset_count} stale candidates")
        
        # Get pending candidates
        pending_candidates = Candidate.query.filter_by(analysis_status='pending').all()
        candidate_ids = [c.id for c in pending_candidates]
        
        if candidate_ids:
            print(f"Starting fast processing for {len(candidate_ids)} candidates")
            
            # Start fast processing
            start_time = time.time()
            result = process_candidates_parallel_fast(candidate_ids)
            end_time = time.time()
            
            total_time = round(end_time - start_time, 2)
            print(f"Fast processing completed in {total_time}s")
            print(f"Results: {result}")
            
            # Show final results
            candidates = Candidate.query.filter(Candidate.id.in_(candidate_ids)).all()
            for candidate in candidates:
                print(f"{candidate.name}: {candidate.analysis_status}, Score: {candidate.ai_score}")
        else:
            print("No pending candidates found")