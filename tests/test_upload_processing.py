#!/usr/bin/env python3
"""
Test bulk upload and AI processing with Supabase
"""
import os
import time
import threading
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

def create_test_candidates():
    """Create test candidates with resume files"""
    with app.app_context():
        # Get or create job
        job = Job.query.first()
        if not job:
            print("No job found, creating test job...")
            admin_user = User.query.first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@vianamoura.com',
                    role='admin'
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
            
            job = Job(
                title='Desenvolvedor Python',
                description='Desenvolvedor Python com experiência em Flask',
                requirements='Python, Flask, SQL, Git',
                dcf_content='Desenvolvimento de aplicações web',
                created_by=admin_user.id
            )
            db.session.add(job)
            db.session.commit()
        
        # Create test resume files and candidates
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

def process_candidate_with_ai(candidate_id):
    """Process candidate with AI analysis"""
    try:
        with app.app_context():
            candidate = Candidate.query.get(candidate_id)
            if not candidate:
                return False
            
            # Update status
            candidate.analysis_status = 'processing'
            db.session.commit()
            
            print(f"Processing candidate {candidate_id}: {candidate.name}")
            
            # Extract resume text
            resume_text = extract_text_from_file(candidate.file_path, candidate.file_type)
            if len(resume_text) > 3000:
                resume_text = resume_text[:3000]
            
            # Generate score
            score_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user",
                    "content": f"""
Você é um avaliador técnico especializado em recrutamento.

Dê uma nota de 0 a 10 para o currículo abaixo com base na vaga '{candidate.job.title}', considerando:

1. Experiência prática na área (peso 4)
2. Habilidades técnicas relevantes (peso 3)
3. Formação acadêmica (peso 2)
4. Clareza e estrutura do currículo (peso 1)

Retorne apenas a nota final, com até duas casas decimais (ex: 7.91 ou 6.25), sem comentários.

Exemplo:
Nota: 6.87

Currículo:
{resume_text}
"""
                }],
                max_tokens=50,
                temperature=0.3
            )
            
            score_text = score_response.choices[0].message.content.strip()
            if ":" in score_text:
                score = float(score_text.split(":")[-1].strip())
            else:
                score = float(score_text)
            
            # Generate analysis
            analysis_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user",
                    "content": f"""
Analise o currículo abaixo para a vaga '{candidate.job.title}'.

Retorne:
- Um resumo estruturado
- Uma análise crítica com recomendação

Formato:
### RESUMO
(Resumo do candidato)

### ANÁLISE
1. Alinhamento Técnico: ...
2. Gaps Técnicos: ...
3. Recomendação: Sim/Parcial/Não

Currículo:
{resume_text}
"""
                }],
                max_tokens=800,
                temperature=0.5
            )
            
            analysis = analysis_response.choices[0].message.content.strip()
            
            # Extract summary
            if "### RESUMO" in analysis:
                summary_part = analysis.split("### ANÁLISE")[0].replace("### RESUMO", "").strip()
                analysis_part = analysis.split("### ANÁLISE")[1].strip() if "### ANÁLISE" in analysis else analysis
            else:
                summary_part = f"Candidato: {candidate.name}"
                analysis_part = analysis
            
            # Update candidate
            candidate.ai_score = score
            candidate.ai_summary = summary_part
            candidate.ai_analysis = analysis_part
            candidate.analysis_status = 'completed'
            candidate.analyzed_at = datetime.utcnow()
            
            db.session.commit()
            
            print(f"✓ Completed: {candidate.name} - Score: {score}")
            return True
            
    except Exception as e:
        print(f"✗ Error processing candidate {candidate_id}: {str(e)}")
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

def test_bulk_processing():
    """Test bulk upload and processing"""
    print("=== TESTE DE UPLOAD EM LOTE E PROCESSAMENTO IA ===")
    
    # Create test candidates
    print("\n1. Criando candidatos de teste...")
    candidate_ids = create_test_candidates()
    
    # Process candidates
    print(f"\n2. Processando {len(candidate_ids)} candidatos com IA...")
    for candidate_id in candidate_ids:
        success = process_candidate_with_ai(candidate_id)
        if success:
            print(f"   ✓ Candidato {candidate_id} processado")
        else:
            print(f"   ✗ Candidato {candidate_id} falhou")
        time.sleep(1)  # Small delay between requests
    
    # Show results
    print("\n3. Resultados finais:")
    with app.app_context():
        candidates = Candidate.query.all()
        for candidate in candidates:
            status_emoji = "✓" if candidate.analysis_status == 'completed' else "✗"
            print(f"   {status_emoji} {candidate.name}: {candidate.ai_score}/10 - {candidate.analysis_status}")
    
    print("\n=== TESTE CONCLUÍDO ===")

if __name__ == "__main__":
    test_bulk_processing()