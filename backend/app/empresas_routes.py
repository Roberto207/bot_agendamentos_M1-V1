from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .dependencies import get_db,verificar_api_key,verificar_api_key_empresa_create,verificar_token
from .schemas import EmpresaCreate, EmpresaUpdate
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
async def deletar_empresa(id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    empresa = db.query(Empresa).filter(Empresa.id == id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    if not usuario.admin and empresa.id_usuario_criador != usuario.id:
        raise HTTPException(status_code=403, detail="Apenas o admin ou o criador podem deletar a empresa")
    
    db.delete(empresa)
    db.commit()
    return {"msg": "Empresa deletada com sucesso"}

@empresas_router.put("/{id}")
async def atualizar_empresa(id: int, dados: EmpresaUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    empresa = db.query(Empresa).filter(Empresa.id == id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    if not usuario.admin and empresa.id_usuario_criador != usuario.id:
        raise HTTPException(status_code=403, detail="Apenas o admin ou o criador podem atualizar a empresa")
    
    if dados.nome is not None:
        empresa.nome = dados.nome
    if dados.telefone is not None:
        empresa.telefone = dados.telefone
    if dados.ramo_empresa is not None:
        empresa.ramo_empresa = dados.ramo_empresa
    if dados.endereco_empresa is not None:
        empresa.endereco_empresa = dados.endereco_empresa
        
    db.commit()
    db.refresh(empresa)
    return empresa