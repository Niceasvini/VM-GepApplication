# 🚀 Viana e Moura - Plataforma de Recrutamento Inteligente

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-3.1.1-blue)
![AI](https://img.shields.io/badge/AI-DeepSeek%20GPT--4o-orange)
![Database](https://img.shields.io/badge/Database-PostgreSQL-blue)

Uma plataforma avançada de recrutamento que automatiza a análise de currículos usando Inteligência Artificial, oferecendo avaliações detalhadas e scores de compatibilidade para otimizar o processo de seleção.

## 🎯 Visão Geral

O **Viana e Moura** é uma solução completa de recrutamento inteligente que utiliza IA para analisar currículos automaticamente, gerando relatórios detalhados com:

- **Scores de compatibilidade** (0-10) baseados nos requisitos da vaga
- **Resumos executivos** organizados com dados pessoais e experiências
- **Análises técnicas** estruturadas em 3 pontos: alinhamento, gaps e recomendações
- **Processamento em lote** para análise de centenas de currículos
- **Interface web moderna** com dashboard e relatórios visuais

## ✨ Principais Funcionalidades

### 🤖 Análise Inteligente de Currículos
- **IA Avançada**: Utiliza DeepSeek GPT-4o para análise profunda
- **Múltiplos Formatos**: Suporte a PDF, DOCX e TXT
- **Scores Precisos**: Avaliação de 0-10 com incrementos de 0.5
- **Análise Estruturada**: Resumo executivo + análise técnica detalhada

### 📊 Gestão Completa de Vagas
- **Criação de Vagas**: Interface intuitiva para definir requisitos
- **DCF Integration**: Documento de Conteúdo Funcional completo
- **Status Tracking**: Acompanhamento de vagas ativas/fechadas
- **Análise de Candidatos**: Ranking automático por compatibilidade

### 🚀 Processamento em Lote
- **Upload Múltiplo**: Até 100+ currículos simultaneamente
- **Processamento Paralelo**: Análise otimizada com múltiplas threads
- **Monitoramento Real-time**: Status de processamento em tempo real
- **Recuperação de Falhas**: Sistema de retry para análises falhadas

### 👥 Sistema de Usuários
- **Autenticação Segura**: Login com hash de senhas
- **Controle de Acesso**: Roles de recruiter e admin
- **Comentários**: Sistema de anotações por candidato
- **Audit Trail**: Histórico completo de ações

## 🛠 Tecnologias Utilizadas

### Backend
- **Flask 3.1.1** - Framework web Python
- **SQLAlchemy 2.0** - ORM para banco de dados
- **PostgreSQL** - Banco de dados principal (Supabase)
- **Flask-Login** - Autenticação e sessões
- **Gunicorn** - Servidor WSGI para produção

### Inteligência Artificial
- **DeepSeek API** - Modelo GPT-4o para análise de currículos
- **OpenAI Python Client** - Interface para comunicação com IA
- **Sistema de Cache** - Otimização de consultas repetidas
- **Processamento Paralelo** - Análise simultânea de múltiplos currículos

### Frontend
- **Bootstrap 5.3.0** - Framework CSS responsivo
- **Font Awesome 6.0** - Ícones modernos
- **Chart.js** - Gráficos e visualizações
- **Vanilla JavaScript** - Interações dinâmicas

### Processamento de Arquivos
- **PyPDF2** - Extração de texto de PDFs
- **python-docx** - Processamento de documentos Word
- **Werkzeug** - Handling seguro de uploads

## 🏗 Arquitetura do Sistema

```
viana-moura/
├── 📁 services/           # Serviços principais
│   ├── ai_service.py      # Integração com IA
│   ├── file_processor.py  # Processamento de arquivos
│   └── cache_service.py   # Sistema de cache
├── 📁 processors/         # Processamento em lote
│   ├── background_processor.py    # Processador principal
│   ├── parallel_processor.py      # Processamento paralelo
│   └── streaming_upload.py        # Upload em lote
├── 📁 utils/             # Utilitários
│   ├── find_outdated_analysis.py  # Manutenção
│   └── monitor_processing.py      # Monitoramento
├── 📁 templates/         # Templates HTML
│   ├── auth/             # Autenticação
│   ├── jobs/             # Gerenciamento de vagas
│   └── candidates/       # Gestão de candidatos
├── 📁 static/            # Arquivos estáticos
│   ├── css/              # Estilos personalizados
│   ├── js/               # Scripts JavaScript
│   └── images/           # Imagens e ícones
├── 📁 uploads/           # Currículos enviados
├── 📁 cache/             # Cache de análises IA
├── app.py                # Configuração principal
├── models.py             # Modelos de dados
├── routes.py             # Rotas da aplicação
└── main.py               # Ponto de entrada
```

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.11+
- PostgreSQL ou Supabase
- DeepSeek API Key (compatível com OpenAI)

### 1. Clone o Repositório
```bash
git clone https://github.com/your-username/viana-moura.git
cd viana-moura
```

### 2. Instale as Dependências
```bash
pip install -r requirements.txt
# ou usando uv
uv sync
```

### 3. Configure as Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:
```env
# Banco de Dados
DATABASE_URL=postgresql://user:password@host:port/database

# IA - DeepSeek API
OPENAI_API_KEY=your_deepseek_api_key
OPENAI_BASE_URL=https://api.deepseek.com/v1

# Flask
SESSION_SECRET=your_secret_key_here
FLASK_ENV=production
```

### 4. Configure o Banco de Dados

#### Opção A: Supabase (Recomendado)
1. Acesse [Supabase Dashboard](https://supabase.com/dashboard)
2. Crie um novo projeto
3. Vá em "Settings" > "Database" > "Connection string"
4. Copie a URI de conexão e substitua a senha
5. Use a URI no `DATABASE_URL`

#### Opção B: PostgreSQL Local
```bash
# Instale PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Crie o banco
sudo -u postgres createdb viana_moura
```

### 5. Execute as Migrações
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 6. Inicie a Aplicação
```bash
# Desenvolvimento
python main.py

# Produção
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## 📋 Como Usar

### 1. Primeiro Acesso
1. Acesse `http://localhost:5000`
2. Registre-se como novo usuário
3. Faça login na plataforma

### 2. Criar uma Vaga
1. Vá em "Vagas" > "Nova Vaga"
2. Preencha título, descrição e requisitos
3. Adicione DCF (Documento de Conteúdo Funcional)
4. Salve a vaga

### 3. Upload de Currículos
1. Acesse a vaga criada
2. Clique em "Upload de Currículos"
3. Selecione múltiplos arquivos (PDF, DOCX, TXT)
4. Aguarde o processamento automático

### 4. Analisar Resultados
1. Vá em "Candidatos" para ver todos os resultados
2. Ordene por score de compatibilidade
3. Clique em candidatos para ver análise detalhada
4. Adicione comentários e atualize status

### 5. Gerenciar Candidatos
- **Ver Detalhes**: Análise completa com resumo e gaps
- **Baixar Currículo**: Download do arquivo original
- **Comentários**: Adicione observações sobre candidatos
- **Status**: Marque como interessado/rejeitado
- **Reprocessar**: Análise novamente se necessário

## 🔧 Funcionalidades Avançadas

### Sistema de Cache
- **Cache Inteligente**: Evita reprocessamento desnecessário
- **Invalidação Automática**: Atualiza quando requisitos mudam
- **Otimização de Custos**: Reduz chamadas à API da IA

### Processamento Paralelo
- **Múltiplas Threads**: Análise simultânea de currículos
- **Balanceamento de Carga**: Distribui trabalho eficientemente
- **Recuperação de Falhas**: Retry automático para análises falhadas

### Monitoramento
- **Status em Tempo Real**: Acompanhe processamento em andamento
- **Logs Detalhados**: Histórico completo de operações
- **Métricas**: Estatísticas de uso e performance

## 🎨 Interface do Usuário

### Dashboard Principal
- **Métricas Gerais**: Total de vagas, candidatos, análises
- **Gráficos**: Distribuição de scores, status dos candidatos
- **Ações Rápidas**: Acesso direto às funcionalidades principais

### Gestão de Vagas
- **Lista Completa**: Todas as vagas com status
- **Filtros Avançados**: Por status, data, candidatos
- **Ações em Lote**: Operações em múltiplas vagas

### Análise de Candidatos
- **Ranking Automático**: Ordenado por compatibilidade
- **Filtros Inteligentes**: Por score, status, vaga
- **Comparação**: Análise lado a lado de candidatos

## 📊 Formato da Análise IA

### Resumo Executivo
```
Nome Completo: [Nome do candidato]

Experiência Relevante:
• [Cargo] na [Empresa] ([período])
• [Cargo] na [Empresa] ([período])
• [Cargo] na [Empresa] ([período])

Habilidades Técnicas: [Lista de skills]
Formação Acadêmica: [Educação e cursos]
Idiomas: [Idiomas e níveis]
Informações de Contato: [Email, telefone, localização]
```

### Análise da IA
```
1. Alinhamento Técnico:
• Experiência relevante: [específica]
• Competências alinhadas: [2-3 competências]
• Adequação à vaga: [explicação objetiva]

2. Gaps Técnicos:
• Lacunas identificadas: [2-3 lacunas]
• Conhecimentos em falta: [específicos]
• Recomendações: [2-3 desenvolvimentos]

3. Recomendação Final: [Adequado/Parcial/Inadequado]
• Pontos fortes: [2-3 pontos específicos]
• Limitações: [2-3 limitações]
• Justificativa: [explicação objetiva]
```

## 🔒 Segurança

### Autenticação
- **Hashing de Senhas**: Werkzeug para segurança
- **Sessões Seguras**: Flask-Login com tokens
- **Controle de Acesso**: Verificação de permissões

### Dados
- **Validação de Entrada**: Sanitização de dados
- **Arquivos Seguros**: Verificação de tipos permitidos
- **Backup**: Suporte a backup automático do banco

### API
- **Rate Limiting**: Controle de requisições
- **Logs de Auditoria**: Registro completo de ações
- **Monitoramento**: Alertas para atividades suspeitas

## 📈 Performance

### Otimizações
- **Conexões de Banco**: Pool de conexões configurado
- **Cache de Consultas**: Redução de queries repetidas
- **Compressão**: Gzip para responses HTTP
- **CDN Ready**: Arquivos estáticos otimizados

### Escalabilidade
- **Processamento Distribuído**: Múltiplos workers
- **Balanceamento**: Nginx + Gunicorn
- **Monitoramento**: Logs estruturados
- **Métricas**: Prometheus/Grafana ready

## 🚢 Deploy

### Replit (Recomendado)
1. Conecte o repositório ao Replit
2. Configure as variáveis de ambiente
3. Clique em "Deploy"
4. Aplicação estará disponível em `.replit.app`

### Heroku
```bash
# Instale Heroku CLI
pip install heroku3

# Deploy
heroku create viana-moura
heroku config:set DATABASE_URL=your_database_url
heroku config:set OPENAI_API_KEY=your_api_key
git push heroku main
```

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
```

## 🤝 Contribuindo

### Como Contribuir
1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Add nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Padrões de Código
- **PEP 8**: Estilo Python padrão
- **Type Hints**: Tipagem quando possível
- **Docstrings**: Documentação de funções
- **Testes**: Cobertura mínima de 80%

## 📞 Suporte

### Documentação
- **Wiki**: Documentação completa no GitHub
- **API Docs**: Swagger/OpenAPI disponível
- **Tutoriais**: Guides passo a passo

### Comunidade
- **Issues**: Reporte bugs e suggest features
- **Discussions**: Participe das discussões
- **Discord**: Chat da comunidade

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📋 Changelog

### v2.0.0 (Atual)
- ✅ Arquitetura modular com pastas services/, processors/, utils/
- ✅ Análise IA com formato estruturado (Resumo + Análise)
- ✅ Download de currículos originais
- ✅ Processamento paralelo otimizado
- ✅ Sistema de cache inteligente
- ✅ Interface responsiva moderna

### v1.0.0
- ✅ Sistema básico de análise de currículos
- ✅ Upload individual de arquivos
- ✅ Análise simples com IA
- ✅ Interface web básica

## 🏆 Reconhecimentos

- **DeepSeek**: Pela API de IA avançada
- **Flask Community**: Pelo framework robusto
- **Supabase**: Pela infraestrutura de banco
- **Bootstrap**: Pelo design system
- **Font Awesome**: Pelos ícones

---

<div align="center">
  <strong>Desenvolvido com ❤️ para revolucionar o recrutamento</strong>
  <br>
  <br>
  <a href="https://github.com/your-username/viana-moura/stargazers">⭐ Star este projeto</a>
  ·
  <a href="https://github.com/your-username/viana-moura/issues">🐛 Reportar Bug</a>
  ·
  <a href="https://github.com/your-username/viana-moura/issues">💡 Solicitar Feature</a>
</div>