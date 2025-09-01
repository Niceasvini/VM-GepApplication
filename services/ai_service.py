import json
import os
import logging
import time
import hashlib
from services.file_processor import extract_text_from_file
from services.cache_service import analysis_cache

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
    Generate only the score for faster processing as a professional recruiter
    """
    prompt = f"""
Você é um recrutador sênior especializado em avaliação de candidatos.

Avalie o currículo abaixo para a vaga '{job.title}' e atribua uma nota de 0 a 10.

VAGA: {job.title}
DESCRIÇÃO: {job.description[:300] if job.description else 'Não especificado'}
REQUISITOS: {job.requirements[:500] if job.requirements else 'Não especificado'}

CRITÉRIOS DE AVALIAÇÃO:
1. Experiência relevante na área (peso 4)
2. Habilidades técnicas que atendem aos requisitos (peso 3)
3. Formação acadêmica adequada (peso 2)
4. Qualidade e clareza do currículo (peso 1)

CURRÍCULO:
{cv_text[:3000]}

INSTRUÇÕES:
- Analise objetivamente a adequação do candidato à vaga específica
- Considere a relevância das experiências em relação aos requisitos
- Avalie se as habilidades técnicas atendem às necessidades da posição
- Atribua uma nota de 0 a 10 com até duas casas decimais
- Retorne apenas a nota final (ex: 7.91 ou 6.25), sem comentários

