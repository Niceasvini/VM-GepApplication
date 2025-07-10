#!/usr/bin/env python3
"""
Debug script to test bulk upload functionality
"""
import os
import time
from datetime import datetime

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://postgres.bndkpowgvagtlxwmthma:5585858Vini%40@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'

from app import app, db
from models import Job, Candidate

def create_test_files():
    """Create test files for bulk upload"""
    test_files = [
        {'name': 'Ana Silva', 'content': 'Ana Silva\nDesenvolvedor Python\n3 anos experiência\nDjango, Flask, PostgreSQL'},
        {'name': 'Carlos Santos', 'content': 'Carlos Santos\nDesenvolvedor Full Stack\n4 anos experiência\nReact, Node.js, Python'},
        {'name': 'Fernanda Costa', 'content': 'Fernanda Costa\nEngenheira de Software\n5 anos experiência\nJava, Spring Boot, Python'},
        {'name': 'Rafael Lima', 'content': 'Rafael Lima\nDesenvolvedor Backend\n2 anos experiência\nPython, FastAPI, Docker'}
    ]
    
    created_files = []
    for i, data in enumerate(test_files):
        filename = f'debug_test_{i+1}.txt'
        filepath = f'uploads/{filename}'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(data['content'])
        
        created_files.append({
            'name': data['name'],
            'filename': filename,
            'filepath': filepath,
            'content': data['content']
        })
        
        print(f"✅ Created: {filename}")
    
    return created_files

def test_bulk_upload_simulation():
    """Simulate bulk upload process"""
    print("=== SIMULANDO UPLOAD EM LOTE ===")
    
    with app.app_context():
        # Get or create a job
        job = Job.query.first()
        if not job:
            print("❌ Nenhuma vaga encontrada")
            return
        
        print(f"📋 Vaga: {job.title}")
        
        # Create test files
        test_files = create_test_files()
        print(f"📁 Arquivos criados: {len(test_files)}")
        
        # Simulate the bulk upload process
        candidate_ids = []
        for file_data in test_files:
            candidate = Candidate(
                name=file_data['name'],
                email=f"{file_data['name'].lower().replace(' ', '')}@test.com",
                phone='(11) 99999-9999',
                filename=file_data['filename'],
                file_path=file_data['filepath'],
                file_type='txt',
                job_id=job.id,
                status='pending',
                analysis_status='pending'
            )
            
            db.session.add(candidate)
            db.session.commit()
            candidate_ids.append(candidate.id)
            print(f"✅ Candidato criado: {candidate.name} (ID: {candidate.id})")
        
        # Start background processing
        print(f"\n🚀 INICIANDO PROCESSAMENTO EM LOTE")
        print(f"Total candidatos: {len(candidate_ids)}")
        
        from background_processor import start_background_analysis
        thread = start_background_analysis(candidate_ids)
        
        print(f"Thread iniciada: {thread.is_alive()}")
        print("⏳ Aguardando processamento...")
        
        # Monitor progress
        for i in range(30):  # Monitor for 30 seconds
            time.sleep(1)
            
            # Check status
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
            
            print(f"[{i+1}s] Pendentes: {pending}, Processando: {processing}, Concluídos: {completed}, Falharam: {failed}")
            
            # Check if all done
            if pending == 0 and processing == 0:
                print("🎉 TODOS OS CANDIDATOS PROCESSADOS!")
                break
        
        # Final results
        print(f"\n=== RESULTADOS FINAIS ===")
        for candidate_id in candidate_ids:
            candidate = Candidate.query.get(candidate_id)
            if candidate:
                score = candidate.ai_score if candidate.ai_score else 0
                print(f"{candidate.name}: {candidate.analysis_status} - Score: {score}")

if __name__ == "__main__":
    test_bulk_upload_simulation()