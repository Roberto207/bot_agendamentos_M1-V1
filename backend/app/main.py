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
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

#uvicorn backend.app.main:app --reload
#alembic revision --autogenerate -m "relationship"


app = FastAPI(title="API de Agendamentos")

load_dotenv() #carregando as variaveis de ambiente do arquivo .env

SECRET_KEY = os.getenv("SECRET_KEY") #pegando a secret key do .env pra usar na criptografia
ALGORITMH = os.getenv("ALGORITMH") 
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

bcrypt_context = CryptContext(schemes=["argon2"], deprecated="auto") #configurando o esquema de criptografia.
#definimos o esquema de cryptografia como bcrypt e deprecated auto pra n usar esquemas antigos

oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/login_formula")

from .agend_routes import agendamentos_router
from .empresas_routes import empresas_router
from .clientes_router import clientes_auth_router

app.include_router(agendamentos_router)
app.include_router(empresas_router)
app.include_router(clientes_auth_router)