"""
Fast parallel processor for AI analysis with optimized performance
"""
import os
import threading
import time
import logging
from datetime import datetime
from app import app, db
from models import Candidate
from services.ai_service import analyze_resume

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_candidate_fast(candidate_id):
    """
    Process a single candidate with optimized speed
    """
    try:
        with app.app_context():
            candidate = db.session.get(Candidate, candidate_id)
            if not candidate:
                return False
            
            # Update status
            candidate.analysis_status = 'processing'
            db.session.commit()
            
            # Analyze with AI
            result = analyze_resume(candidate.file_path, candidate.file_type, candidate.job)
            
            if result:
                candidate.ai_score = result.get('score', 0)
                candidate.ai_summary = result.get('summary', '')
                candidate.ai_analysis = result.get('analysis', '')
                candidate.extracted_skills = result.get('skills', '[]')
                candidate.analysis_status = 'completed'
                candidate.analyzed_at = datetime.utcnow()
                db.session.commit()
                return True
            else:
                candidate.analysis_status = 'failed'
                db.session.commit()
                return False
                
    except Exception as e:
        logger.error(f"Error processing candidate {candidate_id}: {str(e)}")
        try:
            with app.app_context():
                candidate = db.session.get(Candidate, candidate_id)
                if candidate:
                    candidate.analysis_status = 'failed'
                    db.session.commit()
        except:
            pass
        return False

def process_candidates_parallel_fast(candidate_ids):
    """
    Process multiple candidates in parallel with optimized performance
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    logger.info(f"🚀 Starting fast parallel processing of {len(candidate_ids)} candidates")
    
    success_count = 0
    failed_count = 0
    
    # Use smaller thread pool for stability
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all tasks
        future_to_candidate = {
            executor.submit(process_candidate_fast, cid): cid 
            for cid in candidate_ids
        }
        
        # Process completed tasks
        for future in as_completed(future_to_candidate):
            candidate_id = future_to_candidate[future]
            try:
                result = future.result()
                if result:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Exception in processing candidate {candidate_id}: {str(e)}")
                failed_count += 1
    
    logger.info(f"🎉 Fast processing completed: {success_count} success, {failed_count} failed")
    
    return {
        'success': success_count,
        'failed': failed_count,
        'total': len(candidate_ids)
    }

def start_fast_background_processing(candidate_ids):
    """
    Start fast background processing in a separate thread
    """
    def fast_background_worker():
        try:
            process_candidates_parallel_fast(candidate_ids)
        except Exception as e:
            logger.error(f"Error in fast background processing: {str(e)}")
    
    thread = threading.Thread(target=fast_background_worker)
    thread.daemon = True
    thread.start()
    
    return thread

def get_fast_processing_status(candidate_ids):
    """
    Get processing status for candidates
    """
    try:
        with app.app_context():
            status_counts = {
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0
            }
            
            for cid in candidate_ids:
                candidate = db.session.get(Candidate, cid)
                if candidate:
                    status = candidate.analysis_status
                    if status in status_counts:
                        status_counts[status] += 1
            
            return status_counts
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        return {'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0}

def reset_stale_candidates():
    """
    Reset candidates that are stuck in processing status
    """
    try:
        with app.app_context():
            # Find candidates stuck in processing for more than 5 minutes
            from datetime import datetime, timedelta
            threshold = datetime.utcnow() - timedelta(minutes=5)
            
            stale_candidates = Candidate.query.filter(
                Candidate.analysis_status == 'processing',
                Candidate.analyzed_at < threshold
            ).all()
            
            for candidate in stale_candidates:
                candidate.analysis_status = 'pending'
                db.session.commit()
                logger.info(f"Reset stale candidate: {candidate.id}")
            
            return len(stale_candidates)
    except Exception as e:
        logger.error(f"Error resetting stale candidates: {str(e)}")
        return 0