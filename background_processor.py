#!/usr/bin/env python3
"""
Background processor for AI analysis with improved performance
"""
import os
import time
import threading
from datetime import datetime
from openai import OpenAI

# Set environment
os.environ['DATABASE_URL'] = 'postgresql://postgres.bndkpowgvagtlxwmthma:5585858Vini%40@aws-0-sa-east-1.pooler.supabase.com:6543/postgres'

from app import app, db
from models import Candidate
from file_processor import extract_text_from_file

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
    if "OpenAI" in error_type or "API" in error_type or "timeout" in error_msg.lower():
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

# Configure OpenAI client
client = OpenAI(
    api_key="sk-08e53165834948c8b96fe8ec44a12baf",
    base_url="https://api.deepseek.com/v1",

)

# Global variables for tracking processing
processing_threads = {}
processing_status = {}

def process_candidate_background(candidate_id):
    """
    Process a single candidate in the background
    """
    try:
        with app.app_context():
            candidate = db.session.get(Candidate, candidate_id)
            if not candidate:
                return False
            
            # Update status
            candidate.analysis_status = 'processing'
            db.session.commit()
            processing_status[candidate_id] = 'processing'
            
            # Extract resume text
            resume_text = extract_text_from_file(candidate.file_path, candidate.file_type)
            
            # Generate score (wait for DeepSeek even if slow)
            score_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user",
                    "content": f"Avalie este currículo para '{candidate.job.title}' de 0-10. Responda apenas o número (ex: 7.5):\\n\\n{resume_text[:800]}"
                }],
                max_tokens=10,
                temperature=0.1
            )
            
            score_text = score_response.choices[0].message.content.strip()
            
            # Parse score
            import re
            score_match = re.search(r'(\\d+\\.?\\d*)', score_text)
            if score_match:
                score = float(score_match.group(1))
                if score > 10:
                    score = score / 10
            else:
                score = 5.0
            
            # Generate summary (wait for DeepSeek even if slow)
            summary_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user",
                    "content": f"Faça um resumo técnico detalhado de {candidate.name} para {candidate.job.title}. Inclua experiência, habilidades e formação relevante:\\n\\n{resume_text[:3000]}"
                }],
                max_tokens=900,
                temperature=0.3
            )
            
            summary = summary_response.choices[0].message.content.strip()
            
            # Update candidate
            candidate.ai_score = score
            candidate.ai_summary = summary
            candidate.ai_analysis = f"Análise: Score {score}/10. {summary}"
            candidate.analysis_status = 'completed'
            candidate.analyzed_at = datetime.utcnow()
            
            db.session.commit()
            processing_status[candidate_id] = 'completed'
            
            print(f"✓ Processed: {candidate.name} - Score: {score}")
            return True
            
    except Exception as e:
        # Generate detailed error description
        error_description = get_detailed_error_description(e, candidate.file_path if 'candidate' in locals() else 'arquivo desconhecido')
        print(f"✗ FALHA no processamento do candidato {candidate_id}: {error_description}")
        
        # Mark as failed with detailed error
        try:
            with app.app_context():
                candidate = db.session.get(Candidate, candidate_id)
                if candidate:
                    candidate.analysis_status = 'failed'
                    candidate.ai_summary = f'FALHA: {error_description}'
                    candidate.ai_analysis = f'ANÁLISE FALHOU: {error_description}'
                    candidate.ai_score = 0.0
                    db.session.commit()
                    processing_status[candidate_id] = 'failed'
        except Exception as db_error:
            print(f"✗ Erro adicional ao salvar falha: {db_error}")
        
        return False

def start_background_analysis(candidate_ids):
    """
    Start background analysis for multiple candidates
    """
    def worker():
        print(f"🚀 INICIANDO PROCESSAMENTO EM LOTE: {len(candidate_ids)} candidatos")
        for i, candidate_id in enumerate(candidate_ids, 1):
            print(f"📋 [{i}/{len(candidate_ids)}] Processando candidato {candidate_id}")
            try:
                success = process_candidate_background(candidate_id)
                if success:
                    print(f"✅ Candidato {candidate_id} processado com sucesso")
                else:
                    print(f"❌ Erro ao processar candidato {candidate_id}")
            except Exception as e:
                print(f"💥 Erro inesperado com candidato {candidate_id}: {e}")
            
            time.sleep(1)  # Small delay between candidates
        
        print(f"🎉 PROCESSAMENTO EM LOTE CONCLUÍDO: {len(candidate_ids)} candidatos")
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    processing_threads[str(candidate_ids)] = thread
    print(f"🔄 Thread de processamento iniciada para {len(candidate_ids)} candidatos")
    return thread

def get_processing_status(candidate_ids):
    """
    Get processing status for candidates
    """
    try:
        with app.app_context():
            status_counts = {
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0
            }
            
            for candidate_id in candidate_ids:
                candidate = db.session.get(Candidate, candidate_id)
                if candidate:
                    status_counts[candidate.analysis_status] += 1
            
            return status_counts
    except Exception as e:
        print(f"Error getting status: {e}")
        return {'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0}

def cleanup_stale_threads():
    """
    Clean up finished threads
    """
    global processing_threads
    finished_threads = []
    
    for key, thread in processing_threads.items():
        if not thread.is_alive():
            finished_threads.append(key)
    
    for key in finished_threads:
        del processing_threads[key]

def get_active_threads():
    """
    Get count of active processing threads
    """
    cleanup_stale_threads()
    return len(processing_threads)

if __name__ == "__main__":
    # Test with pending candidates
    with app.app_context():
        pending_candidates = Candidate.query.filter_by(analysis_status='pending').all()
        if pending_candidates:
            candidate_ids = [c.id for c in pending_candidates]
            print(f"Starting background processing for {len(candidate_ids)} candidates")
            
            thread = start_background_analysis(candidate_ids)
            
            # Monitor progress
            while thread.is_alive():
                status = get_processing_status(candidate_ids)
                print(f"Status: {status}")
                time.sleep(5)
            
            print("Background processing completed!")
        else:
            print("No pending candidates found")