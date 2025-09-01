#!/usr/bin/env python3
"""
Fast Parallel Processor for AI Analysis - Optimized for Speed
Processes multiple candidates simultaneously with optimized performance
"""
import os
import threading
import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://postgres.dxznqzpnsijpcmigpnfm:vYAeipsI0DBlO1sw@aws-0-sa-east-1.pooler.supabase.com:5432/postgres'

from app import app, db
from models.models import Candidate
from services.file_processor import extract_text_from_file
from services.ai_service import analyze_resume

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FastParallelProcessor:
    """
    High-performance parallel processor for AI analysis
    """
    def __init__(self, max_workers=10, batch_size=5):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.processing_status = {}
        self.lock = threading.Lock()
        self.processing_queue = Queue()
        self.results_queue = Queue()
    
    def process_candidate_fast(self, candidate_id):
        """
        Process a single candidate with optimized performance
        """
        try:
            with app.app_context():
                candidate = db.session.get(Candidate, candidate_id)
                if not candidate:
                    # Candidate was deleted or doesn't exist - skip silently
                    with self.lock:
                        self.processing_status[candidate_id] = 'deleted'
                    return False
                
                # Update status to processing
                candidate.analysis_status = 'processing'
                db.session.commit()
                
                with self.lock:
                    self.processing_status[candidate_id] = 'processing'
                
                # Extract text first (fast operation)
                resume_text = extract_text_from_file(candidate.file_path, candidate.file_type)
                
                # Analyze with AI (optimized)
                result = analyze_resume(candidate.file_path, candidate.file_type, candidate.job)
                
                if result and result.get('score') is not None:
                    # Validate analysis completeness
                    score = result.get('score', 0)
                    summary = result.get('summary', '')
                    analysis = result.get('analysis', '')
                    
                    # Check if analysis is complete
                    is_complete = (
                        score > 0 and
                        summary and len(summary.strip()) > 50 and
                        analysis and len(analysis.strip()) > 100 and
                        not summary.startswith('Erro') and
                        not analysis.startswith('FALHA NA ANÁLISE')
                    )
                    
                    if is_complete:
                        # Update candidate with results
                        candidate.ai_score = score
                        candidate.ai_summary = summary
                        candidate.ai_analysis = analysis
                        candidate.extracted_skills = result.get('skills', '[]')
                        candidate.analysis_status = 'completed'
                        candidate.analyzed_at = datetime.utcnow()
                        
                        db.session.commit()
                        
                        with self.lock:
                            self.processing_status[candidate_id] = 'completed'
                        
                        return True
                    else:
                        # Mark as failed due to incomplete analysis
                        candidate.analysis_status = 'failed'
                        candidate.ai_score = 0.0
                        candidate.ai_summary = 'Análise incompleta - Falha na geração do conteúdo'
                        candidate.ai_analysis = 'FALHA NA ANÁLISE: A análise foi marcada como concluída mas não gerou conteúdo completo. Possíveis causas: erro na API, timeout, ou texto insuficiente.'
                        db.session.commit()
                        
                        with self.lock:
                            self.processing_status[candidate_id] = 'failed'
                        
                        return False
                else:
                    # Mark as failed
                    candidate.analysis_status = 'failed'
                    candidate.ai_score = 0.0
                    candidate.ai_summary = 'Análise falhou'
                    candidate.ai_analysis = 'Erro na análise'
                    db.session.commit()
                    
                    with self.lock:
                        self.processing_status[candidate_id] = 'failed'
                    
                    return False
                    
        except Exception as e:
            # Silent error handling - don't log every error to reduce noise
            try:
                with app.app_context():
                    candidate = db.session.get(Candidate, candidate_id)
                    if candidate:
                        candidate.analysis_status = 'failed'
                        candidate.ai_score = 0.0
                        candidate.ai_summary = f'Erro na análise'
                        candidate.ai_analysis = f'Falha na análise'
                        db.session.commit()
                        
                    with self.lock:
                        self.processing_status[candidate_id] = 'failed'
            except:
                pass
            return False
    
    def process_candidates_parallel_fast(self, candidate_ids):
        """
        Process multiple candidates in parallel with optimized performance
        """
        if not candidate_ids:
            return {'success': 0, 'failed': 0, 'total': 0}
        
        logger.info(f"Iniciando processamento paralelo de {len(candidate_ids)} candidatos")
        
        # Initialize status tracking
        with self.lock:
            for cid in candidate_ids:
                self.processing_status[cid] = 'pending'
        
        success_count = 0
        failed_count = 0
        start_time = time.time()
        
        # Process candidates in parallel with optimized thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks at once
            future_to_candidate = {
                executor.submit(self.process_candidate_fast, cid): cid 
                for cid in candidate_ids
            }
            
            # Process completed tasks as they finish
            for future in as_completed(future_to_candidate):
                candidate_id = future_to_candidate[future]
                try:
                    result = future.result(timeout=120)  # 2 minute timeout per candidate
                    if result:
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    with self.lock:
                        self.processing_status[candidate_id] = 'failed'
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Processamento concluído em {duration:.2f}s: {success_count} sucessos, {failed_count} falhas")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(candidate_ids),
            'duration': duration
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
                'failed': 0,
                'deleted': 0
            }
            
            for cid in candidate_ids:
                status = self.processing_status.get(cid, 'pending')
                status_counts[status] += 1
            
            return status_counts

# Global processor instance
fast_processor = FastParallelProcessor(max_workers=8)

def start_fast_parallel_analysis(candidate_ids):
    """
    Start fast parallel analysis in background thread
    """
    def fast_worker():
        try:
            fast_processor.process_candidates_parallel_fast(candidate_ids)
        except Exception as e:
            logger.error(f"Error in fast parallel analysis: {str(e)}")
    
    thread = threading.Thread(target=fast_worker)
    thread.daemon = True
    thread.start()
    
    return thread

def get_fast_processing_status(candidate_ids):
    """
    Get processing status for candidates
    """
    return fast_processor.get_processing_status(candidate_ids)

def reset_stuck_candidates():
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
        logger.error(f"Error resetting candidates: {str(e)}")
        return 0 