#!/usr/bin/env python3
"""
Find candidates with outdated analysis format that need reprocessing
"""

import os
import sys
from datetime import datetime

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://postgres.bndkpowgvagtlxwmthma:5585858Vini%40@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'

from app import app, db
from models import Candidate, Job

def find_outdated_candidates():
    """Find candidates with outdated analysis format"""
    with app.app_context():
        # Find candidates with completed analysis but old format
        candidates = Candidate.query.filter(
            Candidate.analysis_status == 'completed',
            Candidate.ai_analysis != None,
            Candidate.ai_analysis != ''
        ).all()
        
        outdated_candidates = []
        
        for candidate in candidates:
            # Check if analysis doesn't have the new format
            if '## Análise Detalhada' not in candidate.ai_analysis:
                outdated_candidates.append(candidate)
        
        print(f"📊 RELATÓRIO DE ANÁLISES DESATUALIZADAS")
        print(f"=" * 50)
        print(f"Total de candidatos analisados: {len(candidates)}")
        print(f"Candidatos com análise desatualizada: {len(outdated_candidates)}")
        print(f"Candidatos com análise atualizada: {len(candidates) - len(outdated_candidates)}")
        
        if outdated_candidates:
            print(f"\n🔄 CANDIDATOS QUE PRECISAM DE REPROCESSAMENTO:")
            print("-" * 50)
            
            for candidate in outdated_candidates:
                print(f"ID: {candidate.id}")
                print(f"Nome: {candidate.name}")
                print(f"Vaga: {candidate.job.title}")
                print(f"Score: {candidate.ai_score}")
                print(f"URL: /candidates/{candidate.id}")
                print(f"Análise atual: {candidate.ai_analysis[:100]}...")
                print("-" * 30)
        
        return outdated_candidates

def reprocess_outdated_batch(max_candidates=10):
    """Reprocess a batch of outdated candidates"""
    with app.app_context():
        outdated = find_outdated_candidates()
        
        if not outdated:
            print("✅ Todos os candidatos já possuem análise atualizada!")
            return
        
        # Process first batch
        batch = outdated[:max_candidates]
        print(f"\n🚀 INICIANDO REPROCESSAMENTO DE {len(batch)} CANDIDATOS...")
        
        from background_processor import start_background_analysis
        candidate_ids = [c.id for c in batch]
        
        # Reset status for reprocessing
        for candidate in batch:
            candidate.analysis_status = 'pending'
            candidate.ai_analysis = None
            candidate.ai_summary = None
            candidate.analyzed_at = None
        
        db.session.commit()
        print("✅ Status resetado para reprocessamento")
        
        # Start background processing
        start_background_analysis(candidate_ids)
        print(f"✅ Reprocessamento iniciado para {len(candidate_ids)} candidatos")
        
        print("\n📋 CANDIDATOS EM REPROCESSAMENTO:")
        for candidate in batch:
            print(f"• {candidate.name} (ID: {candidate.id})")

if __name__ == "__main__":
    print("🔍 Buscando candidatos com análise desatualizada...")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "reprocess":
            max_batch = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            reprocess_outdated_batch(max_batch)
        elif sys.argv[1] == "count":
            outdated = find_outdated_candidates()
            print(f"\n📈 RESUMO: {len(outdated)} candidatos precisam de reprocessamento")
    else:
        find_outdated_candidates()