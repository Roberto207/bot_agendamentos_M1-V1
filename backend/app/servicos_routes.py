from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .dependencies import get_db, verificar_api_key, verificar_acesso_empresa, update_model_strict
from datetime import date, time
from .models import Servicos, Empresa, Profissional
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
    
    servico_atualizado = update_model_strict(db=db, model_instance=servico, update_schema=dados)
    return servico_atualizado

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
    
    # servicos_ids é um campo de relacionamento, tratar separadamente
    if dados.servicos_ids is not None:
        servicos = db.query(Servicos).filter(Servicos.id.in_(dados.servicos_ids), Servicos.empresa_id == empresa.id).all()
        profissional.servicos = servicos
    
    profissional_atualizado = update_model_strict(db=db, model_instance=profissional, update_schema=dados)
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


# ====================================================================
# ROTAS VIA TOKEN JWT (para usuários vinculados à empresa)
# Mesmas operações, mas autenticadas via token + verificar_acesso_empresa
# ====================================================================

@servicos_router.post("/t/{empresa_id}/cadastrar_servicos")
async def criar_servico_token(
    servico: ServicoSchema,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    empresa = acesso["empresa"]
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

@servicos_router.put("/t/{empresa_id}/servico/{id}")
async def atualizar_servico_token(
    id: int,
    dados: ServicoUpdate,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    empresa = acesso["empresa"]
    servico = db.query(Servicos).filter(Servicos.id == id, Servicos.empresa_id == empresa.id).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    servico_atualizado = update_model_strict(db=db, model_instance=servico, update_schema=dados)
    return servico_atualizado

@servicos_router.delete("/t/{empresa_id}/servico/{id}")
async def deletar_servico_token(
    id: int,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    empresa = acesso["empresa"]
    servico = db.query(Servicos).filter(Servicos.id == id, Servicos.empresa_id == empresa.id).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    db.delete(servico)
    db.commit()
    return {"msg": "Serviço deletado com sucesso"}

@servicos_router.post("/t/{empresa_id}/cadastrar_profissionais")
async def criar_profissional_token(
    dados: ProfissionalCreate,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    empresa = acesso["empresa"]
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

@servicos_router.put("/t/{empresa_id}/profissional/{id}")
async def atualizar_profissional_token(
    id: int,
    dados: ProfissionalUpdate,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    empresa = acesso["empresa"]
    profissional = db.query(Profissional).filter(Profissional.id == id, Profissional.empresa_id == empresa.id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    
    # servicos_ids é um campo de relacionamento, tratar separadamente
    if dados.servicos_ids is not None:
        servicos = db.query(Servicos).filter(Servicos.id.in_(dados.servicos_ids), Servicos.empresa_id == empresa.id).all()
        profissional.servicos = servicos
    
    profissional_atualizado = update_model_strict(db=db, model_instance=profissional, update_schema=dados)
    return {"msg": "Profissional atualizado com sucesso"}

@servicos_router.delete("/t/{empresa_id}/profissional/{id}")
async def deletar_profissional_token(
    id: int,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    empresa = acesso["empresa"]
    profissional = db.query(Profissional).filter(Profissional.id == id, Profissional.empresa_id == empresa.id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    db.delete(profissional)
    db.commit()
    return {"msg": "Profissional deletado com sucesso"}

@servicos_router.get("/t/{empresa_id}/listar_servicos_profissionais")
async def listar_servicos_profissionais_token(
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    empresa = acesso["empresa"]
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

