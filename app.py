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

# Configuração de logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Cria a aplicação Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
# Necessário para o url_for gerar URLs com https quando atrás de proxy reverso
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configura os headers de CORS para melhor compatibilidade
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Configura a URL do banco de dados, relativa à instância da aplicação
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Usa a string de conexão do Supabase do .env se DATABASE_URL não estiver funcionando
if not database_url or "neon.tech" in database_url:
    database_url = "postgresql://postgres.bndkpowgvagtlxwmthma:5585858Vini%40@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"

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

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Cria a pasta de uploads se ela não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    # Certifique-se de importar os models aqui, senão as tabelas não serão criadas
    import models  # noqa: F401
    import routes  # noqa: F401
    
    try:
        db.create_all()
        logging.info("Tabelas do banco de dados criadas com sucesso")
        
        # Cria usuário admin se ele ainda não existir
        from models import User
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