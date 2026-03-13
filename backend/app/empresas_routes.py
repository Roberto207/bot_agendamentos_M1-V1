from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .dependencies import get_db,verificar_api_key,verificar_api_key_empresa_create,verificar_token
from .schemas import EmpresaCreate
from .models import Empresa,HorarioFuncionamento,Usuario
import secrets



empresas_router = APIRouter(prefix="/empresa", tags=["Empresa"])

@empresas_router.post("/cadastrar_empresa")
async def cadastrar_empresa(
    empresa: EmpresaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(verificar_token)
):
    empresa_existente = db.query(Empresa).filter(Empresa.cnpj == empresa.cnpj).first() or db.query(Empresa).filter(Empresa.email == empresa.email).first() #verificando se o cnpj ou email da empresa ja esta cadastrado na database, se tiver, nao pode cadastrar de novo
    if empresa_existente:
        raise HTTPException(status_code = 404,detail = "empresa ja cadastrada,verifique o email ou o cnpj")
    api_key = secrets.token_hex(16)  # Gerar uma chave de API única para a empresa,mudei de 32 pra 16
    nova_empresa = Empresa(
        nome=empresa.nome,
        cnpj=empresa.cnpj,
        email=empresa.email,
        telefone=empresa.telefone,
        ramo_empresa=empresa.ramo_empresa,
        api_key = api_key 
    )

    db.add(nova_empresa)
    db.commit()
    db.refresh(nova_empresa)

    for horario in empresa.horarios:

        novo_horario = HorarioFuncionamento(
            empresa_id=nova_empresa.id,
            dia_semana=horario.dia_semana,
            horario_inicio=horario.horario_inicio,
            horario_fim=horario.horario_fim
        )

        db.add(novo_horario)

    db.commit()

    return {
        "id": nova_empresa.id,
        "nome": nova_empresa.nome,
        "api_key": api_key
    }

@empresas_router.get("/listar_empresas")
async def listar_empresas(db: Session = Depends(get_db),usuario : Usuario = Depends(verificar_token)):
    if not usuario.admin:
        raise HTTPException(status_code=403,detail="Acesso negado, apenas administradores podem acessar essa rota")
    
    empresas = db.query(Empresa).all()
    return empresas