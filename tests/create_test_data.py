#!/usr/bin/env python3
"""
Create test data for debugging
"""
import os
from app import app, db
from models import Job, Candidate

def create_test_candidates():
    """Create test candidates for debugging"""
    with app.app_context():
        # Find existing job
        job = Job.query.first()
        if not job:
            # Create a test job
            job = Job(
                title="Desenvolvedor Python",
                description="Desenvolvedor Python com experiência em Flask",
                requirements="Python, Flask, SQL, Git",
                dcf_content="Desenvolvimento de aplicações web",
                created_by=1
            )
            db.session.add(job)
            db.session.commit()
            print(f"Created job: {job.title}")
        
        # Create test resume files
        test_resumes = [
            {
                'name': 'João Silva',
                'email': 'joao@email.com',
                'phone': '(11) 99999-9999',
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
                'phone': '(11) 88888-8888',
                'content': '''Maria Santos
Email: maria@email.com
Telefone: (11) 88888-8888

Experiência:
- Desenvolvedora Java - 3 anos
- Spring Boot, Hibernate
- Desenvolvimento de aplicações web
- Conhecimento básico em Python

Formação:
- Engenharia de Software - UNICAMP
- Curso de Python - Udemy
'''
            },
            {
                'name': 'Carlos Oliveira',
                'email': 'carlos@email.com',
                'phone': '(11) 77777-7777',
                'content': '''Carlos Oliveira
Email: carlos@email.com
Telefone: (11) 77777-7777

Experiência:
- Desenvolvedor Frontend - 2 anos
- React, JavaScript, HTML/CSS
- Conhecimento básico em backend
- Interesse em aprender Python

Formação:
- Análise e Desenvolvimento de Sistemas - FIAP
- Bootcamp Fullstack
'''
            }
        ]
        
        # Create resume files and candidates
        candidate_ids = []
        for i, resume in enumerate(test_resumes):
            # Create file
            filename = f"test_resume_{i+1}.txt"
            file_path = os.path.join('uploads', filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(resume['content'])
            
            # Create candidate
            candidate = Candidate(
                name=resume['name'],
                email=resume['email'],
                phone=resume['phone'],
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
            print(f"Created candidate: {candidate.name} (ID: {candidate.id})")
        
        return candidate_ids

if __name__ == "__main__":
    candidate_ids = create_test_candidates()
    print(f"\nCreated {len(candidate_ids)} test candidates")
    print("Candidate IDs:", candidate_ids)