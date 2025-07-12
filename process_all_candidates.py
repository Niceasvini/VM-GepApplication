#!/usr/bin/env python3
"""
Process all pending candidates and show real-time progress
"""
import os
import time
import threading
from datetime import datetime
from openai import OpenAI

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://postgres.bndkpowgvagtlxwmthma:5585858Vini%40@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'

from app import app, db
from models import Candidate
from file_processor import extract_text_from_file

# Configure OpenAI client
client = OpenAI(
    api_key="sk-08e53165834948c8b96fe8ec44a12baf",
    base_url="https://api.deepseek.com/v1",

)

def process_all_with_progress():
    """Process all pending candidates with real-time progress"""
    try:
        with app.app_context():
            pending_candidates = Candidate.query.filter_by(analysis_status='pending').all()
            
            print(f"=== PROCESSAMENTO EM LOTE ===")
            print(f"Candidatos pendentes: {len(pending_candidates)}")
            
            if not pending_candidates:
                print("Nenhum candidato pendente encontrado.")
                return
            
            for i, candidate in enumerate(pending_candidates, 1):
                print(f"\n[{i}/{len(pending_candidates)}] Processando {candidate.name}...")
                
                try:
                    # Update status
                    candidate.analysis_status = 'processing'
                    db.session.commit()
                    
                    # Extract resume text
                    resume_text = extract_text_from_file(candidate.file_path, candidate.file_type)
                    
                    # Generate quick score
                    print(f"  Chamando DeepSeek API...")
                    start_time = time.time()
                    
                    score_response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{
                            "role": "user",
                            "content": f"Avalie este currículo para '{candidate.job.title}' de 0-10. Responda apenas o número (ex: 8.5):\\n\\n{resume_text[:800]}"
                        }],
                        max_tokens=10,
                        temperature=0.1
                    )
                    
                    elapsed = time.time() - start_time
                    score_text = score_response.choices[0].message.content.strip()
                    
                    # Parse score
                    import re
                    score_match = re.search(r'(\\d+\\.?\\d*)', score_text)
                    if score_match:
                        score = float(score_match.group(1))
                        if score > 10:
                            score = score / 10
                    else:
                        score = 5.0
                    
                    print(f"  Score obtido: {score} (tempo: {elapsed:.2f}s)")
                    
                    # Generate summary
                    summary_response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{
                            "role": "user",
                            "content": f"Faça um resumo técnico detalhado de {candidate.name} para {candidate.job.title}. Inclua experiência, habilidades e formação relevante:\\n\\n{resume_text[:5000]}"
                        }],
                        max_tokens=900,
                        temperature=0.3
                    )
                    
                    summary = summary_response.choices[0].message.content.strip()
                    
                    # Update candidate
                    candidate.ai_score = score
                    candidate.ai_summary = summary
                    candidate.ai_analysis = f"Análise: Score {score}/10. {summary}"
                    candidate.analysis_status = 'completed'
                    candidate.analyzed_at = datetime.utcnow()
                    
                    db.session.commit()
                    
                    print(f"  ✓ SUCESSO: {candidate.name} - Score: {score}")
                    
                except Exception as e:
                    print(f"  ✗ ERRO: {candidate.name} - {str(e)}")
                    
                    # Mark as failed
                    candidate.analysis_status = 'failed'
                    candidate.ai_summary = f'Erro: {str(e)}'
                    candidate.ai_score = 0.0
                    db.session.commit()
                
                # Small delay between requests
                time.sleep(2)
            
            print(f"\n=== PROCESSAMENTO CONCLUÍDO ===")
            
            # Show final results
            completed = Candidate.query.filter_by(analysis_status='completed').count()
            failed = Candidate.query.filter_by(analysis_status='failed').count()
            pending = Candidate.query.filter_by(analysis_status='pending').count()
            
            print(f"Concluídos: {completed}")
            print(f"Falharam: {failed}")
            print(f"Pendentes: {pending}")
            
    except Exception as e:
        print(f"Erro geral: {e}")

def run_background_processing():
    """Run processing in background thread"""
    def worker():
        process_all_with_progress()
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    process_all_with_progress()