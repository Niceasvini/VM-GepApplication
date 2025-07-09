#!/usr/bin/env python3
"""
Fix and complete the processing of candidates
"""
import os
import time
import logging
from datetime import datetime
from app import app, db
from models import Candidate
from file_processor import extract_text_from_file
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure OpenAI client
client = OpenAI(
    api_key="sk-08e53165834948c8b96fe8ec44a12baf",
    base_url="https://api.deepseek.com/v1"
)

def fix_and_process_candidates():
    """Fix stuck candidates and process them"""
    with app.app_context():
        # Reset all stuck candidates
        stuck_candidates = Candidate.query.filter(
            Candidate.analysis_status.in_(['processing', 'pending'])
        ).all()
        
        print(f"Found {len(stuck_candidates)} candidates to process")
        
        for candidate in stuck_candidates:
            try:
                print(f"\nProcessing: {candidate.name}")
                
                # Update status to processing
                candidate.analysis_status = 'processing'
                db.session.commit()
                
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

- Considere a relevância das experiências e habilidades em relação à vaga.
- Avalie a formação acadêmica e se ela é adequada para a posição.
- Com base na soma ponderada desses critérios, atribua uma *nota final com até duas casas decimais*, entre 0 e 10.
- Retorne apenas a nota final, com até duas casas decimais (ex: 7.91 ou 6.25), sem comentários ou explicações.

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
                
                print(f"Score: {score}")
                
                # Generate analysis
                analysis_response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{
                        "role": "user",
                        "content": f"""
Você é um analista de currículos. Analise o currículo abaixo para a vaga '{candidate.job.title}'.

Retorne:
- Um resumo estruturado do currículo
- Uma análise crítica com base na vaga (alinhamento técnico, gaps e recomendação)

Use o seguinte formato:

### RESUMO
(Resumo estruturado)

### ANÁLISE
1. Alinhamento Técnico: ...
2. Gaps Técnicos: ...
3. Recomendação Final: Sim / Parcial / Não

Currículo:
{resume_text}
"""
                    }],
                    max_tokens=800,
                    temperature=0.5
                )
                
                analysis = analysis_response.choices[0].message.content.strip()
                
                # Extract summary (first part of analysis)
                if "### RESUMO" in analysis:
                    summary_part = analysis.split("### ANÁLISE")[0].replace("### RESUMO", "").strip()
                    analysis_part = analysis.split("### ANÁLISE")[1].strip() if "### ANÁLISE" in analysis else analysis
                else:
                    summary_part = f"Candidato: {candidate.name} - Vaga: {candidate.job.title}"
                    analysis_part = analysis
                
                # Update candidate with results
                candidate.ai_score = score
                candidate.ai_summary = summary_part
                candidate.ai_analysis = analysis_part
                candidate.analysis_status = 'completed'
                candidate.analyzed_at = datetime.utcnow()
                
                db.session.commit()
                
                print(f"✓ Completed: {candidate.name} - Score: {score}")
                
            except Exception as e:
                print(f"✗ Error processing {candidate.name}: {str(e)}")
                candidate.analysis_status = 'failed'
                candidate.ai_summary = f'Erro na análise: {str(e)}'
                candidate.ai_score = 0.0
                db.session.commit()
        
        # Show final results
        print("\n" + "="*60)
        print("FINAL RESULTS")
        print("="*60)
        
        all_candidates = Candidate.query.all()
        for candidate in all_candidates:
            status_emoji = "✓" if candidate.analysis_status == 'completed' else "✗"
            print(f"{status_emoji} {candidate.name}: {candidate.ai_score}/10 - {candidate.analysis_status}")

if __name__ == "__main__":
    fix_and_process_candidates()