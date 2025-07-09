import json
import os
import logging
import time
import hashlib
from file_processor import extract_text_from_file
from cache_service import analysis_cache

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
from openai import OpenAI

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
openai = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1",
    timeout=60.0  # 60 seconds timeout
)

def analyze_resume(file_path, file_type, job):
    """
    Analyze a resume using DeepSeek API with improved error handling
    Returns a dictionary with score, summary, analysis, and skills
    """
    try:
        logging.info(f"Starting analysis for file: {file_path}")
        
        # Extract text from the resume
        resume_text = extract_text_from_file(file_path, file_type)
        logging.info(f"Resume text extracted successfully, length: {len(resume_text)}")
        
        # Check cache first to avoid redundant API calls
        cached_result = analysis_cache.get_cached_analysis(resume_text, job.id)
        if cached_result:
            logging.info("Using cached analysis result")
            return cached_result
        
        # Check if API key is available
        if not DEEPSEEK_API_KEY:
            logging.error("DeepSeek API key not found in environment variables")
            raise Exception("API key not configured")
        
        # Limit resume text to avoid token limits
        if len(resume_text) > 8000:
            resume_text = resume_text[:8000] + "..."
            logging.info("Resume text truncated to fit token limits")
        
        # Create unique identifier for this analysis
        text_hash = hashlib.md5(resume_text.encode()).hexdigest()[:8]
        timestamp = int(time.time())
        
        # Enhanced prompt with context for uniqueness
        prompt = f"""
[ANÁLISE #{timestamp}-{text_hash}]

Você é um especialista em recrutamento analisando um currículo específico para uma vaga. 
Cada análise deve ser única e personalizada baseada no conteúdo específico do currículo.

CONTEXTO DA VAGA:
Título: {job.title}
Descrição: {job.description[:500]}...
Requisitos: {job.requirements[:500]}...

CURRÍCULO ESPECÍFICO PARA ANÁLISE:
{resume_text}

INSTRUÇÕES IMPORTANTES:
1. Analise ESPECIFICAMENTE este currículo individual
2. Identifique detalhes únicos do candidato (nome, experiências específicas, projetos)
3. Avalie compatibilidade real com os requisitos da vaga
4. Forneça insights personalizados baseados no conteúdo específico
5. Use escala de 0-10 com incrementos de 0.5

RESPONDA EM JSON VÁLIDO:
{{
    "score": float,
    "summary": "resumo personalizado mencionando nome e experiências específicas",
    "analysis": "análise detalhada das qualificações específicas do candidato",
    "skills": ["lista de habilidades identificadas no currículo"],
    "experience_years": int,
    "education_level": "nível educacional específico",
    "match_reasons": ["motivos específicos baseados no currículo"],
    "recommendations": ["recomendações personalizadas para este candidato"]
}}
        """
        
        logging.info("Sending request to DeepSeek API...")
        
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
            max_tokens=1500,
            temperature=0.3
        )
        
        logging.info("Response received from DeepSeek API")
        
        result = json.loads(response.choices[0].message.content)
        logging.info(f"API response parsed successfully: {result}")
        
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
        
        logging.info(f"Analysis completed successfully with score: {analysis_result['score']}")
        
        # Cache the result for future use
        analysis_cache.cache_analysis(resume_text, job.id, analysis_result)
        
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
