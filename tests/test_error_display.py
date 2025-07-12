#!/usr/bin/env python3
"""
Test script to create a candidate with error for testing error display
"""

import os
import sys
from datetime import datetime

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://postgres.bndkpowgvagtlxwmthma:5585858Vini%40@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'

from app import app, db
from models import Candidate, Job

def create_test_error_candidate():
    """Create a test candidate with error status"""
    with app.app_context():
        # Find the first job
        job = Job.query.first()
        if not job:
            print("❌ No jobs found! Create a job first.")
            return
        
        # Create candidate with error
        candidate = Candidate(
            name="Teste Erro Detalhado",
            email="teste.erro@example.com",
            phone="(11) 99999-9999",
            filename="teste_erro.pdf",
            file_path="uploads/teste_erro.pdf",
            file_type="pdf",
            job_id=job.id,
            analysis_status="failed",
            ai_score=0.0,
            ai_summary="FALHA: Erro na extração de texto: Não foi possível extrair o conteúdo do arquivo uploads/teste_erro.pdf. O arquivo pode estar corrompido ou em formato não suportado.",
            ai_analysis="ANÁLISE FALHOU: Erro na extração de texto: Não foi possível extrair o conteúdo do arquivo uploads/teste_erro.pdf. O arquivo pode estar corrompido ou em formato não suportado.",
            uploaded_at=datetime.utcnow()
        )
        
        db.session.add(candidate)
        db.session.commit()
        
        print(f"✅ Candidato de teste criado com ID: {candidate.id}")
        print(f"   Nome: {candidate.name}")
        print(f"   Status: {candidate.analysis_status}")
        print(f"   Erro: {candidate.ai_summary}")
        print(f"   Acesse: /candidates/{candidate.id}")

def create_api_error_candidate():
    """Create a test candidate with API error"""
    with app.app_context():
        # Find the first job
        job = Job.query.first()
        if not job:
            print("❌ No jobs found! Create a job first.")
            return
        
        # Create candidate with API error
        candidate = Candidate(
            name="Teste API Timeout",
            email="teste.api@example.com",
            phone="(11) 88888-8888",
            filename="teste_api.pdf",
            file_path="uploads/teste_api.pdf",
            file_type="pdf",
            job_id=job.id,
            analysis_status="failed",
            ai_score=0.0,
            ai_summary="FALHA: Timeout na API: A análise demorou muito para responder. Isso pode ocorrer quando o serviço de IA está sobrecarregado.",
            ai_analysis="ANÁLISE FALHOU: Timeout na API: A análise demorou muito para responder. Isso pode ocorrer quando o serviço de IA está sobrecarregado.",
            uploaded_at=datetime.utcnow()
        )
        
        db.session.add(candidate)
        db.session.commit()
        
        print(f"✅ Candidato de teste criado com ID: {candidate.id}")
        print(f"   Nome: {candidate.name}")
        print(f"   Status: {candidate.analysis_status}")
        print(f"   Erro: {candidate.ai_summary}")
        print(f"   Acesse: /candidates/{candidate.id}")

def list_failed_candidates():
    """List all failed candidates"""
    with app.app_context():
        candidates = Candidate.query.filter_by(analysis_status='failed').all()
        
        if not candidates:
            print("❌ Nenhum candidato com falha encontrado.")
            return
        
        print(f"📋 Candidatos com falha ({len(candidates)}):")
        for candidate in candidates:
            print(f"   ID: {candidate.id} - {candidate.name}")
            print(f"   Erro: {candidate.ai_summary}")
            print(f"   URL: /candidates/{candidate.id}")
            print("-" * 50)

if __name__ == "__main__":
    print("🧪 Testando sistema de exibição de erros...")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_failed_candidates()
        elif sys.argv[1] == "api":
            create_api_error_candidate()
        else:
            create_test_error_candidate()
    else:
        create_test_error_candidate()
        create_api_error_candidate()
        print("\n" + "="*50)
        list_failed_candidates()