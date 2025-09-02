import os
import logging
from flask import Flask
from dotenv import load_dotenv
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.DEBUG)

# Importar configurações do banco
from database import db, init_db
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

# Configurações de upload
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Tamanho máximo de arquivo: 16MB
app.config['UPLOAD_FOLDER'] = 'uploads'

# Inicializa o banco de dados
init_db(app)

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
    # Certifique-se de importar os models aqui, senão as tabelas não serão criadas
    import models.models  # noqa: F401
    import controllers.routes  # noqa: F401
    
    try:
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