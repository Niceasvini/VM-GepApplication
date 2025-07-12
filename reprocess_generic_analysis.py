#!/usr/bin/env python3
"""
Script para reprocessar candidatos com análise genérica
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

def find_generic_candidates():
    """
    Encontra candidatos com análise genérica que precisa ser reprocessada
    """
    print("🔍 Procurando candidatos com análise genérica...")
    
    with app.app_context():
        # Buscar candidatos com análise no formato antigo
        candidates_to_reprocess = []
        
        # Buscar todos os candidatos com análise completada
        completed_candidates = Candidate.query.filter_by(analysis_status='completed').all()
        
        for candidate in completed_candidates:
            if candidate.ai_analysis:
                # Verificar se NÃO tem o novo formato
                if '## Análise Detalhada' not in candidate.ai_analysis:
                    candidates_to_reprocess.append(candidate)
                    print(f"   📄 {candidate.name} - Formato antigo detectado")
        
        print(f"\n✅ Encontrados {len(candidates_to_reprocess)} candidatos para reprocessar")
        return candidates_to_reprocess

def reprocess_candidate(candidate):
    """
    Reprocessa um candidato individual
    """
    try:
        print(f"🔄 Reprocessando: {candidate.name}")
        
        # Marcar como processando
        candidate.analysis_status = 'processing'
        db.session.commit()
        
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
            print(f"   ✅ Sucesso - Score: {result['score']}/10")
            return True
        else:
            raise Exception("Análise não retornou resultado válido")
            
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        candidate.analysis_status = 'failed'
        candidate.ai_analysis = f"ERRO NO REPROCESSAMENTO: {str(e)}"
        db.session.commit()
        return False

def main():
    """
    Função principal
    """
    print("🚀 INICIANDO REPROCESSAMENTO DE ANÁLISES GENÉRICAS")
    print("=" * 60)
    
    # Encontrar candidatos para reprocessar
    candidates = find_generic_candidates()
    
    if not candidates:
        print("✅ Nenhum candidato com análise genérica encontrado!")
        return
    
    # Limitar para teste
    if len(candidates) > 10:
        print(f"⚠️  Limitando para 10 candidatos para teste")
        candidates = candidates[:10]
    
    # Confirmar reprocessamento
    print(f"\n⚠️  Deseja reprocessar {len(candidates)} candidatos? (y/n): ", end="")
    response = input().strip().lower()
    
    if response not in ['y', 'yes', 's', 'sim']:
        print("❌ Cancelado pelo usuário")
        return
    
    # Reprocessar candidatos
    print("\n🔄 INICIANDO REPROCESSAMENTO...")
    print("-" * 40)
    
    success_count = 0
    failed_count = 0
    
    with app.app_context():
        for i, candidate in enumerate(candidates, 1):
            print(f"\n[{i}/{len(candidates)}]", end=" ")
            
            if reprocess_candidate(candidate):
                success_count += 1
            else:
                failed_count += 1
            
            # Delay entre requisições
            time.sleep(2)
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL")
    print(f"✅ Sucessos: {success_count}")
    print(f"❌ Falhas: {failed_count}")
    print(f"📈 Total processado: {success_count + failed_count}")
    
    if success_count > 0:
        print(f"\n🎉 {success_count} candidatos reprocessados com sucesso!")
    
    if failed_count > 0:
        print(f"\n⚠️  {failed_count} candidatos falharam no reprocessamento")

if __name__ == "__main__":
    main()