Nota: [sua avaliação]
"""
    
    try:
        response = openai.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,  # Increased slightly for better responses
            temperature=0.1,  # Lower temperature for faster, more consistent responses
            timeout=45  # 45 second timeout
        )
    except Exception as api_error:
        logging.error(f"Score API call failed: {api_error}")
        # Return a default score instead of failing
        return 5.0
    
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
    Generate detailed summary and analysis in structured format as a professional recruiter
    """
    prompt = f"""
Você é um recrutador sênior especializado em análise de currículos. 

ANALISE APENAS O CURRÍCULO REAL FORNECIDO ABAIXO. NÃO INVENTE INFORMAÇÕES.

VAGA: {job.title}
DESCRIÇÃO: {job.description[:500] if job.description else 'Não especificado'}
REQUISITOS: {job.requirements[:1000] if job.requirements else 'Não especificado'}

CURRÍCULO REAL DO CANDIDATO:
{cv_text[:4000]}

INSTRUÇÕES OBRIGATÓRIAS:
1. Analise APENAS as informações reais do currículo fornecido
2. NÃO invente dados, empresas ou experiências
3. Se alguma informação não estiver no currículo, escreva "Não informado"
4. Seja específico sobre o candidato real
5. NÃO use exemplos hipotéticos como "João Silva" ou "Empresa XYZ"
6. Analise o currículo REAL fornecido acima

FORNECE UMA ANÁLISE PROFISSIONAL NO SEGUINTE FORMATO EXATO:

RESUMO DO CURRÍCULO

Nome Completo: [nome real do candidato do currículo]

Experiência Relevante:
• [Cargo real] na [Empresa real] ([período real])
• [Cargo real] na [Empresa real] ([período real])
• [Cargo real] na [Empresa real] ([período real])

Habilidades Técnicas: [Habilidades reais identificadas no currículo]

Formação Acadêmica: [Formação real do candidato]

Idiomas: [Idiomas reais do candidato, se informados]

Informações de Contato: [Email e telefone reais do candidato]

ANÁLISE DO RECRUTADOR

1. ALINHAMENTO TÉCNICO:
• Experiência relevante: [cargo específico real] na [empresa real] ([período real])
• Competências alinhadas: [liste 2-3 competências reais que atendem aos requisitos da vaga]
• Adequação à vaga: [explique objetivamente como o perfil real se adequa à posição]

2. GAPS IDENTIFICADOS:
• Lacunas técnicas: [liste 2-3 lacunas específicas em relação aos requisitos da vaga]
• Conhecimentos em falta: [conhecimentos específicos que faltam baseado no currículo real]
• Áreas de desenvolvimento: [sugira 2-3 desenvolvimentos específicos baseado no perfil real]

3. RECOMENDAÇÃO FINAL: [ADEQUADO/PARCIAL/INADEQUADO]
• Pontos fortes: [liste 2-3 pontos fortes específicos do candidato real]
• Limitações: [liste 2-3 limitações específicas baseadas no currículo real]
• Justificativa: [explique objetivamente por que é ADEQUADO/PARCIAL/INADEQUADO para a vaga]

IMPORTANTE: 
- O RESUMO DO CURRÍCULO deve conter APENAS informações factuais do currículo
- A ANÁLISE DO RECRUTADOR deve conter APENAS a avaliação profissional
- NÃO inclua análise no resumo
- NÃO inclua resumo na análise
- Use exatamente os títulos "RESUMO DO CURRÍCULO" e "ANÁLISE DO RECRUTADOR"

IMPORTANTE:
- Analise APENAS as informações reais do currículo fornecido
- NÃO invente dados, empresas ou experiências
- Se alguma informação não estiver no currículo, escreva "Não informado"
- Seja específico sobre o candidato real
- NÃO use exemplos hipotéticos
- Avalie objetivamente a adequação à vaga específica
- Use linguagem clara e direta
- Evite frases genéricas, seja específico sobre o candidato real
- Se o currículo não contiver informações suficientes, indique claramente
"""
    
    try:
        response = openai.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,  # Increased for complete analysis
            temperature=0.2,  # Lower temperature for more consistent responses
            timeout=90  # 90 second timeout for better reliability
        )
    except Exception as api_error:
        logging.error(f"Analysis API call failed: {api_error}")
        # Return a basic analysis instead of failing completely
        return f"""
RESUMO DO CURRÍCULO

Nome Completo: [Nome não identificado no currículo]

Experiência Relevante:
• [Experiência não detalhada no currículo]

Habilidades Técnicas: [Habilidades não especificadas]

Formação Acadêmica: [Formação não informada]

Idiomas: [Idiomas não informados]

Informações de Contato: [Contato não disponível]

ANÁLISE DO RECRUTADOR

1. ALINHAMENTO TÉCNICO:
• Experiência relevante: [Não foi possível analisar devido a erro técnico]
• Competências alinhadas: [Análise não disponível]
• Adequação à vaga: [Avaliação não possível]

2. GAPS IDENTIFICADOS:
• Lacunas técnicas: [Não foi possível identificar]
• Conhecimentos em falta: [Análise não disponível]
• Áreas de desenvolvimento: [Não especificado]

3. RECOMENDAÇÃO FINAL: PARCIAL
• Pontos fortes: [Não foi possível identificar]
• Limitações: [Análise técnica não disponível]
• Justificativa: Erro técnico na análise. Recomenda-se reprocessar o currículo.
"""
    
    result = response.choices[0].message.content
    
    # Validate that we got a meaningful response
    if not result or len(result.strip()) < 100:
        logging.warning(f"API returned very short response: {len(result)} characters")
        return f"""
RESUMO DO CURRÍCULO

Nome Completo: [Nome não identificado]

Experiência Relevante:
• [Experiência não detalhada]

Habilidades Técnicas: [Habilidades não especificadas]

Formação Acadêmica: [Formação não informada]

Idiomas: [Idiomas não informados]

Informações de Contato: [Contato não disponível]

ANÁLISE DO RECRUTADOR

1. ALINHAMENTO TÉCNICO:
• Experiência relevante: [Análise não disponível]
• Competências alinhadas: [Não foi possível identificar]
• Adequação à vaga: [Avaliação não possível]

2. GAPS IDENTIFICADOS:
• Lacunas técnicas: [Não foi possível identificar]
• Conhecimentos em falta: [Análise não disponível]
• Áreas de desenvolvimento: [Não especificado]

3. RECOMENDAÇÃO FINAL: PARCIAL
• Pontos fortes: [Não foi possível identificar]
• Limitações: [Análise técnica não disponível]
• Justificativa: Resposta da API muito curta. Recomenda-se reprocessar o currículo.
"""
    
    return result

