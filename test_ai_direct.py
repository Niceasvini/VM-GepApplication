#!/usr/bin/env python3
"""
Test AI processing directly without Flask app
"""
import os
import sys
from openai import OpenAI

# Configure OpenAI client
client = OpenAI(
    api_key="sk-08e53165834948c8b96fe8ec44a12baf",
    base_url="https://api.deepseek.com/v1"
)

def test_ai_processing():
    """Test AI processing directly"""
    
    test_resume = """
João Silva
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
"""
    
    job_title = "Desenvolvedor Python Teste"
    
    # Test scoring
    print("Testing scoring...")
    try:
        response = client.chat.completions.create(
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
{test_resume}
"""
            }],
            max_tokens=50,
            temperature=0.3
        )
        
        score_text = response.choices[0].message.content.strip()
        print(f"Score response: {score_text}")
        
        # Extract score
        if ":" in score_text:
            score = float(score_text.split(":")[-1].strip())
        else:
            score = float(score_text)
        
        print(f"Extracted score: {score}")
        
        # Test analysis
        print("\nTesting analysis...")
        
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
{test_resume}
"""
            }],
            max_tokens=800,
            temperature=0.5
        )
        
        analysis = analysis_response.choices[0].message.content.strip()
        print(f"Analysis: {analysis}")
        
        print("\n✓ AI processing working correctly!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_ai_processing()
    sys.exit(0 if success else 1)