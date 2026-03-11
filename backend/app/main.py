from fastapi import FastAPI, Depends, HTTPException, Header, Security,APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import SessionLocal
from .dependencies import criar_agendamento,get_db,verificar_api_key
from .schemas import AgendamentoCreate,StatusAgendamento
from .models import Agendamento
import os
from dotenv import load_dotenv
from sqlalchemy import func
from datetime import date
#uvicorn backend.app.main:app --reload
#alembic revision --autogenerate -m "relationship"


app = FastAPI(title="API de Agendamentos")

from .agend_routes import agendamentos_router
from .empresas_routes import empresas_router

app.include_router(agendamentos_router)
app.include_router(empresas_router)