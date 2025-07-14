from sqlalchemy import create_engine
from urllib.parse import quote_plus

# Codifica a senha com caractere especial
senha = quote_plus("vYAeipsI0DBlO1sw")

# ✅ Opção 3: Shared Pooler (IPv4 compatível)
DATABASE_URL = f"postgresql+psycopg2://postgres.dxznqzpnsijpcmigpnfm:{senha}@aws-0-sa-east-1.pooler.supabase.com:5432/postgres"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect():
        print("Conexão com PostgreSQL (Supabase): SUCESSO!")
except Exception as e:
    print("Conexão com PostgreSQL (Supabase): FALHOU!")
    print(f"Erro: {e}")