import os
from pathlib import Path
from database import engine

def apply_schema():
    sql_path = Path(__file__).resolve().parent / "schema.sql"
    print(f"Lendo arquivo de schema: {sql_path}")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    print("Conectando ao PostgreSQL Mooney e aplicando todas as tabelas, tipos e views...")
    
    # Executa usando a conexao do psycopg2 atraves do engine do SQLAlchemy
    with engine.connect() as conn:
        raw_conn = conn.connection
        with raw_conn.cursor() as cursor:
            cursor.execute(sql_content)
        raw_conn.commit()

    print("[SUCESSO] Todas as tabelas, tipos, indices e views foram criadas com exito!")

if __name__ == "__main__":
    apply_schema()
