from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .dependencies import get_db, verificar_api_key, verificar_api_key_empresa_create, verificar_token, verificar_acesso_empresa, update_model_strict
from .schemas import EmpresaCreate, EmpresaUpdate
from .models import Empresa, HorarioFuncionamento, Usuario, UsuarioEmpresa, NivelAcesso
import secrets



empresas_router = APIRouter(prefix="/empresa", tags=["Empresa"])

@empresas_router.post("/cadastrar_empresa")
async def cadastrar_empresa(
    empresa: EmpresaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(verificar_token)
):
    empresa_existente = db.query(Empresa).filter(Empresa.cnpj == empresa.cnpj).first() or db.query(Empresa).filter(Empresa.email == empresa.email).first()
    if empresa_existente:
        raise HTTPException(status_code = 404,detail = "empresa ja cadastrada,verifique o email ou o cnpj")
    api_key = secrets.token_hex(16)
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

    # Criar vínculo automático: criador vira admin_empresa na tabela intermediária
    vinculo_criador = UsuarioEmpresa(
        usuario_id=usuario.id,
        empresa_id=nova_empresa.id,
        nivel=NivelAcesso.admin_empresa.value,
        convidado_por=None
    )
    db.add(vinculo_criador)

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


@empresas_router.delete("/{empresa_id}")
async def deletar_empresa(
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=3)),
    db: Session = Depends(get_db)
):
    """Apenas admin_empresa (nível 3), criador ou admin do site podem deletar"""
    empresa = acesso["empresa"]
    
    db.delete(empresa)
    db.commit()
    return {"msg": "Empresa deletada com sucesso"}



@empresas_router.put("/{empresa_id}")
async def atualizar_empresa(
    dados: EmpresaUpdate,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=3)),
    db: Session = Depends(get_db)
):
    """Apenas admin_empresa (nível 3), criador ou admin do site podem atualizar"""
    empresa = acesso["empresa"]
    
    empresa_atualizada = update_model_strict(db=db, model_instance=empresa, update_schema=dados)
    return empresa_atualizada