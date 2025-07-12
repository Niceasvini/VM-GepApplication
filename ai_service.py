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
    base_url="https://api.deepseek.com/v1"
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
Você é um analista de currículos especializado. Analise o currículo abaixo para a vaga '{job.title}' e formate a resposta EXATAMENTE como solicitado:

FORMATO OBRIGATÓRIO:

Resumo Executivo

Nome Completo: [nome do candidato]

Experiência Relevante: [Cargo] na [Empresa] ([Ano-Início] - [Ano-Fim]), [Cargo] na [Empresa] ([Ano-Início] - [Ano-Fim]), [continuar com todas as experiências mais relevantes]

Habilidades Técnicas: [Liste as principais habilidades técnicas identificadas no currículo]

Formação Acadêmica: [Grau] em [Curso] na [Instituição], [Cursos complementares relevantes]

Idiomas: [Idioma] ([Nível]), [Idioma] ([Nível])

Informações de Contato: Email: [email], Telefone: [telefone], Localização: [cidade/estado]

Análise da IA

1. Alinhamento Técnico:
O candidato possui experiência em [cite experiências específicas do currículo] na empresa [nome da empresa] durante [período]. Suas responsabilidades incluíram [liste atividades específicas]. Em relação aos requisitos da vaga de {job.title}, o candidato demonstra competência em [liste competências específicas que se alinham]. Por exemplo, sua experiência com [tecnologia/processo específico] na [empresa] por [período] indica capacidade para [função específica da vaga]. Adicionalmente, sua formação em [curso/área] complementa os requisitos de [requisito específico da vaga].

2. Gaps Técnicos:
Analisando os requisitos da vaga, o candidato apresenta lacunas em [liste especificamente quais requisitos faltam]. Não possui experiência comprovada em [tecnologia/metodologia específica] que é essencial para [função específica]. Sua formação carece de [conhecimento específico] necessário para [atividade da vaga]. Recomenda-se desenvolvimento em [área específica] através de [curso/certificação específica]. Também seria benéfico adquirir experiência prática em [tecnologia/processo específico] para atender plenamente aos requisitos de [requisito específico da vaga].

3. Recomendação Final: [Adequado/Parcial/Inadequado]
Baseado na análise técnica, o candidato demonstra [pontos fortes específicos] através de sua experiência em [empresa/cargo] e formação em [área]. Contudo, apresenta limitações em [áreas específicas] que impactam sua adequação para [função específica da vaga]. Considerando que [justificativa técnica baseada em experiência e requisitos], a recomendação é [Adequado/Parcial/Inadequado] pois [explicação detalhada do raciocínio].

VAGA: {job.title}
REQUISITOS: {job.requirements[:1000] if job.requirements else 'Não especificado'}

CURRÍCULO:
{cv_text[:3000]}

IMPORTANTE: 
- Use exatamente o formato mostrado acima
- No Resumo Executivo, organize as informações em seções estruturadas SEM usar traços, hashes ou marcações
- Na Análise da IA, seja específico citando empresas, cargos, tecnologias e experiências reais
- Para candidatos com score baixo, use "Inadequado" na recomendação
- Não use **, asteriscos, ---, ###, #### ou qualquer marcação de formatação no texto
- Seja direto e específico, evite frases genéricas como "baseado no perfil apresentado"
"""
    
    response = openai.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,  # Increased for longer detailed summaries
        temperature=0.5
    )
    
    result = response.choices[0].message.content
    return result

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
        full_analysis = generate_summary_and_analysis(resume_text, job)
        logging.info("Summary and analysis generated")
        
        # Step 3: Split the analysis into executive summary and detailed analysis
        executive_summary = ""
        detailed_analysis = ""
        
        if full_analysis:
            if "## Resumo Executivo" in full_analysis and "## Análise Detalhada" in full_analysis:
                parts = full_analysis.split("## Análise Detalhada")
                if len(parts) >= 2:
                    executive_summary = parts[0].replace("## Resumo Executivo", "").strip()
                    detailed_analysis = "## Análise Detalhada" + parts[1]
                else:
                    executive_summary = full_analysis
                    detailed_analysis = full_analysis
            else:
                # If format is not as expected, use the full analysis as summary
                executive_summary = full_analysis
                detailed_analysis = full_analysis
        
        # Extract skills from resume text (simple keyword extraction)
        skills = extract_skills_from_text(resume_text)
        
        # Estimate experience years from text
        experience_years = estimate_experience_years(resume_text)
        
        # Determine education level
        education_level = determine_education_level(resume_text)
        
        # Create result
        analysis_result = {
            'score': score,
            'summary': executive_summary,  # Only the executive summary
            'analysis': detailed_analysis,  # Only the detailed analysis
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
        # Detailed error description based on error type
        error_description = get_detailed_error_description(e, file_path)
        logging.error(f"Error analyzing resume: {error_description}")
        
        return {
            'score': 0.0,
            'summary': 'Erro na análise do currículo',
            'analysis': f'FALHA NA ANÁLISE: {error_description}',
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

def get_detailed_error_description(error, file_path):
    """
    Generate detailed error description based on error type
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # File-related errors
    if "No such file or directory" in error_msg:
        return f"Arquivo não encontrado: {file_path} - O arquivo foi removido ou movido durante o processamento."
    
    # Permission errors
    if "Permission denied" in error_msg:
        return f"Erro de permissão: Não foi possível acessar o arquivo {file_path}. Verifique as permissões do arquivo."
    
    # OpenAI/API errors
    if "OpenAI" in error_type or "API" in error_type:
        if "timeout" in error_msg.lower():
            return f"Timeout na API: A análise demorou muito para responder. Isso pode ocorrer quando o serviço de IA está sobrecarregado."
        elif "rate limit" in error_msg.lower():
            return f"Limite de taxa excedido: Muitas requisições à API. Aguarde alguns minutos antes de tentar novamente."
        elif "invalid" in error_msg.lower():
            return f"Erro de API: Chave de API inválida ou problema na configuração do serviço de IA."
        elif "connection" in error_msg.lower():
            return f"Erro de conexão: Não foi possível conectar ao serviço de IA. Verifique a conexão com a internet."
        else:
            return f"Erro na API de IA: {error_msg}"
    
    # Database errors
    if "database" in error_msg.lower() or "sql" in error_msg.lower():
        return f"Erro de banco de dados: {error_msg} - Problema ao salvar ou recuperar dados do candidato."
    
    # Text extraction errors
    if "extract" in error_msg.lower() or "decode" in error_msg.lower():
        return f"Erro na extração de texto: Não foi possível extrair o conteúdo do arquivo {file_path}. O arquivo pode estar corrompido ou em formato não suportado."
    
    # Memory/processing errors
    if "memory" in error_msg.lower() or "out of" in error_msg.lower():
        return f"Erro de memória: O arquivo {file_path} é muito grande ou complexo para processamento."
    
    # Network errors
    if "network" in error_msg.lower() or "dns" in error_msg.lower():
        return f"Erro de rede: Problema de conectividade. Verifique a conexão com a internet."
    
    # Generic errors
    return f"Erro inesperado ({error_type}): {error_msg}"

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
