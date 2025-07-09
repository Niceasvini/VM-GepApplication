#!/usr/bin/env python3
"""
Test AI processing directly without Flask app
"""
import os
from openai import OpenAI

# Test DeepSeek API
client = OpenAI(
    api_key="sk-08e53165834948c8b96fe8ec44a12baf",
    base_url="https://api.deepseek.com/v1"
)

def test_ai_processing():
    """Test AI processing directly"""
    try:
        print("Testing DeepSeek API connection...")
        
        # Simple test
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "user",
                "content": "Teste simples: responda apenas 'OK'"
            }],
            max_tokens=10,
            temperature=0.1
        )
        
        print(f"✓ DeepSeek API works: {response.choices[0].message.content}")
        
        # Test resume scoring
        resume_text = """João Silva
Email: joao@email.com
Telefone: (11) 99999-9999

Experiência:
- Desenvolvedor Python Senior - 5 anos
- Flask, Django, SQLAlchemy
- Desenvolvimento de APIs REST
- Testes automatizados com pytest

Formação:
- Ciências da Computação - USP
- Especialização em Desenvolvimento Web"""
        
        print("\nTesting resume scoring...")
        score_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "user",
                "content": f"Avalie este currículo para a vaga 'Desenvolvedor Python' de 0 a 10. Responda apenas a nota (ex: 7.5):\n\n{resume_text}"
            }],
            max_tokens=20,
            temperature=0.3
        )
        
        score_text = score_response.choices[0].message.content.strip()
        print(f"✓ Score response: {score_text}")
        
        # Test analysis
        print("\nTesting resume analysis...")
        analysis_response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "user",
                "content": f"Resumo do candidato João Silva para vaga 'Desenvolvedor Python' (máximo 200 palavras):\n\n{resume_text}"
            }],
            max_tokens=300,
            temperature=0.5
        )
        
        analysis = analysis_response.choices[0].message.content.strip()
        print(f"✓ Analysis response: {analysis[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_ai_processing()
    if success:
        print("\n✓ All AI tests passed!")
    else:
        print("\n✗ AI tests failed!")