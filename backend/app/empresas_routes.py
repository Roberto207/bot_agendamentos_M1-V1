from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import SessionLocal
from .dependencies import get_db,verificar_api_key,verificar_api_key_empresa_create
from .schemas import EmpresaCreate
from .models import Empresa,HorarioFuncionamento

empresas_router = APIRouter(prefix="/empresa", tags=["Empresa"])

@empresas_router.post("/cadastrar_empresa")
async def cadastrar_empresa(
    empresa: EmpresaCreate,
    db: Session = Depends(get_db),
    autorizado: bool = Depends(verificar_api_key_empresa_create)
):

    nova_empresa = Empresa(
        nome=empresa.nome,
        cnpj=empresa.cnpj,
        email=empresa.email,
        telefone=empresa.telefone,
        ramo_empresa=empresa.ramo_empresa
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
        "nome": nova_empresa.nome
    }