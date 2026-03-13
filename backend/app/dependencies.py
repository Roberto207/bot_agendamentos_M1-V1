from sqlalchemy.orm import Session
from .models import Agendamento,Empresa,Cliente,Usuario
from .schemas import AgendamentoCreate,Origem_Cliente
from sqlalchemy.exc import IntegrityError, InternalError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials,OAuth2PasswordBearer
from .database import SessionLocal
from fastapi import FastAPI, Depends, HTTPException, Header, Security,APIRouter
import os
from dotenv import load_dotenv
from jose import JWTError, jwt


bearer_scheme = HTTPBearer()
load_dotenv()
API_KEY = os.getenv("SECRET_KEY")


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth_site/login_formula")

async def criar_agendamento_whatssap(db: Session, agendamento: AgendamentoCreate, empresa: Empresa):
    cliente_existente = db.query(Cliente).filter(Cliente.telefone == agendamento.telefone_cliente).first()
    novo = Agendamento(
    empresa_id=empresa.id,
    nome_cliente=agendamento.nome_cliente,
    telefone_cliente=agendamento.telefone_cliente,
    data_servico=agendamento.data_servico,
    hora_inicio=agendamento.hora_inicio,
    hora_fim=agendamento.hora_fim,
    cliente_id = cliente_existente.id if cliente_existente else None,
    tipos_servico=agendamento.tipos_servico,
    origem = Origem_Cliente.whatsapp)



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

def verificar_token(token: str = Depends(oauth2_schema),db: Session = Depends(get_db)):

    try:
        dict_info = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        

        id_usuario = int(dict_info.get("sub"))
        if not id_usuario:
            raise HTTPException(status_code=401, detail="Token sem sub = ids")
    except JWTError as erro:
        print(erro)
        raise HTTPException(status_code=401,detail="acesso negado,verifique a validade do token")
        

    #verificar se o token é valido
    #extrair o id do usuario do token 
    usuario = db.query(Usuario).filter(Usuario.id==id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=401,detail="acesso invalido")
    return usuario



# Dependência simples de autenticação
async def verificar_api_key(
    credentials = Security(security),
    telefone_empresa: str = Header(...),
    db: Session = Depends(get_db)
):

    api_key = credentials.credentials
    
    
        
    empresa = db.query(Empresa).filter(
        Empresa.api_key == api_key,
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