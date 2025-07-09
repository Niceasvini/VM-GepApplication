import json
import os
import logging
from file_processor import extract_text_from_file

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

def analyze_resume(file_path, file_type, job):
    """
    Analyze a resume using OpenAI GPT-4o model
    Returns a dictionary with score, summary, analysis, and skills
    """
    try:
        # Extract text from the resume
        resume_text = extract_text_from_file(file_path, file_type)
        
        # Prepare the analysis prompt
        prompt = f"""
        Você é um especialista em recrutamento da empresa "Viana e Moura". 
        Analise o currículo abaixo para a vaga especificada e forneça uma avaliação completa.
        
        VAGA:
        Título: {job.title}
        Descrição: {job.description}
        Requisitos: {job.requirements}
        {f"DCF: {job.dcf_content}" if job.dcf_content else ""}
        
        CURRÍCULO:
        {resume_text}
        
        Forneça sua análise no formato JSON com os seguintes campos:
        {{
            "score": [pontuação de 0.0 a 10.0, múltiplos de 0.5],
            "summary": "[resumo executivo do candidato em 2-3 frases]",
            "analysis": "[análise detalhada incluindo pontos fortes, fracos e adequação à vaga]",
            "skills": ["lista", "de", "habilidades", "técnicas", "identificadas"],
            "experience_years": [número estimado de anos de experiência],
            "education_level": "[nível educacional identificado]",
            "match_reasons": ["razões", "específicas", "para", "a", "pontuação"],
            "recommendations": ["recomendações", "para", "próximos", "passos"]
        }}
        
        Seja preciso, profissional e focado na adequação do candidato à vaga específica.
        """
        
        response = openai.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um especialista em recrutamento com 15 anos de experiência. "
                             "Analise currículos de forma objetiva e profissional, fornecendo insights "
                             "práticos para decisões de contratação. Sempre responda em português brasileiro."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=2000,
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Validate and clean the result
        analysis_result = {
            'score': max(0.0, min(10.0, float(result.get('score', 0)))),
            'summary': result.get('summary', 'Resumo não disponível'),
            'analysis': result.get('analysis', 'Análise não disponível'),
            'skills': result.get('skills', []),
            'experience_years': result.get('experience_years', 0),
            'education_level': result.get('education_level', 'Não informado'),
            'match_reasons': result.get('match_reasons', []),
            'recommendations': result.get('recommendations', [])
        }
        
        return analysis_result
        
    except Exception as e:
        logging.error(f"Error analyzing resume: {e}")
        return {
            'score': 0.0,
            'summary': 'Erro na análise do currículo',
            'analysis': f'Não foi possível analisar o currículo: {str(e)}',
            'skills': [],
            'experience_years': 0,
            'education_level': 'Não informado',
            'match_reasons': [],
            'recommendations': []
        }

def generate_batch_analysis_report(candidates):
    """
    Generate a comprehensive report for multiple candidates
    """
    try:
        candidates_data = []
        for candidate in candidates:
            candidates_data.append({
                'name': candidate.name,
                'score': candidate.ai_score,
                'summary': candidate.ai_summary,
                'skills': candidate.get_skills_list(),
                'status': candidate.status
            })
        
        prompt = f"""
        Analise os seguintes candidatos e gere um relatório executivo de recrutamento:
        
        CANDIDATOS:
        {json.dumps(candidates_data, indent=2, ensure_ascii=False)}
        
        Forneça um relatório no formato JSON com:
        {{
            "executive_summary": "[resumo executivo dos candidatos]",
            "top_candidates": ["lista", "dos", "3", "melhores", "candidatos"],
            "skills_analysis": "[análise das habilidades mais comuns]",
            "recommendations": ["recomendações", "para", "o", "processo", "seletivo"],
            "score_distribution": "[análise da distribuição de pontuações]"
        }}
        """
        
        response = openai.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um consultor sênior de RH especializado em análise de candidatos."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1500,
            temperature=0.3
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logging.error(f"Error generating batch analysis: {e}")
        return {
            'executive_summary': 'Erro na geração do relatório',
            'top_candidates': [],
            'skills_analysis': 'Análise não disponível',
            'recommendations': [],
            'score_distribution': 'Distribuição não disponível'
        }
