import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/postgres')
SCHEMA_NAME = os.getenv('SCHEMA_NAME', 'appcurriculos')

# Configurar metadados com schema
metadata = MetaData(schema=SCHEMA_NAME)

# Inicializar SQLAlchemy
db = SQLAlchemy(metadata=metadata)

def init_db(app):
    """Inicializar o banco de dados com a aplicação Flask"""
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    db.init_app(app)
    
    with app.app_context():
        # Criar schema se não existir
        with db.engine.connect() as conn:
            conn.execute(db.text(f'CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}'))
            conn.commit()
        
        # Criar todas as tabelas
        db.create_all()
        
        print(f"✅ Banco de dados inicializado com sucesso!")
        print(f"✅ Schema '{SCHEMA_NAME}' verificado/criado")
