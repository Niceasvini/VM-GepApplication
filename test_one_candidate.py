#!/usr/bin/env python3
"""
Script para testar reprocessamento de um candidato
"""

import os
import sys
import time
from datetime import datetime

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://postgres.bndkpowgvagtlxwmthma:5585858Vini%40@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'

from app import app, db
from models import Candidate
from ai_service import analyze_resume

def test_one_candidate():
    """
    Testa reprocessamento de um candidato
    """
    print("🔍 Testando reprocessamento de um candidato...")
    
    with app.app_context():
        # Buscar um candidato com formato antigo
        candidate = Candidate.query.filter_by(analysis_status='completed').first()
        
        if not candidate:
            print("❌ Nenhum candidato encontrado")
            return
        
        if '## Análise Detalhada' in candidate.ai_analysis:
            print("❌ Candidato já tem formato novo")
            return
        
        print(f"📄 Candidato: {candidate.name}")
        print(f"📝 Análise atual: {candidate.ai_analysis[:100]}...")
        
        try:
            # Marcar como processando
            candidate.analysis_status = 'processing'
            db.session.commit()
            
            print("🔄 Iniciando reprocessamento...")
            
            # Executar análise completa
            result = analyze_resume(candidate.file_path, candidate.file_type, candidate.job)
            
            if result and 'score' in result:
                # Atualizar candidato com nova análise
                candidate.ai_score = result['score']
                candidate.ai_summary = result.get('summary', '')
                candidate.ai_analysis = result.get('analysis', '')
                candidate.extracted_skills = result.get('skills', '')
                candidate.analysis_status = 'completed'
                candidate.analyzed_at = datetime.utcnow()
                
                db.session.commit()
                print(f"✅ Sucesso - Score: {result['score']}/10")
                
                # Mostrar nova análise
                print("\n📊 NOVA ANÁLISE:")
                print("-" * 50)
                if '## Análise Detalhada' in candidate.ai_analysis:
                    analysis_part = candidate.ai_analysis.split('## Análise Detalhada')[1][:300]
                    print(f"Análise Detalhada:{analysis_part}...")
                else:
                    print("Formato ainda não atualizado")
                
            else:
                raise Exception("Análise não retornou resultado válido")
                
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            candidate.analysis_status = 'failed'
            candidate.ai_analysis = f"ERRO NO REPROCESSAMENTO: {str(e)}"
            db.session.commit()

if __name__ == "__main__":
    test_one_candidate()