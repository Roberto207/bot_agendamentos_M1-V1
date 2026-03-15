from sqlalchemy.orm import Session
from .models import Agendamento,Empresa,Cliente,Usuario,UsuarioEmpresa
from .schemas import AgendamentoCreate
from sqlalchemy.exc import IntegrityError, InternalError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials,OAuth2PasswordBearer
from .database import SessionLocal
from fastapi import FastAPI, Depends, HTTPException, Header, Security,APIRouter
import os
from dotenv import load_dotenv
from jose import JWTError, jwt
from pydantic import BaseModel, field_validator
from typing import Type,TypeVar
from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=["argon2"], deprecated="auto")
bearer_scheme = HTTPBearer()
load_dotenv()
API_KEY = os.getenv("SECRET_KEY")


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth_site/login_formula")

ModelType = TypeVar("ModelType")

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
            detail="Empresa não autentificada"
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


def verificar_acesso_empresa(nivel_minimo: int = 1):
    """
    Dependency factory que retorna uma dependência FastAPI.
    Verifica se o usuário logado tem acesso à empresa com nível >= nivel_minimo.
    
    Ordem de checagem:
    1. Admin do site → acesso total (nível 3)
    2. Criador da empresa (retrocompatibilidade) → nível 3
    3. Vínculo na tabela usuarios_empresas → checa nível
    
    Retorna dict: {"usuario": ..., "empresa": ..., "nivel": ...}
    """
    async def _verificar(
        empresa_id: int,
        db: Session = Depends(get_db),
        usuario: Usuario = Depends(verificar_token)
    ):
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not empresa:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")

        # 1. Admin do site → acesso total
        if usuario.admin:
            return {"usuario": usuario, "empresa": empresa, "nivel": 3}

        # 2. Retrocompatibilidade: criador da empresa = admin_empresa
        if empresa.id_usuario_criador == usuario.id:
            return {"usuario": usuario, "empresa": empresa, "nivel": 3}

        # 3. Vínculo na tabela usuarios_empresas
        vinculo = db.query(UsuarioEmpresa).filter(
            UsuarioEmpresa.usuario_id == usuario.id,
            UsuarioEmpresa.empresa_id == empresa_id
        ).first()

        if not vinculo or vinculo.nivel < nivel_minimo:
            raise HTTPException(status_code=403, detail="Sem permissão para acessar esta empresa")
        
        return {"usuario": usuario, "empresa": empresa, "nivel": vinculo.nivel}
    
    return _verificar






def update_model_strict(
    db: Session, 
    model_instance: ModelType, 
    update_schema: BaseModel,
    strings_ignoradas: list[str] = None
) -> ModelType:
    """
    Atualiza apenas campos válidos.
    Strings ignoradas: None, vazias, "string", ou customizadas
    """
    if strings_ignoradas is None:
        strings_ignoradas = ["string", "null", "undefined", "none","int","float","bool","true","false"]
    
    # Converte tudo para lowercase para comparação
    strings_ignoradas = [s.lower() for s in strings_ignoradas]
    

    # 1. PEGA SÓ OS CAMPOS QUE FORAM ENVIADOS NA REQUISIÇÃO
    # exclude_unset=True = ignora campos que não vieram no JSON
    # Exemplo: se enviou só {"endereco": "Rua X"}, 
    # update_data = {"endereco": "Rua X"} (nome, telefone etc não aparecem)

    update_data = update_schema.model_dump(exclude_unset=True)
    
    # 2. PERCORRE CADA CAMPO ENVIADO
    for field, value in update_data.items():
        # field = nome do campo (ex: "endereco")
        # value = valor enviado (ex: "Rua X")
        if value is None:
            continue

        # 3. IGNORA SE VALOR FOR None, STRING VAZIA, OU STRING IGNORADA
        # # 4. SE FOR STRING, VERIFICA REGRAS EXTRAS    
        if isinstance(value, str):
            stripped = value.strip().lower()
            if stripped == "" or stripped in strings_ignoradas:
                continue
                
            # SE O CAMPO FOR "SENHA", FAZ HASH!
            if field == "senha":
                # Hash da senha antes de salvar
                hashed_value = bcrypt_context.hash(value)
                setattr(model_instance, field, hashed_value)
                continue  # Já tratou, vai para próximo campo
        
        # 5. SE CHEGOU AQUI, VALOR É VÁLIDO → ATUALIZA NO BANCO
        setattr(model_instance, field, value)
    

    

    #adiciona no banco de dados
    db.commit()
    db.refresh(model_instance)
    return model_instance
