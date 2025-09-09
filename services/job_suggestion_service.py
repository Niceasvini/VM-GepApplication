"""
Serviço de sugestão de IA para criação de vagas
"""
import os
import logging
from openai import OpenAI

def get_openai_client():
    """Get OpenAI client with proper API key loading"""
    from dotenv import load_dotenv
    load_dotenv()
    
    deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        deepseek_api_key = os.environ.get("OPENAI_API_KEY")
    
    if not deepseek_api_key:
        raise ValueError("DEEPSEEK_API_KEY ou OPENAI_API_KEY não encontrada")
    
    return OpenAI(
        api_key=deepseek_api_key,
        base_url="https://api.deepseek.com/v1"
    )

def generate_job_suggestions(job_title):
    """
    Gera sugestões de descrição e requisitos para uma vaga baseado no título
    """
    try:
        prompt = f"""
RH especialista. Vaga: "{job_title}"

Gere JSON rápido e completo:
{{
    "description": "Descrição da vaga, responsabilidades e benefícios",
    "requirements": "MÍNIMO EXIGIDO:\\n• Formação\\n• Experiência\\n• Conhecimentos técnicos\\n• Habilidades\\n\\nDESEJÁVEL:\\n• Formação extra\\n• Experiência adicional\\n• Soft skills\\n• Certificações"
}}

Seja direto, específico e profissional.
"""

        openai = get_openai_client()
        response = openai.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.1,
            timeout=25
        )
        
        result = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        import json
        try:
            # Remove any markdown formatting if present
            if result.startswith('```json'):
                result = result.replace('```json', '').replace('```', '').strip()
            elif result.startswith('```'):
                result = result.replace('```', '').strip()
            
            suggestions = json.loads(result)
            
            # Validate the response structure
            if 'description' in suggestions and 'requirements' in suggestions:
                return {
                    'success': True,
                    'description': suggestions['description'],
                    'requirements': suggestions['requirements']
                }
            else:
                raise ValueError("Estrutura de resposta inválida")
                
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao fazer parse do JSON: {e}")
            logging.error(f"Resposta da IA: {result}")
            
            # Fallback: try to extract content manually
            return extract_suggestions_manually(result)
            
    except Exception as e:
        logging.error(f"Erro na geração de sugestões: {e}")
        return {
            'success': False,
            'error': str(e),
            'description': '',
            'requirements': ''
        }

def extract_suggestions_manually(text):
    """
    Extrai sugestões manualmente quando o JSON não é válido
    """
    try:
        lines = text.split('\n')
        description = ""
        requirements = ""
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if 'description' in line.lower() or 'descrição' in line.lower():
                current_section = 'description'
                continue
            elif 'requirements' in line.lower() or 'requisitos' in line.lower() or 'habilidades' in line.lower():
                current_section = 'requirements'
                continue
            
            if current_section == 'description':
                description += line + '\n'
            elif current_section == 'requirements':
                requirements += line + '\n'
        
        return {
            'success': True,
            'description': description.strip(),
            'requirements': requirements.strip()
        }
        
    except Exception as e:
        logging.error(f"Erro na extração manual: {e}")
        return {
            'success': False,
            'error': str(e),
            'description': '',
            'requirements': ''
        }

def get_job_title_suggestions(partial_title):
    """
    Gera sugestões de títulos de vaga baseado em texto parcial
    """
    try:
        prompt = f"""
Você é um especialista em Recursos Humanos. 

Com base no texto "{partial_title}", sugira 5 títulos de vagas profissionais e atrativos.

INSTRUÇÕES:
- Use terminologia padrão do mercado brasileiro
- Seja específico e claro
- Considere diferentes níveis (Júnior, Pleno, Sênior)
- Mantenha títulos concisos mas descritivos

Retorne APENAS uma lista JSON:
["Título 1", "Título 2", "Título 3", "Título 4", "Título 5"]
"""

        openai = get_openai_client()
        response = openai.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.4,
            timeout=30
        )
        
        result = response.choices[0].message.content.strip()
        
        # Clean up response
        if result.startswith('```json'):
            result = result.replace('```json', '').replace('```', '').strip()
        elif result.startswith('```'):
            result = result.replace('```', '').strip()
        
        import json
        suggestions = json.loads(result)
        
        return {
            'success': True,
            'suggestions': suggestions
        }
        
    except Exception as e:
        logging.error(f"Erro na geração de sugestões de título: {e}")
        return {
            'success': False,
            'error': str(e),
            'suggestions': []
        }
