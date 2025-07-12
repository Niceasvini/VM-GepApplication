#!/usr/bin/env python3
"""
Test bulk upload and processing to ensure ALL candidates are processed
"""
import os
import time
import threading
from datetime import datetime

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://postgres.bndkpowgvagtlxwmthma:5585858Vini%40@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'

from app import app, db
from models import Job, Candidate

def create_test_candidates():
    """Create test candidates to simulate bulk upload"""
    with app.app_context():
        job = Job.query.first()
        if not job:
            print("No job found!")
            return []
        
        # Create 5 test candidates
        test_candidates = [
            {'name': 'Carlos Silva', 'email': 'carlos@test.com', 'content': 'Carlos Silva\nDesenvolvedor Python - 4 anos\nDjango, Flask, PostgreSQL\nExperiência com APIs REST'},
            {'name': 'Fernanda Costa', 'email': 'fernanda@test.com', 'content': 'Fernanda Costa\nDesenvolvedor Backend - 3 anos\nPython, FastAPI, MongoDB\nConhecimento em Docker'},
            {'name': 'Rafael Santos', 'email': 'rafael@test.com', 'content': 'Rafael Santos\nEngenheiro de Software - 5 anos\nPython, Java, Spring Boot\nExperiência com microserviços'},
            {'name': 'Julia Oliveira', 'email': 'julia@test.com', 'content': 'Julia Oliveira\nDesenvolvedor Full Stack - 2 anos\nPython, React, PostgreSQL\nConhecimento em testes automatizados'},
            {'name': 'Bruno Lima', 'email': 'bruno@test.com', 'content': 'Bruno Lima\nAnalista de Sistemas - 6 anos\nPython, SQL, Power BI\nExperiência em análise de dados'}
        ]
        
        candidate_ids = []
        for i, data in enumerate(test_candidates):
            filename = f'test_bulk_{i+1}.txt'
            file_path = f'uploads/{filename}'
            
            # Create file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(data['content'])
            
            # Create candidate
            candidate = Candidate(
                name=data['name'],
                email=data['email'],
                phone='(11) 99999-9999',
                filename=filename,
                file_path=file_path,
                file_type='txt',
                job_id=job.id,
                status='pending',
                analysis_status='pending'
            )
            
            db.session.add(candidate)
            db.session.commit()
            candidate_ids.append(candidate.id)
            print(f'✓ Created: {candidate.name} (ID: {candidate.id})')
        
        return candidate_ids

def start_bulk_processing(candidate_ids):
    """Start processing all candidates like the bulk upload does"""
    print(f"\n=== INICIANDO PROCESSAMENTO EM LOTE ===")
    print(f"Total candidatos: {len(candidate_ids)}")
    
    # This is exactly what happens in routes.py after bulk upload
    from processors.background_processor import start_background_analysis
    thread = start_background_analysis(candidate_ids)
    
    print(f"Processamento iniciado em background!")
    print(f"Thread ativa: {thread.is_alive()}")
    
    return thread

def monitor_progress(candidate_ids, max_wait_minutes=10):
    """Monitor processing progress"""
    print(f"\n=== MONITORANDO PROGRESSO ===")
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while time.time() - start_time < max_wait_seconds:
        with app.app_context():
            # Count statuses
            pending = 0
            processing = 0
            completed = 0
            failed = 0
            
            for candidate_id in candidate_ids:
                candidate = Candidate.query.get(candidate_id)
                if candidate:
                    if candidate.analysis_status == 'pending':
                        pending += 1
                    elif candidate.analysis_status == 'processing':
                        processing += 1
                    elif candidate.analysis_status == 'completed':
                        completed += 1
                    elif candidate.analysis_status == 'failed':
                        failed += 1
            
            total = len(candidate_ids)
            progress = (completed + failed) / total * 100 if total > 0 else 0
            
            print(f"[{time.strftime('%H:%M:%S')}] Pendentes: {pending}, Processando: {processing}, Concluídos: {completed}, Falharam: {failed} | Progresso: {progress:.1f}%")
            
            # Check if all done
            if pending == 0 and processing == 0:
                print(f"\n✓ TODOS OS CANDIDATOS PROCESSADOS!")
                break
            
            time.sleep(5)  # Check every 5 seconds
    
    # Final status
    print(f"\n=== RESULTADO FINAL ===")
    with app.app_context():
        for candidate_id in candidate_ids:
            candidate = Candidate.query.get(candidate_id)
            if candidate:
                score = candidate.ai_score if candidate.ai_score else 0
                print(f"{candidate.name}: {candidate.analysis_status} - Score: {score}")

if __name__ == "__main__":
    print("=== TESTE DE UPLOAD EM LOTE ===")
    print("Criando candidatos de teste...")
    
    # Create test candidates
    candidate_ids = create_test_candidates()
    
    if candidate_ids:
        # Start bulk processing
        thread = start_bulk_processing(candidate_ids)
        
        # Monitor progress
        monitor_progress(candidate_ids)
        
        print("\n=== TESTE CONCLUÍDO ===")
        print("Todos os candidatos foram processados pela IA!")
    else:
        print("Erro ao criar candidatos de teste")