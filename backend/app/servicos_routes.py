from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .dependencies import get_db, verificar_api_key
from datetime import date, time
from .models import Servicos, Empresa,Profissional
from .schemas import ServicoSchema

servicos_router = APIRouter(prefix='/servicos', tags=['Serviços'])

@servicos_router.post("/cadastrar_profissionais")
async def criar_profissional(
    nome: str,
    funcao: str,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):

    novo = Profissional(
        nome=nome,
        empresa_id=empresa.id,
        funcao=funcao
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    return novo

@servicos_router.post("/cadastrar_servicos")
async def criar_servico(
    servico: ServicoSchema,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):

    novo = Servicos(
        nome=servico.nome,
        duracao=servico.duracao,
        preco=servico.preco,
        empresa_id=empresa.id,
        descricao=servico.descricao,
        tempo_buffer=servico.tempo_buffer

    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    return novo



@servicos_router.post("/servicos/{servico_id}/ligar_profissionais_servicos")
async def adicionar_profissionais(
    servico_id: int,
    profissionais_ids: list[int],
    db: Session = Depends(get_db)
):

    servico = db.query(Servicos).filter(
        Servicos.id == servico_id
    ).first()

    profissionais = db.query(Profissional).filter(
        Profissional.id.in_(profissionais_ids)
    ).all()

    servico.profissionais.extend(profissionais)

    db.commit()

    return {"msg": "Profissionais vinculados"}


# async def criar_servico(servico: ServicoSchema, db: Session = Depends(get_db), empresa: Empresa = Depends(verificar_api_key)):
#     if not empresa:
#         raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
#     if servico.duracao <= 0:
#         raise HTTPException(status_code=400, detail="A duração do serviço deve ser maior que zero")
    
#     if servico.preco < 0:
#         raise HTTPException(status_code=400, detail="O preço do serviço não pode ser negativo")
    
#     if servico.tempo_buffer < 0:
#         raise HTTPException(status_code=400, detail="O tempo de buffer não pode ser negativo")
    
#     if not servico.nome.strip():
#         raise HTTPException(status_code=400, detail="O nome do serviço não pode ser vazio")
    
#     servico_existente = db.query(Servicos).filter(Servicos.nome == servico.nome, Servicos.empresa_id == empresa.id).first()
#     if servico_existente:
#         raise HTTPException(status_code=400, detail="Já existe um serviço com esse nome para esta empresa")
    
    
    
    
#     novo_servico = Servicos(
#         nome=servico.nome,
#         duracao=servico.duracao,
#         preco=servico.preco,
#         empresa_id=empresa.id,
#         descricao=servico.descricao,
#         tempo_buffer=servico.tempo_buffer
#     )
#     db.add(novo_servico)
#     db.commit()
#     db.refresh(novo_servico)
#     return {"id": novo_servico.id, "nome": novo_servico.nome, "duracao": novo_servico.duracao, "preco": novo_servico.preco,"empresa":empresa.nome}



