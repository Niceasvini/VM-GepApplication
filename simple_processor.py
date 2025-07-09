#!/usr/bin/env python3
"""
Simple and reliable processor for AI analysis
"""
import threading
import time
import logging
from datetime import datetime
from app import app, db
from models import Candidate
from ai_service import generate_score_only, generate_summary_and_analysis, extract_skills_from_text, estimate_experience_years, determine_education_level
from file_processor import extract_text_from_file

def process_candidate_simple(candidate_id):
    """
    Process a single candidate with simple, reliable approach
    """
    try:
        with app.app_context():
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                return False
            
            # Update status
            candidate.analysis_status = 'processing'
            db.session.commit()
            
            logging.info(f"Processing candidate {candidate_id}: {candidate.name}")
            
            # Extract resume text
            resume_text = extract_text_from_file(candidate.file_path, candidate.file_type)
            if len(resume_text) > 3000:
                resume_text = resume_text[:3000]
            
            # Generate basic score (most important)
            try:
                score = generate_score_only(resume_text, candidate.job)
                logging.info(f"Generated score {score} for candidate {candidate_id}")
            except Exception as e:
                logging.error(f"Failed to generate score for candidate {candidate_id}: {e}")
                score = 5.0  # Default score
            
            # Generate summary and analysis
            try:
                summary, analysis = generate_summary_and_analysis(resume_text, candidate.job)
                logging.info(f"Generated summary and analysis for candidate {candidate_id}")
            except Exception as e:
                logging.error(f"Failed to generate summary for candidate {candidate_id}: {e}")
                summary = f"Currículo de {candidate.name}"
                analysis = "Análise não disponível devido a erro no processamento"
            
            # Extract additional info (offline processing)
            skills = extract_skills_from_text(resume_text)
            experience_years = estimate_experience_years(resume_text)
            education_level = determine_education_level(resume_text)
            
            # Update candidate with all results
            candidate.ai_score = score
            candidate.ai_summary = summary
            candidate.ai_analysis = analysis
            candidate.set_skills_list(skills)
            candidate.analysis_status = 'completed'
            candidate.analyzed_at = datetime.utcnow()
            
            db.session.commit()
            
            logging.info(f"Successfully processed candidate {candidate_id} with score {score}")
            return True
            
    except Exception as e:
        logging.error(f"Error processing candidate {candidate_id}: {str(e)}")
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

def process_all_pending():
    """
    Process all pending candidates one by one
    """
    with app.app_context():
        pending_candidates = Candidate.query.filter_by(analysis_status='pending').all()
        
        if not pending_candidates:
            print("No pending candidates found")
            return
        
        print(f"Processing {len(pending_candidates)} pending candidates...")
        
        success_count = 0
        for candidate in pending_candidates:
            print(f"Processing {candidate.name}...")
            if process_candidate_simple(candidate.id):
                success_count += 1
                print(f"✓ Completed: {candidate.name}")
            else:
                print(f"✗ Failed: {candidate.name}")
            
            # Small delay between candidates
            time.sleep(2)
        
        print(f"Processing complete! {success_count}/{len(pending_candidates)} successful")

def start_simple_background_processing(candidate_ids):
    """
    Start simple background processing
    """
    def simple_worker():
        try:
            with app.app_context():
                for candidate_id in candidate_ids:
                    candidate = Candidate.query.get(candidate_id)
                    if candidate and candidate.analysis_status == 'pending':
                        process_candidate_simple(candidate_id)
                        time.sleep(1)  # Small delay between candidates
                        
        except Exception as e:
            logging.error(f"Simple background processing error: {str(e)}")
    
    thread = threading.Thread(target=simple_worker, daemon=True)
    thread.start()
    return thread

def reset_processing_candidates():
    """
    Reset candidates stuck in processing
    """
    with app.app_context():
        processing_candidates = Candidate.query.filter_by(analysis_status='processing').all()
        reset_count = 0
        
        for candidate in processing_candidates:
            candidate.analysis_status = 'pending'
            reset_count += 1
            print(f"Reset {candidate.name} to pending")
        
        db.session.commit()
        return reset_count

if __name__ == "__main__":
    # Reset stuck candidates
    reset_count = reset_processing_candidates()
    print(f"Reset {reset_count} candidates")
    
    # Process all pending
    process_all_pending()