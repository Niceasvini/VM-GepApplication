"""
Parallel processor for AI analysis with concurrent processing
"""
import os
import threading
import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from app import app, db
from models import Candidate
from ai_service import analyze_resume

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParallelAIProcessor:
    """
    Processes multiple candidates simultaneously using thread pool
    """
    def __init__(self, max_workers=8):
        self.max_workers = max_workers
        self.processing_status = {}
        self.lock = threading.Lock()
    
    def process_candidate(self, candidate_id):
        """
        Process a single candidate with AI analysis
        """
        try:
            with app.app_context():
                candidate = db.session.get(Candidate, candidate_id)
                if not candidate:
                    logger.error(f"Candidate {candidate_id} not found")
                    return False
                
                # Update status to processing
                candidate.analysis_status = 'processing'
                db.session.commit()
                
                with self.lock:
                    self.processing_status[candidate_id] = 'processing'
                
                logger.info(f"Starting analysis for candidate {candidate_id}: {candidate.name}")
                
                # Analyze with AI
                result = analyze_resume(candidate.file_path, candidate.file_type, candidate.job)
                
                if result:
                    # Update candidate with results
                    candidate.ai_score = result.get('score', 0)
                    candidate.ai_summary = result.get('summary', '')
                    candidate.ai_analysis = result.get('analysis', '')
                    candidate.extracted_skills = result.get('skills', '[]')
                    candidate.analysis_status = 'completed'
                    candidate.analyzed_at = datetime.utcnow()
                    
                    db.session.commit()
                    
                    with self.lock:
                        self.processing_status[candidate_id] = 'completed'
                    
                    logger.info(f"✅ Completed analysis for {candidate.name} - Score: {result.get('score', 0)}")
                    return True
                else:
                    # Mark as failed
                    candidate.analysis_status = 'failed'
                    db.session.commit()
                    
                    with self.lock:
                        self.processing_status[candidate_id] = 'failed'
                    
                    logger.error(f"❌ Failed analysis for {candidate.name}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error processing candidate {candidate_id}: {str(e)}")
            try:
                with app.app_context():
                    candidate = db.session.get(Candidate, candidate_id)
                    if candidate:
                        candidate.analysis_status = 'failed'
                        db.session.commit()
                        
                    with self.lock:
                        self.processing_status[candidate_id] = 'failed'
            except:
                pass
            return False
    
    def process_candidates_parallel(self, candidate_ids):
        """
        Process multiple candidates in parallel
        """
        if not candidate_ids:
            return {'success': 0, 'failed': 0, 'total': 0}
        
        logger.info(f"🚀 Starting parallel processing of {len(candidate_ids)} candidates")
        
        # Initialize status tracking
        with self.lock:
            for cid in candidate_ids:
                self.processing_status[cid] = 'pending'
        
        success_count = 0
        failed_count = 0
        
        # Process candidates in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_candidate = {
                executor.submit(self.process_candidate, cid): cid 
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
        
        logger.info(f"🎉 Parallel processing completed: {success_count} success, {failed_count} failed")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(candidate_ids)
        }
    
    def get_processing_status(self, candidate_ids):
        """
        Get current processing status
        """
        with self.lock:
            status_counts = {
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0
            }
            
            for cid in candidate_ids:
                status = self.processing_status.get(cid, 'pending')
                status_counts[status] += 1
            
            return status_counts

# Global processor instance
processor = ParallelAIProcessor(max_workers=8)

def start_parallel_analysis(candidate_ids):
    """
    Start parallel analysis in background thread
    """
    def worker():
        try:
            processor.process_candidates_parallel(candidate_ids)
        except Exception as e:
            logger.error(f"Error in parallel analysis: {str(e)}")
    
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    
    return thread

def get_processing_status(candidate_ids):
    """
    Get processing status for candidates
    """
    return processor.get_processing_status(candidate_ids)