"""
Improved Parallel processor for AI analysis with better concurrency and error handling
"""
import os
import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread, Lock
from app import app, db
from models import Candidate
from services.ai_service import analyze_resume

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedParallelAIProcessor:
    """
    Processes multiple candidates simultaneously with improved performance
    """
    def __init__(self, max_workers=15):  # Increased workers for better concurrency
        self.max_workers = max_workers
        self.processing_status = {}
        self.status_lock = Lock()  # Thread-safe status updates
        logger.info(f"Initialized ImprovedParallelAIProcessor with {max_workers} workers")
    
    def process_candidate_safe(self, candidate_id):
        """
        Process a single candidate with improved error handling and database safety
        """
        try:
            with app.app_context():
                # Use a separate database session per thread
                candidate = db.session.get(Candidate, candidate_id)
                if not candidate:
                    logger.warning(f"Candidate {candidate_id} not found (may have been deleted)")
                    with self.status_lock:
                        self.processing_status[candidate_id] = 'not_found'
                    return False
                
                # Check if job still exists (prevent errors when job is deleted)
                if not candidate.job:
                    logger.warning(f"Job for candidate {candidate_id} not found (may have been deleted)")
                    with self.status_lock:
                        self.processing_status[candidate_id] = 'job_deleted'
                    return False
                
                # Update status to processing
                candidate.analysis_status = 'processing'
                db.session.commit()
                
                with self.status_lock:
                    self.processing_status[candidate_id] = 'processing'
                
                logger.info(f"🔍 Analisando candidato {candidate_id}: {candidate.name}")
                
                # Analyze with AI - with timeout protection
                try:
                    result = analyze_resume(candidate.file_path, candidate.file_type, candidate.job)
                except Exception as analysis_error:
                    logger.error(f"Analysis error for {candidate_id}: {str(analysis_error)}")
                    result = None
                
                if result:
                    # Update candidate with results
                    candidate.ai_score = result.get('score', 0)
                    candidate.ai_summary = result.get('summary', '')
                    candidate.ai_analysis = result.get('analysis', '')
                    candidate.extracted_skills = result.get('skills', '[]')
                    candidate.analysis_status = 'completed'
                    candidate.analyzed_at = datetime.utcnow()
                    
                    # Auto-reject low scores
                    if candidate.ai_score < 5.0:
                        candidate.status = 'rejected'
                    
                    db.session.commit()
                    
                    with self.status_lock:
                        self.processing_status[candidate_id] = 'completed'
                    
                    logger.info(f"✅ Candidato {candidate.name} processado - Score: {result.get('score', 0)}")
                    return True
                else:
                    # Mark as failed
                    candidate.analysis_status = 'failed'
                    db.session.commit()
                    
                    with self.status_lock:
                        self.processing_status[candidate_id] = 'failed'
                    
                    logger.error(f"❌ Falha na análise para {candidate.name}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro crítico ao processar candidato {candidate_id}: {str(e)}")
            try:
                with app.app_context():
                    candidate = db.session.get(Candidate, candidate_id)
                    if candidate:
                        candidate.analysis_status = 'failed'
                        db.session.commit()
                    with self.status_lock:
                        self.processing_status[candidate_id] = 'failed'
            except Exception as cleanup_error:
                logger.error(f"Erro no cleanup: {str(cleanup_error)}")
            return False
    
    def process_candidates_parallel(self, candidate_ids):
        """
        Process multiple candidates in parallel with better performance
        """
        if not candidate_ids:
            logger.info("Nenhum candidato para processar")
            return {'success': 0, 'failed': 0, 'total': 0}
        
        logger.info(f"🚀 Iniciando processamento paralelo de {len(candidate_ids)} candidatos")
        
        success_count = 0
        failed_count = 0
        start_time = time.time()
        
        # Use ThreadPoolExecutor for better I/O handling
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_candidate = {
                executor.submit(self.process_candidate_safe, candidate_id): candidate_id
                for candidate_id in candidate_ids
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
                    logger.error(f"Erro ao processar candidato {candidate_id}: {str(e)}")
                    failed_count += 1
                    with self.status_lock:
                        self.processing_status[candidate_id] = 'failed'
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ Processamento concluído em {duration:.2f}s: {success_count} sucessos, {failed_count} falhas")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(candidate_ids),
            'duration': duration
        }
    
    def get_processing_status(self, candidate_ids):
        """
        Get current processing status with thread safety
        """
        with self.status_lock:
            status_counts = {
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0,
                'not_found': 0,
                'job_deleted': 0
            }
            
            for candidate_id in candidate_ids:
                status = self.processing_status.get(candidate_id, 'pending')
                if status in status_counts:
                    status_counts[status] += 1
                else:
                    status_counts['pending'] += 1
            
            return status_counts
    
    def cleanup_status(self, candidate_ids):
        """
        Clean up processing status for completed candidates
        """
        with self.status_lock:
            for candidate_id in candidate_ids:
                if candidate_id in self.processing_status:
                    if self.processing_status[candidate_id] in ['completed', 'failed', 'not_found']:
                        del self.processing_status[candidate_id]

# Global instance with improved settings
improved_processor = ImprovedParallelAIProcessor(max_workers=15)

def start_improved_parallel_analysis(candidate_ids):
    """
    Start improved parallel analysis in background thread
    """
    def worker():
        try:
            result = improved_processor.process_candidates_parallel(candidate_ids)
            logger.info(f"Processamento em background concluído: {result}")
        except Exception as e:
            logger.error(f"Erro no processamento em background: {str(e)}")
    
    thread = Thread(target=worker)
    thread.daemon = True
    thread.start()
    return thread

def get_improved_processing_status(candidate_ids):
    """
    Get processing status for candidates
    """
    return improved_processor.get_processing_status(candidate_ids)

def cleanup_processing_status(candidate_ids):
    """
    Clean up processing status
    """
    improved_processor.cleanup_status(candidate_ids)

# Legacy compatibility functions
def start_parallel_analysis(candidate_ids):
    """Legacy function for backward compatibility"""
    return start_improved_parallel_analysis(candidate_ids)

def get_processing_status(candidate_ids):
    """Legacy function for backward compatibility"""
    return get_improved_processing_status(candidate_ids)