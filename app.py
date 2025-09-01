import os
import logging
from flask import Flask
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import MetaData, text

# Configuração de logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

DB_SCHEMA = os.environ.get("DB_SCHEMA", "public")

metadata = MetaData(schema=DB_SCHEMA)
db = SQLAlchemy(model_class=Base, metadata=metadata)
login_manager = LoginManager()

# Cria a aplicação Flask
app = Flask(__name__, 
            template_folder='views/templates',
            static_folder='views/static')
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
# Necessário para o url_for gerar URLs com https quando atrás de proxy reverso
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configura os headers de CORS para melhor compatibilidade
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Configuração do banco de dados
def get_database_url():
    """Get Supabase database URL"""
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        raise ValueError("DATABASE_URL não encontrada no arquivo .env")
    
    # Fix postgres:// to postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Test PostgreSQL connection
    try:
        import psycopg2
        
        # Use the URL directly instead of parsing
        conn = psycopg2.connect(database_url)
        conn.close()
        logging.info("✅ Conexão com Supabase bem-sucedida!")
        return database_url
    except Exception as e:
        logging.error(f"❌ Erro na conexão com Supabase: {e}")
        raise Exception(f"Não foi possível conectar ao Supabase: {e}")

# Configura a URL do banco de dados
database_url = get_database_url()

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Configurações de upload
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Tamanho máximo de arquivo: 16MB
app.config['UPLOAD_FOLDER'] = 'uploads'

# Inicializa o SQLAlchemy com a aplicação
db.init_app(app)

# Inicializa o Login Manager
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Filtro personalizado para formatar requisitos da vaga
@app.template_filter('format_requirements')
def format_requirements(text):
    """Formata os requisitos da vaga para exibição melhorada"""
    if not text:
        return text
    
    # Substitui marcadores comuns por HTML formatado
    formatted = text.replace('*', '•')
    
    # Identifica seções específicas
    sections = {
        'Funções': 'fas fa-cogs',
        'Formação': 'fas fa-graduation-cap',
        'Conhecimentos': 'fas fa-brain',
        'Habilidades': 'fas fa-star'
    }
    
    # Formata cada seção
    for section, icon in sections.items():
        if section in formatted:
            formatted = formatted.replace(
                f'{section}',
                f'<h6 class="mt-3 mb-2"><i class="{icon} me-2"></i>{section}</h6>'
            )
    
    # Processa especificamente a formatação de "Mínimo Exigido" e "Desejável"
    import re
    
    # Formata "Mínimo Exigido" e "Desejável"
    formatted = re.sub(
        r'(Mínimo Exigido|Desejável)\s*([^•\n]*)',
        r'<strong>\1:</strong> \2',
        formatted
    )
    
    # Converte quebras de linha em parágrafos
    paragraphs = formatted.split('\n')
    formatted_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if para:
            if para.startswith('•'):
                # Lista com bullets
                formatted_paragraphs.append(f'<li>{para[1:].strip()}</li>')
            elif para.startswith('<h6'):
                # Títulos de seção
                formatted_paragraphs.append(para)
            elif para.startswith('<strong>'):
                # Texto com formatação especial
                formatted_paragraphs.append(f'<p class="mb-2">{para}</p>')
            else:
                # Texto normal
                formatted_paragraphs.append(f'<p class="mb-2">{para}</p>')
    
    # Agrupa itens de lista
    result = []
    in_list = False
    
    for item in formatted_paragraphs:
        if item.startswith('<li>'):
            if not in_list:
                result.append('<ul class="mb-3">')
                in_list = True
            result.append(item)
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(item)
    
    if in_list:
        result.append('</ul>')
    
    return ''.join(result)

@login_manager.user_loader
def load_user(user_id):
    from models.models import User
    return User.query.get(int(user_id))

# Cria a pasta de uploads se ela não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    # Garante que o schema exista antes de criar as tabelas
    try:
        if DB_SCHEMA and DB_SCHEMA != "public":
            with db.engine.connect() as conn:
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}"'))
                conn.commit()
            logging.info(f"Schema '{DB_SCHEMA}' verificado/criado com sucesso")
    except Exception as e:
        logging.error(f"Erro ao garantir schema '{DB_SCHEMA}': {e}")

    # Certifique-se de importar os models aqui, senão as tabelas não serão criadas
    import models.models  # noqa: F401
    import controllers.routes  # noqa: F401
    
    try:
        db.create_all()
        logging.info("Tabelas do banco de dados criadas com sucesso")
        
        # Cria usuário admin se ele ainda não existir
        from models.models import User
        admin_user = User.query.filter_by(email='viniciusniceas@vianaemoura.com.br').first()
        if not admin_user:
            try:
                admin_user = User(
                    username='admin',
                    email='viniciusniceas@vianaemoura.com.br',
                    role='admin'
                )
                admin_user.set_password('5585858Vi@')
                db.session.add(admin_user)
                db.session.commit()
                logging.info("Usuário admin criado: viniciusniceas@vianaemoura.com.br")
            except Exception as e:
                logging.info(f"Usuário admin já existe: {e}")
                db.session.rollback()
        
    except Exception as e:
        logging.error(f"Erro no banco de dados: {e}")
        logging.info("As tabelas do banco de dados serão criadas quando a conexão estiver disponível")