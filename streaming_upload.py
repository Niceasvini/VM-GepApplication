"""
Streaming upload processor to handle large batches without timeout
"""
import os
import logging
import time
from flask import jsonify, request, current_app
from werkzeug.utils import secure_filename
from app import app, db
from models import Candidate, Job
from file_processor import process_uploaded_file
from sqlalchemy.exc import SQLAlchemyError

def process_files_in_batches(files, job_id, batch_size=10):
    """
    Process files in smaller batches to avoid timeout
    """
    total_files = len(files)
    processed = 0
    candidate_ids = []
    errors = []
    
    for i in range(0, total_files, batch_size):
        batch = files[i:i + batch_size]
        
        logging.info(f"Processing batch {i//batch_size + 1}: files {i+1}-{min(i+batch_size, total_files)}")
        
        for file in batch:
            try:
                if not file.filename or file.filename == '':
                    continue
                    
                # Secure filename
                filename = secure_filename(file.filename)
                if not filename:
                    filename = f"resume_{int(time.time())}.pdf"
                
                # Check file type
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if file_ext not in ['pdf', 'docx', 'txt']:
                    errors.append(f'Formato não suportado: {filename}')
                    continue
                
                # Save file
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Process file to extract basic info
                try:
                    name, email, phone = process_uploaded_file(file_path, file_ext)
                except Exception as e:
                    logging.error(f"Error processing file {filename}: {e}")
                    name = filename.rsplit('.', 1)[0]
                    email = None
                    phone = None
                
                # Create candidate record
                candidate = Candidate(
                    name=name,
                    email=email,
                    phone=phone,
                    filename=filename,
                    file_path=file_path,
                    file_type=file_ext,
                    job_id=job_id,
                    status='pending',
                    analysis_status='pending'
                )
                
                # Save to database
                try:
                    db.session.add(candidate)
                    db.session.flush()
                    candidate_id = candidate.id
                    db.session.commit()
                    candidate_ids.append(candidate_id)
                    processed += 1
                    
                    logging.info(f"✅ Saved: {filename} (ID: {candidate_id}) - {processed}/{total_files}")
                    
                except SQLAlchemyError as db_error:
                    logging.error(f"Database error for {filename}: {db_error}")
                    db.session.rollback()
                    errors.append(f'Erro de banco para {filename}: {str(db_error)}')
                    continue
                    
            except Exception as e:
                logging.error(f"Error processing file {file.filename}: {e}")
                errors.append(f'Erro ao processar {file.filename}: {str(e)}')
        
        # Small delay between batches
        if i + batch_size < total_files:
            time.sleep(0.1)
    
    return {
        'processed_count': processed,
        'candidate_ids': candidate_ids,
        'errors': errors,
        'total_files': total_files
    }

def start_batch_upload(files, job_id):
    """
    Start batch upload process
    """
    try:
        logging.info(f"Starting batch upload for {len(files)} files")
        
        # Process files in batches
        result = process_files_in_batches(files, job_id, batch_size=5)
        
        # Start AI analysis if we have candidates
        if result['candidate_ids']:
            logging.info(f"Starting AI analysis for {len(result['candidate_ids'])} candidates")
            from parallel_processor import start_parallel_analysis
            start_parallel_analysis(result['candidate_ids'])
        
        return result
        
    except Exception as e:
        logging.error(f"Error in batch upload: {str(e)}")
        return {
            'processed_count': 0,
            'candidate_ids': [],
            'errors': [f'Erro no processamento: {str(e)}'],
            'total_files': len(files)
        }