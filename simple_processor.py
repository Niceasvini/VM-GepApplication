"""
Simple and reliable processor for AI analysis
"""
import os
import threading
import logging
import time
from datetime import datetime
from app import app, db
from models import Candidate
from ai_service import analyze_resume

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_candidate_simple(candidate_id):
    """
    Process a single candidate with simple, reliable approach
    """
    try:
        with app.app_context():
            candidate = db.session.get(Candidate, candidate_id)
            if not candidate:
                logger.error(f"Candidate {candidate_id} not found")
                return False
            
            logger.info(f"Processing candidate {candidate_id}: {candidate.name}")
            
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
                
                logger.info(f"✅ Completed: {candidate.name} - Score: {result.get('score', 0)}")
                return True
            else:
                candidate.analysis_status = 'failed'
                db.session.commit()
                logger.error(f"❌ Failed: {candidate.name}")
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

def process_all_pending():
    """
    Process all pending candidates one by one
    """
    try:
        with app.app_context():
            pending_candidates = Candidate.query.filter_by(analysis_status='pending').all()
            
            if not pending_candidates:
                logger.info("No pending candidates to process")
                return
            
            logger.info(f"Processing {len(pending_candidates)} pending candidates")
            
            success_count = 0
            
            for candidate in pending_candidates:
                if process_candidate_simple(candidate.id):
                    success_count += 1
                
                # Small delay between candidates
                time.sleep(0.5)
            
            logger.info(f"Processing complete: {success_count}/{len(pending_candidates)} successful")
            
    except Exception as e:
        logger.error(f"Error in process_all_pending: {str(e)}")

def start_simple_background_processing(candidate_ids):
    """
    Start simple background processing
    """
    def simple_worker():
        try:
            for candidate_id in candidate_ids:
                process_candidate_simple(candidate_id)
                time.sleep(0.5)  # Small delay between candidates
        except Exception as e:
            logger.error(f"Error in simple background processing: {str(e)}")
    
    thread = threading.Thread(target=simple_worker)
    thread.daemon = True
    thread.start()
    
    return thread

def reset_processing_candidates():
    """
    Reset candidates stuck in processing
    """
    try:
        with app.app_context():
            processing_candidates = Candidate.query.filter_by(analysis_status='processing').all()
            
            for candidate in processing_candidates:
                candidate.analysis_status = 'pending'
                db.session.commit()
                logger.info(f"Reset candidate {candidate.id}: {candidate.name}")
            
            return len(processing_candidates)
    except Exception as e:
        logger.error(f"Error resetting processing candidates: {str(e)}")
        return 0