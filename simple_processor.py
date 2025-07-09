#!/usr/bin/env python3
"""
Simple and reliable processor for AI analysis
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
    base_url="https://api.deepseek.com/v1"
)

def process_candidate_simple(candidate_id):
    """
    Process a single candidate with simple, reliable approach
    """
    try:
        with app.app_context():
            candidate = db.session.get(Candidate, candidate_id)
            if not candidate:
                print(f"Candidate {candidate_id} not found")
                return False
            
            print(f"Processing candidate {candidate_id}: {candidate.name}")
            
            # Update status
            candidate.analysis_status = 'processing'
            db.session.commit()
            
            # Extract resume text
            resume_text = extract_text_from_file(candidate.file_path, candidate.file_type)
            if len(resume_text) > 2000:
                resume_text = resume_text[:2000]
            
            # Generate score
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
            
            # Generate analysis
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
            candidate.ai_analysis = f"Score: {score}/10. {analysis}"
            candidate.analysis_status = 'completed'
            candidate.analyzed_at = datetime.utcnow()
            
            db.session.commit()
            
            print(f"✓ Completed: {candidate.name} - Score: {score}")
            return True
            
    except Exception as e:
        print(f"✗ Error processing candidate {candidate_id}: {str(e)}")
        try:
            with app.app_context():
                candidate = db.session.get(Candidate, candidate_id)
                if candidate:
                    candidate.analysis_status = 'failed'
                    candidate.ai_summary = f'Erro na análise: {str(e)}'
                    candidate.ai_score = 0.0
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
            
            print(f"Found {len(pending_candidates)} pending candidates")
            
            for candidate in pending_candidates:
                success = process_candidate_simple(candidate.id)
                if success:
                    print(f"   ✓ Processed: {candidate.name}")
                else:
                    print(f"   ✗ Failed: {candidate.name}")
                
                # Small delay between requests
                time.sleep(2)
            
            print("All pending candidates processed!")
            
    except Exception as e:
        print(f"Error processing all candidates: {e}")

def start_simple_background_processing(candidate_ids):
    """
    Start simple background processing
    """
    def simple_worker():
        try:
            print(f"Starting background processing for {len(candidate_ids)} candidates...")
            
            for candidate_id in candidate_ids:
                success = process_candidate_simple(candidate_id)
                if success:
                    print(f"   ✓ Processed candidate {candidate_id}")
                else:
                    print(f"   ✗ Failed candidate {candidate_id}")
                
                # Small delay between requests
                time.sleep(2)
            
            print("Background processing completed!")
            
        except Exception as e:
            print(f"Error in background processing: {e}")
    
    thread = threading.Thread(target=simple_worker, daemon=True)
    thread.start()
    return thread

def reset_processing_candidates():
    """
    Reset candidates stuck in processing
    """
    try:
        with app.app_context():
            stuck_candidates = Candidate.query.filter_by(analysis_status='processing').all()
            for candidate in stuck_candidates:
                candidate.analysis_status = 'pending'
            db.session.commit()
            print(f"Reset {len(stuck_candidates)} stuck candidates")
    except Exception as e:
        print(f"Error resetting candidates: {e}")

if __name__ == "__main__":
    # Reset any stuck candidates
    reset_processing_candidates()
    
    # Process all pending candidates
    process_all_pending()