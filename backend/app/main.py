from fastapi import FastAPI, Depends, HTTPException, Header, Security,APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import SessionLocal
from .crud import criar_agendamento,get_db,verificar_api_key
from .schemas import AgendamentoCreate
from .models import Agendamento,StatusAgendamento
import os
from dotenv import load_dotenv
from sqlalchemy import func
from datetime import date



app = FastAPI(title="API de Agendamentos")

from .agend_routes import agendamentos_router
app.include_router(agendamentos_router)