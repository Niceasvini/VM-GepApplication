# Estrutura do Projeto - Viana e Moura

## Organização dos Arquivos

### Arquivos Principais (Raiz)
- `main.py` - Entrada da aplicação
- `app.py` - Configuração do Flask e banco de dados
- `models.py` - Modelos de dados (User, Job, Candidate, etc.)
- `routes.py` - Rotas da aplicação web
- `replit.md` - Documentação do projeto e preferências

### Pasta `services/`
**Serviços principais da aplicação**
- `ai_service.py` - Serviço de análise de currículos com IA (DeepSeek)
- `file_processor.py` - Processamento de arquivos (PDF, DOCX, TXT)
- `cache_service.py` - Cache para análises de IA

### Pasta `processors/`
**Processadores de análise em lote**
- `background_processor.py` - Processador principal usado pelo sistema
- `async_processor.py` - Processador assíncrono
- `parallel_processor.py` - Processador paralelo básico
- `parallel_processor_improved.py` - Processador paralelo melhorado
- `simple_processor.py` - Processador simples
- `fast_processor.py` - Processador rápido
- `streaming_upload.py` - Processador de upload em lote

### Pasta `utils/`
**Utilitários e scripts de manutenção**
- `find_outdated_analysis.py` - Encontra candidatos com análise desatualizada
- `fix_processing.py` - Corrige processamento de candidatos
- `monitor_processing.py` - Monitora processamento em tempo real
- `process_all_candidates.py` - Processa todos os candidatos pendentes
- `reprocess_generic_analysis.py` - Reprocessa análises genéricas

### Pasta `tests/`
**Testes e depuração**
- `test_*.py` - Arquivos de teste
- `debug_*.py` - Scripts de depuração
- `create_test_*.py` - Criação de dados de teste

### Pastas do Sistema
- `templates/` - Templates HTML (Jinja2)
- `static/` - Arquivos estáticos (CSS, JS, imagens)
- `uploads/` - Arquivos de currículos enviados
- `cache/` - Cache de análises de IA
- `instance/` - Instância do Flask

## Fluxo de Processamento

1. **Upload de Currículos** (`routes.py` → `services/file_processor.py`)
2. **Análise de IA** (`processors/background_processor.py` → `services/ai_service.py`)
3. **Armazenamento** (`models.py` → Banco de dados)
4. **Visualização** (`templates/` → Interface web)

## Importações Principais

```python
# Serviços
from services.ai_service import analyze_resume
from services.file_processor import process_uploaded_file

# Processadores
from processors.background_processor import start_background_analysis

# Utilitários
from utils.find_outdated_analysis import find_outdated_candidates
```

## Configuração do Ambiente

- **Banco de dados**: PostgreSQL (Supabase)
- **IA**: DeepSeek API (compatível com OpenAI)
- **Arquivos**: Suporte a PDF, DOCX, TXT
- **Cache**: Sistema de cache para análises