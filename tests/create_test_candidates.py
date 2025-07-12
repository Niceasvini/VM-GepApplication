#!/usr/bin/env python3
"""
Create test candidates for testing parallel processing
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Job, Candidate
from datetime import datetime

def create_test_candidates():
    """Create test candidates for parallel processing"""
    with app.app_context():
        # Get or create a test user
        test_user = User.query.filter_by(username='test_admin').first()
        if not test_user:
            test_user = User(
                username='test_admin',
                email='admin@test.com',
                role='admin'
            )
            test_user.set_password('test123')
            db.session.add(test_user)
            db.session.commit()
            print("Created test user")
        
        # Get or create a test job
        test_job = Job.query.filter_by(title='Desenvolvedor Python Teste').first()
        if not test_job:
            test_job = Job(
                title='Desenvolvedor Python Teste',
                description='Vaga para desenvolvedor Python com experiência em Flask',
                requirements='Python, Flask, SQL, Git',
                created_by=test_user.id
            )
            db.session.add(test_job)
            db.session.commit()
            print("Created test job")
        
        # Create test resume files
        test_resumes = [
            {
                'name': 'João Silva',
                'email': 'joao@email.com',
                'content': '''João Silva
Email: joao@email.com
Telefone: (11) 99999-9999

Experiência:
- Desenvolvedor Python Senior - 5 anos
- Flask, Django, SQLAlchemy
- Desenvolvimento de APIs REST
- Testes automatizados com pytest

Formação:
- Ciências da Computação - USP
- Especialização em Desenvolvimento Web
'''
            },
            {
                'name': 'Maria Santos',
                'email': 'maria@email.com',
                'content': '''Maria Santos
Email: maria@email.com
Telefone: (11) 88888-8888

Experiência:
- Desenvolvedora Full Stack - 3 anos
- Python, JavaScript, React
- Banco de dados MySQL, PostgreSQL
- Metodologias ágeis

Formação:
- Engenharia de Software - UNICAMP
- Curso de Python Avançado
'''
            },
            {
                'name': 'Carlos Oliveira',
                'email': 'carlos@email.com',
                'content': '''Carlos Oliveira
Email: carlos@email.com
Telefone: (11) 77777-7777

Experiência:
- Analista de Sistemas - 2 anos
- Python básico, SQL avançado
- Análise de dados com pandas
- Relatórios automatizados

Formação:
- Análise de Sistemas - FATEC
- Certificação em Python
'''
            }
        ]
        
        # Create uploads directory if it doesn't exist
        os.makedirs('uploads', exist_ok=True)
        
        created_candidates = []
        
        for i, resume_data in enumerate(test_resumes):
            # Check if candidate already exists
            existing = Candidate.query.filter_by(
                name=resume_data['name'],
                job_id=test_job.id
            ).first()
            
            if existing:
                print(f"Candidate {resume_data['name']} already exists")
                continue
            
            # Create resume file
            filename = f"test_resume_{i+1}.txt"
            filepath = os.path.join('uploads', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(resume_data['content'])
            
            # Create candidate record
            candidate = Candidate(
                name=resume_data['name'],
                email=resume_data['email'],
                phone='(11) 99999-9999',
                filename=filename,
                file_path=filepath,
                file_type='txt',
                job_id=test_job.id,
                analysis_status='pending'
            )
            
            db.session.add(candidate)
            created_candidates.append(candidate)
            print(f"Created candidate: {resume_data['name']}")
        
        db.session.commit()
        print(f"Created {len(created_candidates)} test candidates")
        return created_candidates

if __name__ == "__main__":
    candidates = create_test_candidates()
    print(f"Test setup complete! Created {len(candidates)} candidates ready for processing.")