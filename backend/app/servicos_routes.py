from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .dependencies import get_db, verificar_api_key
from datetime import date, time
from .models import Servicos, Empresa,Profissional
from .schemas import ServicoSchema, ServicoUpdate, ProfissionalCreate, ProfissionalUpdate

servicos_router = APIRouter(prefix='/servicos', tags=['Serviços'])

@servicos_router.post("/cadastrar_profissionais")
async def criar_profissional(
    dados: ProfissionalCreate,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):

    novo = Profissional(
        nome=dados.nome,
        empresa_id=empresa.id,
        funcao=dados.funcao,
        hora_inicio=dados.hora_inicio,
        hora_fim=dados.hora_fim
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



@servicos_router.post("/{servico_id}/ligar_profissionais_servicos")
async def adicionar_profissionais(
    servico_id: int,
    profissionais_ids: list[int],
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
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



@servicos_router.get("/listar_servicos_profissionais")
async def listar_servicos_profissionais(
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):
    servicos = db.query(Servicos).filter(Servicos.empresa_id == empresa.id, Servicos.ativo == True).all()
    
    resultado = []
    for servico in servicos:
        profissionais = [{"id": prof.id, "nome": prof.nome, "funcao": prof.funcao} for prof in servico.profissionais if prof.ativo]
        resultado.append({
            "id": servico.id,
            "nome": servico.nome,
            "descricao": servico.descricao,
            "duracao": servico.duracao,
            "preco": servico.preco,
            "profissionais": profissionais
        })
    
    return resultado

@servicos_router.put("/{id}")
async def atualizar_servico(
    id: int,
    dados: ServicoUpdate,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):
    servico = db.query(Servicos).filter(Servicos.id == id, Servicos.empresa_id == empresa.id).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    if dados.nome is not None:
        servico.nome = dados.nome
    if dados.descricao is not None:
        servico.descricao = dados.descricao
    if dados.duracao is not None:
        servico.duracao = dados.duracao
    if dados.tempo_buffer is not None:
        servico.tempo_buffer = dados.tempo_buffer
    if dados.preco is not None:
        servico.preco = dados.preco
    if dados.ativo is not None:
        servico.ativo = dados.ativo
        
    db.commit()
    db.refresh(servico)
    return servico

@servicos_router.delete("/{id}")
async def deletar_servico(
    id: int,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):
    servico = db.query(Servicos).filter(Servicos.id == id, Servicos.empresa_id == empresa.id).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    db.delete(servico)
    db.commit()
    return {"msg": "Serviço deletado com sucesso"}

@servicos_router.put("/profissionais/{id}")
async def atualizar_profissional(
    id: int,
    dados: ProfissionalUpdate,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):
    profissional = db.query(Profissional).filter(Profissional.id == id, Profissional.empresa_id == empresa.id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    
    if dados.nome is not None:
        profissional.nome = dados.nome
    if dados.funcao is not None:
        profissional.funcao = dados.funcao
    if dados.ativo is not None:
        profissional.ativo = dados.ativo
    if dados.hora_inicio is not None:
        profissional.hora_inicio = dados.hora_inicio
    if dados.hora_fim is not None:
        profissional.hora_fim = dados.hora_fim
        
    if dados.servicos_ids is not None:
        servicos = db.query(Servicos).filter(Servicos.id.in_(dados.servicos_ids), Servicos.empresa_id == empresa.id).all()
        profissional.servicos = servicos
        
    db.commit()
    db.refresh(profissional)
    return {"msg": "Profissional atualizado com sucesso"}

@servicos_router.delete("/profissionais/{id}")
async def deletar_profissional(
    id: int,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):
    profissional = db.query(Profissional).filter(Profissional.id == id, Profissional.empresa_id == empresa.id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    
    db.delete(profissional)
    db.commit()
    return {"msg": "Profissional deletado com sucesso"}


