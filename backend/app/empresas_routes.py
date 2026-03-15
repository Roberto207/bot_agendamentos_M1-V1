from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from .dependencies import get_db,verificar_api_key,verificar_api_key_empresa_create,verificar_token,update_model_strict
from .schemas import EmpresaCreate, EmpresaUpdate,EmpresaOut
from .models import Empresa,HorarioFuncionamento,Usuario
from .main import bcrypt_context
import secrets
# from sqlalchemy.ext.asyncio import AsyncSession  # Se usar asynsc
from sqlalchemy.future import select  # Para consultas async


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
        endereco_empresa=empresa.endereco_empresa,
        api_key=api_key,
        id_usuario_criador=usuario.id
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


@empresas_router.delete("/{id}")
async def deletar_empresa(id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token),senha_usuario: str = Header(None)):
    empresa = db.query(Empresa).filter(Empresa.id == id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    if usuario.admin:
        pass
    
    elif empresa.id_usuario_criador == usuario.id:
        if not bcrypt_context.verify(senha_usuario, usuario.senha):
            raise HTTPException(status_code=403, detail="Senha incorreta ou sem autorizacao")
    else:
        raise HTTPException(status_code=403, detail="Sem permissão para deletar esta empresa")
    
    
    db.delete(empresa)
    db.commit()
    return {"msg": "Empresa deletada com sucesso"}






@empresas_router.put("/{id}",response_model=EmpresaOut)
def atualizar_empresa(
    empresa_id: int,
    dados: EmpresaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(verificar_token),
    senha_usuario: str = Header(None)
):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    # Verificação de permissão
    if usuario.admin:
        pass
    
    elif empresa.id_usuario_criador == usuario.id:
        if not bcrypt_context.verify(senha_usuario, usuario.senha):
            raise HTTPException(status_code=403, detail="Senha incorreta ou sem autorizacao")
    else:
        raise HTTPException(status_code=403, detail="Sem permissão para atualizar esta empresa")
    


    # Atualiza
    empresa_atualizada = update_model_strict(db, empresa, dados)
    
    # Retorna convertido para schema Pydantic
    return empresa_atualizada
