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

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    DEEPSEEK_API_KEY = os.environ.get("OPENAI_API_KEY")

# Configure OpenAI client for DeepSeek API
openai = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1",
    timeout=60.0  # 60 seconds timeout
)

def generate_score_only(cv_text, job):
    """
    Generate only the score for faster processing
    """
    prompt = f"""
Você é um avaliador técnico especializado em recrutamento.

Dê uma nota de 0 a 10 para o currículo abaixo com base na vaga '{job.title}', considerando:

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
{cv_text[:3000]}
"""
    
    response = openai.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=50,
        temperature=0.3
    )
    
    result = response.choices[0].message.content
    # Extract score using regex - more precise
    import re
    match = re.search(r"(\d{1,2}(?:\.\d{1,2})?)", result)
    if match:
        raw_score = float(match.group(1))
        # Ensure score is between 0 and 10 with proper scaling
        if raw_score > 10:
            raw_score = raw_score / 10  # Handle cases like 85/100
        return round(min(max(raw_score, 0), 10), 2)
    
    # If no score found, try to extract from different patterns
    if "excelente" in result.lower() or "muito bom" in result.lower():
        return 8.5
    elif "bom" in result.lower() or "adequado" in result.lower():
        return 7.0
    elif "regular" in result.lower() or "médio" in result.lower():
        return 5.5
    elif "fraco" in result.lower() or "inadequado" in result.lower():
        return 3.0
    
    return 5.0

def generate_summary_and_analysis(cv_text, job):
    """
    Generate detailed summary and analysis in structured format
    """
    prompt = f"""
Você é um analista de currículos especializado. Analise o currículo abaixo para a vaga '{job.title}' e formate a resposta EXATAMENTE como o exemplo:

📄 Currículo de [Nome do Candidato]

📋 Conteúdo do Currículo
Nome: [Nome completo]
Idade: [Idade se disponível]
Localização: [Cidade/Estado]
Contato: [Telefone] | [E-mail]

Objetivo:
[Objetivo profissional do candidato]

Experiência Profissional:
[Listar experiências com empresas, cargos e períodos]

Educação:
[Formação acadêmica e cursos]

🔍 Análise da IA

Alinhamento Técnico:
• [Pontos positivos relevantes para a vaga]
• [Experiências que agregam valor]
• [Habilidades alinhadas com os requisitos]

Gaps Técnicos:
• [Competências que faltam para a vaga]
• [Experiências não relacionadas ou insuficientes]
• [Conhecimentos técnicos em falta]

Recomendação Final: [Forte/Parcial/Fraco]
[Justificativa da recomendação com base na análise]

Currículo para análise:
{cv_text[:2000]}

Requisitos da vaga:
{job.requirements[:1000] if job.requirements else 'Não especificado'}

IMPORTANTE: Mantenha exatamente essa formatação com emojis e estrutura organizacional.

Use o seguinte formato:

### RESUMO
(Resumo estruturado)

### ANÁLISE
1. Alinhamento Técnico: ...
2. Gaps Técnicos: ...
3. Recomendação Final: Sim / Parcial / Não

Currículo:
{cv_text[:3000]}
"""
    
    response = openai.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.5
    )
    
    result = response.choices[0].message.content
    parts = result.split('### ANÁLISE')
    
    summary = parts[0].replace('### RESUMO', '').strip()
    analysis = parts[1].strip() if len(parts) > 1 else 'Análise não disponível'
    
    return summary, analysis

def analyze_resume(file_path, file_type, job):
    """
    Optimized resume analysis with faster processing
    Returns a dictionary with score, summary, analysis, and skills
    """
    try:
        logging.info(f"Starting optimized analysis for file: {file_path}")
        
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
        if len(resume_text) > 5000:
            resume_text = resume_text[:5000] + "..."
            logging.info("Resume text truncated to fit token limits")
        
        # Step 1: Generate score quickly (most important)
        logging.info("Generating score...")
        score = generate_score_only(resume_text, job)
        logging.info(f"Score generated: {score}")
        
        # Step 2: Generate summary and analysis
        logging.info("Generating summary and analysis...")
        summary, analysis = generate_summary_and_analysis(resume_text, job)
        logging.info("Summary and analysis generated")
        
        # Extract skills from resume text (simple keyword extraction)
        skills = extract_skills_from_text(resume_text)
        
        # Estimate experience years from text
        experience_years = estimate_experience_years(resume_text)
        
        # Determine education level
        education_level = determine_education_level(resume_text)
        
        # Create result
        analysis_result = {
            'score': score,
            'summary': summary,
            'analysis': analysis,
            'skills': skills,
            'experience_years': experience_years,
            'education_level': education_level,
            'match_reasons': [f"Score: {score}/10"],
            'recommendations': ["Avaliação baseada em experiência e habilidades técnicas"]
        }
        
        logging.info(f"Optimized analysis completed successfully with score: {analysis_result['score']}")
        
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

def extract_skills_from_text(text):
    """
    Extract skills from resume text using keyword matching
    """
    skills_keywords = [
        'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'docker', 'kubernetes',
        'aws', 'azure', 'gcp', 'flask', 'django', 'spring', 'laravel',
        'git', 'github', 'gitlab', 'jenkins', 'ci/cd', 'agile', 'scrum',
        'html', 'css', 'bootstrap', 'tailwind', 'rest', 'api', 'graphql',
        'machine learning', 'data science', 'pandas', 'numpy', 'tensorflow',
        'pytorch', 'power bi', 'tableau', 'excel', 'word', 'powerpoint'
    ]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in skills_keywords:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    return found_skills[:10]  # Return top 10 skills

def estimate_experience_years(text):
    """
    Estimate years of experience from resume text
    """
    import re
    
    # Look for patterns like "5 anos", "3 years", "2+ anos"
    patterns = [
        r'(\d+)\s*(?:anos?|years?)',
        r'(\d+)\+\s*(?:anos?|years?)',
        r'(?:há|for)\s*(\d+)\s*(?:anos?|years?)'
    ]
    
    years = []
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        for match in matches:
            years.append(int(match))
    
    return max(years) if years else 1

def determine_education_level(text):
    """
    Determine education level from resume text
    """
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['doutorado', 'phd', 'doutor']):
        return 'Doutorado'
    elif any(word in text_lower for word in ['mestrado', 'master', 'mestre']):
        return 'Mestrado'
    elif any(word in text_lower for word in ['bacharelado', 'bacharel', 'graduação', 'superior']):
        return 'Superior'
    elif any(word in text_lower for word in ['técnico', 'tecnólogo']):
        return 'Técnico'
    else:
        return 'Não informado'

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