def analyze_resume(file_path, file_type, job):
    """
    Fast optimized resume analysis with parallel processing
    Returns a dictionary with score, summary, analysis, and skills
    """
    try:
        # Extract text from the resume
        resume_text = extract_text_from_file(file_path, file_type)
        
        # Log the extracted text for debugging
        logging.info(f"Extracted text length: {len(resume_text)}")
        logging.info(f"First 500 characters: {resume_text[:500]}")
        
        if not resume_text or len(resume_text.strip()) < 50:
            logging.error(f"Resume text is too short or empty: {len(resume_text)} characters")
            return {
                'score': 0.0,
                'summary': 'Erro: Não foi possível extrair texto do currículo',
                'analysis': 'FALHA NA ANÁLISE: O arquivo não contém texto legível ou está corrompido.',
                'skills': [],
                'experience_years': 0,
                'education_level': 'Não informado',
                'match_reasons': [],
                'recommendations': []
            }
        
        # Check cache first to avoid redundant API calls
        cached_result = analysis_cache.get_cached_analysis(resume_text, job.id)
        if cached_result:
            return cached_result
        
        # Check if API key is available
        if not DEEPSEEK_API_KEY:
            logging.error("DeepSeek API key not found")
            raise Exception("API key not configured")
        
        # Limit resume text to avoid token limits (increased for better analysis)
        if len(resume_text) > 4000:
            resume_text = resume_text[:4000] + "..."
        
        # Verify that we have meaningful text
        if not resume_text or len(resume_text.strip()) < 100:
            logging.error(f"Resume text is too short for analysis: {len(resume_text)} characters")
            return {
                'score': 0.0,
                'summary': 'Erro: Currículo não contém texto suficiente para análise',
                'analysis': 'FALHA NA ANÁLISE: O arquivo não contém texto suficiente para análise. Verifique se o arquivo está legível.',
                'skills': [],
                'experience_years': 0,
                'education_level': 'Não informado',
                'match_reasons': [],
                'recommendations': []
            }
        
        # Step 1: Generate score quickly (most important)
        try:
            score = generate_score_only(resume_text, job)
        except Exception as score_error:
            logging.error(f"Error generating score: {score_error}")
            score = 5.0  # Default score
        
        # Step 2: Generate summary and analysis (optimized)
        try:
            full_analysis = generate_summary_and_analysis(resume_text, job)
        except Exception as analysis_error:
            logging.error(f"Error generating analysis: {analysis_error}")
            full_analysis = "Análise não disponível devido a erro técnico."
        
        # Step 3: Process analysis and separate summary from detailed analysis
        executive_summary = ""
        detailed_analysis = ""
        
        if full_analysis:
            # Try to separate summary from detailed analysis
            if "RESUMO DO CURRÍCULO" in full_analysis and "ANÁLISE DO RECRUTADOR" in full_analysis:
                parts = full_analysis.split("ANÁLISE DO RECRUTADOR")
                if len(parts) >= 2:
                    # Extract summary (remove the "RESUMO DO CURRÍCULO" header)
                    summary_part = parts[0].replace("RESUMO DO CURRÍCULO", "").strip()
                    if summary_part:
                        executive_summary = summary_part
                    # Keep only the detailed analysis
                    detailed_analysis = parts[1].strip()
                else:
                    executive_summary = full_analysis
                    detailed_analysis = ""
            elif "RESUMO EXECUTIVO" in full_analysis and "ANÁLISE DO RECRUTADOR" in full_analysis:
                # Handle old format
                parts = full_analysis.split("ANÁLISE DO RECRUTADOR")
                if len(parts) >= 2:
                    summary_part = parts[0].replace("RESUMO EXECUTIVO", "").strip()
                    if summary_part:
                        executive_summary = summary_part
                    detailed_analysis = parts[1].strip()
                else:
                    executive_summary = full_analysis
                    detailed_analysis = ""
            else:
                # If format is not as expected, use the full analysis as summary only
                executive_summary = full_analysis
                detailed_analysis = ""
        
        # Clean up any remaining separators and analysis content from summary
        if executive_summary:
            executive_summary = executive_summary.replace("---", "").strip()
            # Remove any analysis content that might have leaked into summary
            analysis_indicators = [
                "ANÁLISE DO RECRUTADOR", "1. ALINHAMENTO TÉCNICO", "2. GAPS IDENTIFICADOS", 
                "3. RECOMENDAÇÃO FINAL", "OBSERVAÇÃO FINAL", "Pontos fortes:", "Limitações:", 
                "Justificativa:", "Lacunas técnicas:", "Conhecimentos em falta:", 
                "Áreas de desenvolvimento:", "Competências alinhadas:", "Adequação à vaga:", 
                "Experiência relevante:", "PARCIAL", "ADEQUADO", "INADEQUADO"
            ]
            for indicator in analysis_indicators:
                if indicator in executive_summary:
                    executive_summary = executive_summary.split(indicator)[0].strip()
        
        if detailed_analysis:
            detailed_analysis = detailed_analysis.replace("---", "").strip()
        
        # Extract skills quickly
        skills = extract_skills_from_text(resume_text)
        
        # Validate analysis completeness with more tolerance
        has_score = score is not None and score > 0
        has_summary = executive_summary and len(executive_summary.strip()) > 30
        has_analysis = detailed_analysis and len(detailed_analysis.strip()) > 50
        
        # More flexible validation - if we have at least score and some content, consider it valid
        is_analysis_complete = has_score and (has_summary or has_analysis)
        
        if not is_analysis_complete:
            logging.warning(f"Incomplete analysis detected for candidate. Score: {score}, Summary length: {len(executive_summary)}, Analysis length: {len(detailed_analysis)}")
            
            # Try to provide partial results if possible
            if has_score:
                return {
                    'score': score,
                    'summary': executive_summary if has_summary else 'Análise parcial - Resumo não disponível',
                    'analysis': detailed_analysis if has_analysis else 'Análise parcial - Detalhes não disponíveis. Recomenda-se reprocessar para análise completa.',
                    'skills': skills,
                    'experience_years': 1,
                    'education_level': 'Não informado',
                    'match_reasons': [f"Score: {score}/10"],
                    'recommendations': ['Recomenda-se reprocessar para análise completa']
                }
            else:
                return {
                    'score': 0.0,
                    'summary': 'Análise incompleta - Falha na geração do resumo',
                    'analysis': 'FALHA NA ANÁLISE: A análise foi marcada como concluída mas não gerou conteúdo completo. Possíveis causas: erro na API, timeout, ou texto insuficiente.',
                    'skills': [],
                    'experience_years': 0,
                    'education_level': 'Não informado',
                    'match_reasons': [],
                    'recommendations': ['Recomenda-se reprocessar o currículo']
                }
        
        # Create result
        analysis_result = {
            'score': score,
            'summary': executive_summary,
            'analysis': detailed_analysis,
            'skills': skills,
            'experience_years': 1,  # Default for speed
            'education_level': 'Não informado',
            'match_reasons': [f"Score: {score}/10"],
            'recommendations': ["Avaliação baseada em experiência e habilidades técnicas"]
        }
        
        # Cache the result for future use
        analysis_cache.cache_analysis(resume_text, job.id, analysis_result)
        
        return analysis_result
        
    except Exception as e:
        # Quick error handling
        error_description = str(e)
        logging.error(f"Error in fast analysis: {error_description}")
        
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
