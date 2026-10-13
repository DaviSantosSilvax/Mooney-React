from datetime import date
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from models import Institution, Category, Transaction, Account, User
from projection import Contribution, compare_scenarios, effective_annual_rate

app = FastAPI(
    title="Mooney API",
    description="Backend oficial da plataforma de investimentos e finanças Mooney",
    version="1.0.0"
)

# -------------------------------------------------------------
# 🌐 CORS (Permite que o React na porta 5173 acesse esta API)
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------
# 📌 Rotas da API
# -------------------------------------------------------------

@app.get("/")
def raiz():
    """Rota inicial para checar se a API está funcionando."""
    return {
        "status": "online",
        "mensagem": "Mooney API está rodando com sucesso!",
        "documentacao": "Acesse http://localhost:8000/docs para ver o Swagger"
    }


@app.get("/api/saldo")
def obter_saldo(db: Session = Depends(get_db)):
    """
    Retorna o saldo total consolidado e a lista de contas ativas.
    Consome a VIEW v_user_total_balance e v_account_balances do banco Mooney.
    """
    try:
        # Consulta o saldo total através da view
        total_balance = db.execute(text("SELECT total_balance FROM v_user_total_balance LIMIT 1;")).scalar()
        
        # Consulta saldos por conta através da view
        contas = db.execute(text("""
            SELECT account_id, name, balance, include_in_total 
            FROM v_account_balances;
        """)).fetchall()

        return {
            "saldo_total": float(total_balance) if total_balance is not None else 0.0,
            "moeda": "BRL",
            "contas": [
                {
                    "id": str(c.account_id),
                    "nome": c.name,
                    "saldo": float(c.balance),
                    "inclui_no_total": c.include_in_total
                }
                for c in contas
            ]
        }
    except Exception as e:
        # Se as views estiverem vazias sem contas cadastradas, retorna valor inicial amigável
        return {
            "saldo_total": 0.00,
            "moeda": "BRL",
            "contas": []
        }


@app.get("/api/transacoes")
def listar_transacoes(db: Session = Depends(get_db), limite: int = 10):
    """
    Retorna as últimas transações cadastradas no banco de dados.
    """
    transacoes = (
        db.query(Transaction)
        .order_by(Transaction.occurred_on.desc())
        .limit(limite)
        .all()
    )

    return [
        {
            "id": str(t.id),
            "descricao": t.description,
            "valor": float(t.amount),
            "tipo": t.type,
            "data": t.occurred_on.isoformat(),
            "categoria_id": str(t.category_id) if t.category_id else None
        }
        for t in transacoes
    ]


class NovaTransacaoPayload(BaseModel):
    valor: float
    descricao: str = "Nova transação"
    tipo: str = "income"  # "income" (receita) ou "expense" (despesa)


