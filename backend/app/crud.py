from sqlalchemy.orm import Session
from .models import Agendamento
from .schemas import AgendamentoCreate
from sqlalchemy.exc import IntegrityError, InternalError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .database import SessionLocal
from fastapi import FastAPI, Depends, HTTPException, Header, Security,APIRouter
import os
from dotenv import load_dotenv



load_dotenv()
API_KEY = os.getenv("SECRET_KEY")
def criar_agendamento(db: Session, agendamento: AgendamentoCreate):
    novo = Agendamento(**agendamento.dict())
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
def verificar_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Não autorizado")