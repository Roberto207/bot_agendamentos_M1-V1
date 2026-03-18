from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

#uvicorn backend.app.main:app --reload
#alembic revision --autogenerate -m "relationship"


app = FastAPI(title="API de Agendamentos")

# Configuração de CORS para permitir que o Lovable (Frontend) acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv() #carregando as variaveis de ambiente do arquivo .env

SECRET_KEY = os.getenv("SECRET_KEY") #pegando a secret key do .env pra usar na criptografia
ALGORITHM = os.getenv("ALGORITHM") 
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

bcrypt_context = CryptContext(schemes=["argon2"], deprecated="auto") #configurando o esquema de criptografia.
#definimos o esquema de cryptografia como bcrypt e deprecated auto pra n usar esquemas antigos

oauth2_schema = OAuth2PasswordBearer(tokenUrl="auth_site/login_formula") #definindo o esquema de autenticacao do tipo oauth2, onde o cliente vai enviar um token jwt no header da requisicao pra acessar rotas protegidas da api, o token jwt é gerado na rota de login e tem um tempo de expiracao definido na variavel ACCESS_TOKEN_EXPIRE_MINUTES, entao o cliente precisa fazer login novamente depois desse tempo pra obter um novo token jwt.

from .agend_routes import agendamentos_router
from .empresas_routes import empresas_router
from .auth_site_router import auth_site_router
from .servicos_routes import servicos_router
from .vinculos_routes import vinculos_router
from .dashboard_routes import dashboard_router

app.include_router(agendamentos_router)
app.include_router(empresas_router)
app.include_router(auth_site_router)
app.include_router(servicos_router)
app.include_router(vinculos_router)
app.include_router(dashboard_router)