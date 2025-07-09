#!/usr/bin/env python3
"""
Fix and complete the processing of candidates
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

# Configure OpenAI client with timeout
client = OpenAI(
    api_key="sk-08e53165834948c8b96fe8ec44a12baf",
    base_url="https://api.deepseek.com/v1",
    timeout=30  # 30 second timeout
)

def fix_and_process_candidates():
    """Fix stuck candidates and process them"""
    try:
        with app.app_context():
            # Reset any stuck candidates
            stuck_candidates = Candidate.query.filter_by(analysis_status='processing').all()
            for candidate in stuck_candidates:
                candidate.analysis_status = 'pending'
            db.session.commit()
            print(f"Reset {len(stuck_candidates)} stuck candidates")
            
            # Get pending candidates
            pending_candidates = Candidate.query.filter_by(analysis_status='pending').all()
            print(f"Found {len(pending_candidates)} pending candidates")
            
            for candidate in pending_candidates:
                print(f"\nProcessing {candidate.name}...")
                
                try:
                    # Update status to processing
                    candidate.analysis_status = 'processing'
                    db.session.commit()
                    
                    # Extract text from resume
                    resume_text = extract_text_from_file(candidate.file_path, candidate.file_type)
                    
                    # Truncate if too long
                    if len(resume_text) > 1500:
                        resume_text = resume_text[:1500]
                    
                    # Test simple prompt first
                    print(f"  Making API call to DeepSeek...")
                    start_time = time.time()
                    
                    # Generate score with simple prompt
                    score_response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{
                            "role": "user",
                            "content": f"Avalie este currículo para vaga '{candidate.job.title}' de 0 a 10. Responda APENAS a nota (ex: 8.5):\n\n{resume_text[:500]}"
                        }],
                        max_tokens=10,
                        temperature=0.1
                    )
                    
                    elapsed = time.time() - start_time
                    print(f"  API call completed in {elapsed:.2f}s")
                    
                    # Extract score
                    score_text = score_response.choices[0].message.content.strip()
                    print(f"  Raw score response: '{score_text}'")
                    
                    # Parse score
                    try:
                        # Remove any non-numeric characters except decimal point
                        import re
                        score_match = re.search(r'(\d+\.?\d*)', score_text)
                        if score_match:
                            score = float(score_match.group(1))
                        else:
                            score = 5.0  # Default score if parsing fails
                    except:
                        score = 5.0
                    
                    # Generate simple analysis
                    analysis_response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{
                            "role": "user",
                            "content": f"Resumo de {candidate.name} para vaga '{candidate.job.title}' (máximo 100 palavras):\n\n{resume_text[:500]}"
                        }],
                        max_tokens=200,
                        temperature=0.3
                    )
                    
                    analysis = analysis_response.choices[0].message.content.strip()
                    
                    # Update candidate
                    candidate.ai_score = score
                    candidate.ai_summary = analysis
                    candidate.ai_analysis = f"Análise automática: Score {score}/10 baseado em compatibilidade com os requisitos da vaga."
                    candidate.analysis_status = 'completed'
                    candidate.analyzed_at = datetime.utcnow()
                    
                    db.session.commit()
                    
                    print(f"  ✓ SUCESSO: {candidate.name} - Score: {score}")
                    
                except Exception as e:
                    print(f"  ✗ ERRO: {candidate.name} - {str(e)}")
                    
                    # Mark as failed
                    candidate.analysis_status = 'failed'
                    candidate.ai_summary = f'Erro na análise: {str(e)}'
                    candidate.ai_score = 0.0
                    db.session.commit()
                
                # Small delay between requests
                time.sleep(2)
            
            print(f"\n=== PROCESSAMENTO CONCLUÍDO ===")
            
            # Show final status
            completed = Candidate.query.filter_by(analysis_status='completed').count()
            failed = Candidate.query.filter_by(analysis_status='failed').count()
            pending = Candidate.query.filter_by(analysis_status='pending').count()
            
            print(f"Concluídos: {completed}")
            print(f"Falharam: {failed}")
            print(f"Pendentes: {pending}")
            
    except Exception as e:
        print(f"Erro geral: {e}")

if __name__ == "__main__":
    fix_and_process_candidates()