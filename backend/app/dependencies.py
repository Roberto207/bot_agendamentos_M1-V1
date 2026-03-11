from sqlalchemy.orm import Session
from .models import Agendamento,Empresa
from .schemas import AgendamentoCreate
from sqlalchemy.exc import IntegrityError, InternalError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .database import SessionLocal
from fastapi import FastAPI, Depends, HTTPException, Header, Security,APIRouter
import os
from dotenv import load_dotenv



load_dotenv()
API_KEY = os.getenv("SECRET_KEY")
async def criar_agendamento(db: Session, agendamento: AgendamentoCreate,empresa: Empresa):
    novo = Agendamento(
    empresa_id=empresa.id,
    nome=agendamento.nome,
    telefone=agendamento.telefone,
    data_servico=agendamento.data_servico,
    hora_inicio=agendamento.hora_inicio,
    hora_fim=agendamento.hora_fim,
    tipos_servico=agendamento.tipos_servico
)


    db.add(novo)
    try:
        db.commit()
        db.refresh(novo)
        return {"status": "confirmado", "mensagem": "Agendamento confirmado", "id": novo.id}
    except (IntegrityError, InternalError) as e:
        db.rollback()
        return {
            "status": "erro",
            "mensagem": "Horário já ocupado"
        }

# Dependência para DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

security = HTTPBearer()

# Dependência simples de autenticação
async def verificar_api_key(
    credentials = Security(security),
    telefone_empresa: str = Header(...),
    db: Session = Depends(get_db)
):

    api_key = credentials.credentials

    empresa = db.query(Empresa).filter(
        #Empresa.api_key == api_key,
        Empresa.telefone == telefone_empresa
    ).first()

    if not empresa:
        raise HTTPException(
            status_code=401,
            detail="Empresa não autenticada"
        )

    return empresa

async def verificar_api_key_empresa_create(credentials = Security(security)):

    api_key = credentials.credentials
    admin_key = os.getenv("ADMIN_API_KEY")

    if api_key != admin_key:
        raise HTTPException(
            status_code=403,
            detail="API key inválida"
        )

    return True