#!/usr/bin/env python3
"""
Fast parallel processor for AI analysis with optimized performance
"""
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from openai import OpenAI

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://postgres.bndkpowgvagtlxwmthma:5585858Vini%40@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'

from app import app, db
from models import User, Job, Candidate
from file_processor import extract_text_from_file

# Configure OpenAI client
client = OpenAI(
    api_key="sk-08e53165834948c8b96fe8ec44a12baf",
    base_url="https://api.deepseek.com/v1"
)

def process_candidate_fast(candidate_id):
    """
    Process a single candidate with optimized speed
    """
    try:
        with app.app_context():
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                return False
            
            # Update status
            candidate.analysis_status = 'processing'
            db.session.commit()
            
            # Extract resume text
            resume_text = extract_text_from_file(candidate.file_path, candidate.file_type)
            if len(resume_text) > 2000:
                resume_text = resume_text[:2000]
            
            # Generate score only (faster)
            score_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user",
                    "content": f"Avalie este currículo para a vaga '{candidate.job.title}' de 0 a 10. Responda apenas a nota (ex: 7.5):\n\n{resume_text}"
                }],
                max_tokens=20,
                temperature=0.3
            )
            
            score_text = score_response.choices[0].message.content.strip()
            try:
                score = float(score_text.replace(":", "").strip())
            except:
                score = 5.0
            
            # Basic analysis (shorter)
            analysis_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user",
                    "content": f"Resumo do candidato {candidate.name} para vaga '{candidate.job.title}' (máximo 200 palavras):\n\n{resume_text}"
                }],
                max_tokens=300,
                temperature=0.5
            )
            
            analysis = analysis_response.choices[0].message.content.strip()
            
            # Update candidate
            candidate.ai_score = score
            candidate.ai_summary = analysis
            candidate.ai_analysis = f"Análise rápida: Score {score}/10 baseado em compatibilidade com a vaga."
            candidate.analysis_status = 'completed'
            candidate.analyzed_at = datetime.utcnow()
            
            db.session.commit()
            
            return True
            
    except Exception as e:
        print(f"Error processing candidate {candidate_id}: {str(e)}")
        try:
            with app.app_context():
                candidate = Candidate.query.get(candidate_id)
                if candidate:
                    candidate.analysis_status = 'failed'
                    candidate.ai_summary = f'Erro na análise: {str(e)}'
                    candidate.ai_score = 0.0
                    db.session.commit()
        except:
            pass
        return False

def process_candidates_parallel_fast(candidate_ids):
    """
    Process multiple candidates in parallel with optimized performance
    """
    results = {'success': 0, 'failed': 0}
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all tasks
        futures = {executor.submit(process_candidate_fast, cid): cid for cid in candidate_ids}
        
        # Process results as they complete
        for future in as_completed(futures):
            candidate_id = futures[future]
            try:
                success = future.result()
                if success:
                    results['success'] += 1
                    print(f"✓ Completed candidate {candidate_id}")
                else:
                    results['failed'] += 1
                    print(f"✗ Failed candidate {candidate_id}")
            except Exception as e:
                results['failed'] += 1
                print(f"✗ Exception for candidate {candidate_id}: {e}")
    
    return results

def start_fast_background_processing(candidate_ids):
    """
    Start fast background processing in a separate thread
    """
    def fast_background_worker():
        print(f"Starting fast background processing for {len(candidate_ids)} candidates...")
        results = process_candidates_parallel_fast(candidate_ids)
        print(f"Fast processing completed: {results['success']} success, {results['failed']} failed")
    
    thread = threading.Thread(target=fast_background_worker, daemon=True)
    thread.start()
    return thread

def get_fast_processing_status(candidate_ids):
    """
    Get processing status for candidates
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

def reset_stale_candidates():
    """
    Reset candidates that are stuck in processing status
    """
    try:
        with app.app_context():
            stale_candidates = Candidate.query.filter_by(analysis_status='processing').all()
            for candidate in stale_candidates:
                candidate.analysis_status = 'pending'
            db.session.commit()
            print(f"Reset {len(stale_candidates)} stale candidates")
    except Exception as e:
        print(f"Error resetting stale candidates: {e}")

if __name__ == "__main__":
    # Test with existing candidates
    with app.app_context():
        candidates = Candidate.query.all()
        if candidates:
            candidate_ids = [c.id for c in candidates]
            print(f"Found {len(candidate_ids)} candidates to process")
            
            # Reset any stuck candidates
            reset_stale_candidates()
            
            # Process them
            results = process_candidates_parallel_fast(candidate_ids)
            print(f"Processing completed: {results}")
        else:
            print("No candidates found to process")