#!/usr/bin/env python3
"""
Real-time processing monitor and controller
"""
import os
import sys
import time
import threading
import logging
from datetime import datetime
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure OpenAI client
client = OpenAI(
    api_key="sk-08e53165834948c8b96fe8ec44a12baf",
    base_url="https://api.deepseek.com/v1"
)

class ProcessingMonitor:
    def __init__(self):
        self.active_threads = {}
        self.processing_status = {}
        
    def process_candidate_simple(self, candidate_data):
        """Process a candidate with simple AI integration"""
        try:
            candidate_id = candidate_data['id']
            name = candidate_data['name']
            resume_text = candidate_data['resume_text']
            job_title = candidate_data['job_title']
            
            logging.info(f"Processing candidate {candidate_id}: {name}")
            
            # Generate score
            score_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user",
                    "content": f"""
Você é um avaliador técnico especializado em recrutamento.

Dê uma nota de 0 a 10 para o currículo abaixo com base na vaga '{job_title}', considerando:

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
            
            logging.info(f"Generated score {score} for candidate {candidate_id}")
            
            # Generate analysis
            analysis_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user",
                    "content": f"""
Você é um analista de currículos. Analise o currículo abaixo para a vaga '{job_title}'.

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
            
            result = {
                'candidate_id': candidate_id,
                'score': score,
                'analysis': analysis,
                'status': 'completed',
                'processed_at': datetime.now().isoformat()
            }
            
            logging.info(f"Successfully processed candidate {candidate_id} with score {score}")
            return result
            
        except Exception as e:
            logging.error(f"Error processing candidate {candidate_id}: {str(e)}")
            return {
                'candidate_id': candidate_id,
                'score': 0.0,
                'analysis': f'Erro na análise: {str(e)}',
                'status': 'failed',
                'processed_at': datetime.now().isoformat()
            }
    
    def test_with_sample_data(self):
        """Test with sample candidate data"""
        sample_candidates = [
            {
                'id': 1,
                'name': 'João Silva',
                'resume_text': '''João Silva
Email: joao@email.com
Telefone: (11) 99999-9999

Experiência:
- Desenvolvedor Python Senior - 5 anos
- Flask, Django, SQLAlchemy
- Desenvolvimento de APIs REST
- Testes automatizados com pytest

Formação:
- Ciências da Computação - USP
- Especialização em Desenvolvimento Web''',
                'job_title': 'Desenvolvedor Python'
            },
            {
                'id': 2,
                'name': 'Maria Santos',
                'resume_text': '''Maria Santos
Email: maria@email.com
Telefone: (11) 88888-8888

Experiência:
- Desenvolvedora Java - 3 anos
- Spring Boot, Hibernate
- Desenvolvimento de aplicações web
- Conhecimento básico em Python

Formação:
- Engenharia de Software - UNICAMP
- Curso de Python - Udemy''',
                'job_title': 'Desenvolvedor Python'
            },
            {
                'id': 3,
                'name': 'Carlos Oliveira',
                'resume_text': '''Carlos Oliveira
Email: carlos@email.com
Telefone: (11) 77777-7777

Experiência:
- Desenvolvedor Frontend - 2 anos
- React, JavaScript, HTML/CSS
- Conhecimento básico em backend
- Interesse em aprender Python

Formação:
- Análise e Desenvolvimento de Sistemas - FIAP
- Bootcamp Fullstack''',
                'job_title': 'Desenvolvedor Python'
            }
        ]
        
        print("Testing AI processing with sample candidates...")
        results = []
        
        for candidate in sample_candidates:
            print(f"\nProcessing {candidate['name']}...")
            result = self.process_candidate_simple(candidate)
            results.append(result)
            
            print(f"Result: {result['status']}")
            print(f"Score: {result['score']}")
            print(f"Analysis preview: {result['analysis'][:100]}...")
            print("-" * 50)
        
        return results

def main():
    monitor = ProcessingMonitor()
    
    # Test the system
    results = monitor.test_with_sample_data()
    
    print("\n" + "="*60)
    print("PROCESSING RESULTS SUMMARY")
    print("="*60)
    
    for result in results:
        print(f"Candidate {result['candidate_id']}: {result['status']} - Score: {result['score']}")
    
    successful = len([r for r in results if r['status'] == 'completed'])
    print(f"\nSUCCESS: {successful}/{len(results)} candidates processed successfully")
    
    if successful == len(results):
        print("✓ All candidates processed successfully!")
        print("✓ AI integration is working correctly!")
        print("✓ System is ready for production!")
        return True
    else:
        print("✗ Some candidates failed to process")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)