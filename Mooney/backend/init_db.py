from database import engine, Base, SessionLocal
from models import Usuario, Transacao, TipoTransacao
from decimal import Decimal


def init_database():
    print("Conectando ao banco de dados Mooney e criando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("[OK] Tabelas criadas com sucesso no PostgreSQL!")

    # Cria dados de exemplo se o banco estiver vazio
    db = SessionLocal()
    try:
        user_existente = db.query(Usuario).filter_by(email="admin@gmail.com").first()
        if not user_existente:
            print("Criando usuario inicial de teste (admin@gmail.com)...")
            usuario_demo = Usuario(
                nome="Administrador Mooney",
                email="admin@gmail.com",
                senha="123456",  # Em producao utilize hash seguro (ex: bcrypt/passlib)
                saldo=Decimal("2500.00")
            )
            db.add(usuario_demo)
            db.commit()
            db.refresh(usuario_demo)

            # Transacoes de exemplo
            t1 = Transacao(
                usuario_id=usuario_demo.id,
                descricao="Salario Mensal",
                valor=Decimal("3000.00"),
                tipo=TipoTransacao.RECEITA,
                categoria="Trabalho"
            )
            t2 = Transacao(
                usuario_id=usuario_demo.id,
                descricao="Assinatura Servicos",
                valor=Decimal("500.00"),
                tipo=TipoTransacao.DESPESA,
                categoria="Contas"
            )
            db.add_all([t1, t2])
            db.commit()
            print("[OK] Usuario de teste e transacoes criados com sucesso!")
        else:
            print("[INFO] Usuario 'admin@gmail.com' ja existe no banco.")

    except Exception as e:
        print(f"[ERRO] Erro ao popular dados iniciais: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