@app.post("/api/transacoes")
def criar_transacao(dados: NovaTransacaoPayload, db: Session = Depends(get_db)):
    """
    Cria uma nova transação no banco de dados e recalcula o saldo.
    """
    import hashlib
    import uuid

    # 1. Garante um usuário demo se ainda não existir
    usuario = db.query(User).first()
    if not usuario:
        usuario = User(
            name="Administrador Mooney",
            email="admin@gmail.com",
            password_hash="argon2_demo",
            currency="BRL"
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    # 2. Garante uma conta demo para associar a transação
    conta = db.query(Account).filter_by(user_id=usuario.id).first()
    if not conta:
        conta = Account(
            user_id=usuario.id,
            name="Conta Corrente Principal",
            type="checking",
            initial_balance=0.00
        )
        db.add(conta)
        db.commit()
        db.refresh(conta)

    # 3. Cria a nova transação
    dedupe = hashlib.sha256(f"{conta.id}:{date.today()}:{dados.valor}:{dados.descricao}:{uuid.uuid4()}".encode()).hexdigest()

    nova = Transaction(
        user_id=usuario.id,
        account_id=conta.id,
        description=dados.descricao,
        amount=dados.valor,
        type=dados.tipo if dados.tipo in ("income", "expense") else "income",
        occurred_on=date.today(),
        dedupe_hash=dedupe
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)

    return {
        "sucesso": True,
        "mensagem": "Transação registrada com sucesso!",
        "transacao": {
            "id": str(nova.id),
            "descricao": nova.description,
            "valor": float(nova.amount),
            "tipo": nova.type
        }
    }


class NovaContaPayload(BaseModel):
    banco: Optional[str] = None
    nome: Optional[str] = None
    saldo_atual: Optional[float] = 0.0
    saldo_inicial: Optional[float] = 0.0
    tipo: Optional[str] = "checking"
    institution_id: Optional[int] = None


@app.post("/api/contas")
def criar_conta(dados: NovaContaPayload, db: Session = Depends(get_db)):
    """
    Cria uma nova conta bancária para o usuário.
    Aceita tanto 'banco'/'saldo_atual' quanto 'nome'/'saldo_inicial'.
    """
    usuario = db.query(User).first()
    if not usuario:
        usuario = User(
            name="Administrador Mooney",
            email="admin@gmail.com",
            password_hash="argon2_demo",
            currency="BRL"
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    nome_conta = dados.nome or dados.banco or "Nova Conta"
    saldo = dados.saldo_inicial if dados.saldo_inicial is not None and dados.saldo_inicial > 0 else (dados.saldo_atual or 0.0)

    nova_conta = Account(
        user_id=usuario.id,
        name=nome_conta,
        type=dados.tipo if dados.tipo in ('checking', 'savings', 'credit_card', 'investment', 'cash', 'other') else 'checking',
        initial_balance=saldo,
        institution_id=dados.institution_id
    )
    db.add(nova_conta)
    db.commit()
    db.refresh(nova_conta)

    return {
        "sucesso": True,
        "mensagem": f"Conta '{nova_conta.name}' criada com sucesso!",
        "conta": {
            "id": str(nova_conta.id),
            "nome": nova_conta.name,
            "saldo": float(nova_conta.initial_balance)
        }
    }


@app.get("/api/contas")
@app.get("/api/bancos")
def listar_contas(db: Session = Depends(get_db)):
    """Lista todas as contas/bancos cadastrados."""
    contas = db.query(Account).filter_by(is_active=True).all()
    return [
        {
            "id": str(c.id),
            "nome": c.name,
            "banco": c.name,
            "saldo": float(c.initial_balance)
        }
        for c in contas
    ]


@app.get("/api/instituicoes")
def listar_instituicoes(db: Session = Depends(get_db)):
    """Lista todos os bancos e instituições disponíveis."""
    bancos = db.query(Institution).filter_by(is_active=True).all()
    return [
        {
            "id": b.id,
            "codigo": b.code,
            "nome": b.name,
            "codigo_banco": b.bank_code,
            "logo_url": b.logo_url
        }
        for b in bancos
    ]


# -------------------------------------------------------------
# 📈 Modelo e Rota de Projeção de Investimentos
# -------------------------------------------------------------

class AportePayload(BaseModel):
    amount: float
    frequency: str = "monthly"  # "once", "daily", "weekly", "monthly", "yearly"
    starts_on: date
    ends_on: Optional[date] = None


class ProjecaoPayload(BaseModel):
    valor_inicial: float = 10000.0
    data_inicio: date = date.today()
    data_fim: date
    tipo_taxa: str = "cdi_percent"  # "prefixed", "cdi_percent", "selic", "ipca_plus", "savings"
    valor_taxa: float = 110.0       # ex: 110% do CDI ou 12.5% a.a.
    cdi: Optional[float] = 14.9
    selic: Optional[float] = 13.75
    ipca: Optional[float] = 4.5
    regime_ir: str = "ir_regressive"
    aportes_extras: List[AportePayload] = []


@app.post("/api/projecao")
def calcular_projecao(dados: ProjecaoPayload):
    """
    Executa a projeção de rendimento composto e devolve o comparativo
    de cenários com gráficos pronto para o frontend.
    """
    try:
        taxa_efetiva = effective_annual_rate(
            rate_type=dados.tipo_taxa,
            rate_value=dados.valor_taxa,
            cdi=dados.cdi,
            selic=dados.selic,
            ipca=dados.ipca
        )

        aportes = [
            Contribution(
                amount=a.amount,
                frequency=a.frequency,
                starts_on=a.starts_on,
                ends_on=a.ends_on
            )
            for a in dados.aportes_extras
        ]

        resultado = compare_scenarios(
            initial_amount=dados.valor_inicial,
            start_date=dados.data_inicio,
            end_date=dados.data_fim,
            annual_rate=taxa_efetiva,
            extra=aportes,
            tax_regime=dados.regime_ir
        )

        return {
            "sucesso": True,
            "taxa_efetiva_anual": round(taxa_efetiva * 100, 2),
            "resultado": resultado
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
