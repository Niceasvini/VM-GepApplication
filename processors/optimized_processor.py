#!/usr/bin/env python3
"""
Optimized Processor for AI Analysis - Balanced Performance
Processes candidates with controlled load to maintain server responsiveness
"""
import os
import threading
import time
import logging
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://postgres.dxznqzpnsijpcmigpnfm:vYAeipsI0DBlO1sw@aws-0-sa-east-1.pooler.supabase.com:5432/postgres'

from app import app, db
from models.models import Candidate
from services.file_processor import extract_text_from_file
from services.ai_service import analyze_resume

# Configure logging - reduced level to minimize terminal output
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class OptimizedProcessor:
    """
    Optimized processor that balances performance with server responsiveness
    """
    def __init__(self, max_workers=2, batch_size=3, delay_between_batches=3):
        # Configurações conservadoras para manter servidor responsivo
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.processing_status = {}
        self.lock = threading.Lock()
        self.is_processing = False
    
    def process_candidate_optimized(self, candidate_id):
        """
        Process a single candidate with optimized performance
        """
        try:
            with app.app_context():
                candidate = db.session.get(Candidate, candidate_id)
                if not candidate:
                    with self.lock:
                        self.processing_status[candidate_id] = 'deleted'
                    return False
                
                # Update status to processing
                candidate.analysis_status = 'processing'
                db.session.commit()
                
                with self.lock:
                    self.processing_status[candidate_id] = 'processing'
                
                # Add delay to reduce server load
                time.sleep(1)
                
                # Analyze with AI
                result = analyze_resume(candidate.file_path, candidate.file_type, candidate.job)
                
                if result and result.get('score') is not None:
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
                        # Usar timezone do Brasil
                        brazil_tz = pytz.timezone('America/Sao_Paulo')
                        candidate.analyzed_at = datetime.now(brazil_tz)
                        
                        db.session.commit()
                        
                        with self.lock:
                            self.processing_status[candidate_id] = 'completed'
                        
                        # Log apenas scores altos para reduzir poluição
                        if score >= 7:
                            print(f"✓ {candidate.name} - Score: {score}")
                        
                        return True
                    else:
                        # Mark as failed due to incomplete analysis
                        candidate.analysis_status = 'failed'
                        candidate.ai_score = 0.0
                        candidate.ai_summary = 'Análise incompleta'
                        candidate.ai_analysis = 'FALHA NA ANÁLISE: Análise incompleta'
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
    
    def process_candidates_optimized(self, candidate_ids):
        """
        Process candidates in optimized batches to maintain server responsiveness
        """
        if not candidate_ids:
            return {'success': 0, 'failed': 0, 'total': 0}
        
        if self.is_processing:
            print("⚠️ Processamento já em andamento, aguardando...")
            return {'success': 0, 'failed': 0, 'total': 0, 'message': 'Processamento já em andamento'}
        
        self.is_processing = True
        
        try:
            print(f"🚀 INICIANDO PROCESSAMENTO OTIMIZADO: {len(candidate_ids)} candidatos")
            
            # Initialize status tracking
            with self.lock:
                for cid in candidate_ids:
                    self.processing_status[cid] = 'pending'
            
            success_count = 0
            failed_count = 0
            start_time = time.time()
            
            # Process in batches to avoid server overload
            for i in range(0, len(candidate_ids), self.batch_size):
                batch = candidate_ids[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (len(candidate_ids) + self.batch_size - 1) // self.batch_size
                
                print(f"📋 Processando lote {batch_num}/{total_batches} ({len(batch)} candidatos)")
                
                # Process batch with limited workers
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_candidate = {
                        executor.submit(self.process_candidate_optimized, cid): cid 
                        for cid in batch
                    }
                    
                    # Process completed tasks
                    for future in as_completed(future_to_candidate):
                        candidate_id = future_to_candidate[future]
                        try:
                            result = future.result(timeout=120)
                            if result:
                                success_count += 1
                            else:
                                failed_count += 1
                        except Exception as e:
                            failed_count += 1
                            with self.lock:
                                self.processing_status[candidate_id] = 'failed'
                
                # Delay between batches to keep server responsive
                if i + self.batch_size < len(candidate_ids):
                    print(f"⏳ Aguardando {self.delay_between_batches}s antes do próximo lote...")
                    time.sleep(self.delay_between_batches)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"🎉 PROCESSAMENTO CONCLUÍDO em {duration:.1f}s: {success_count} sucessos, {failed_count} falhas")
            
            return {
                'success': success_count,
                'failed': failed_count,
                'total': len(candidate_ids),
                'duration': duration
            }
            
        finally:
            self.is_processing = False
    
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

# Global processor instance - optimized for server responsiveness
optimized_processor = OptimizedProcessor(max_workers=2, batch_size=3, delay_between_batches=3)

def start_optimized_analysis(candidate_ids):
    """
    Start optimized analysis in background thread
    """
    def optimized_worker():
        try:
            print(f"🔄 Iniciando worker otimizado para candidatos: {candidate_ids}")
            result = optimized_processor.process_candidates_optimized(candidate_ids)
            print(f"✅ Worker otimizado concluído: {result}")
        except Exception as e:
            print(f"❌ Erro no worker otimizado: {str(e)}")
            logger.error(f"Error in optimized analysis: {str(e)}")
    
    print(f"🚀 Criando thread para processamento de candidatos: {candidate_ids}")
    thread = threading.Thread(target=optimized_worker)
    thread.daemon = True
    thread.start()
    
    print(f"✅ Thread de processamento iniciada para candidatos: {candidate_ids}")
    return thread

def get_optimized_processing_status(candidate_ids):
    """
    Get processing status for candidates
    """
    return optimized_processor.get_processing_status(candidate_ids)
