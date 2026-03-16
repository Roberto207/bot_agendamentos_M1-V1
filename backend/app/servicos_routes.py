from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .dependencies import get_db, verificar_acesso_empresa, update_model_strict
from datetime import date, time
from .models import Servicos, Empresa, Profissional, HorarioProfissional, HorarioFuncionamento
from .schemas import (
    ServicoSchema, ServicoUpdate, ProfissionalCreate, ProfissionalUpdate,
    ServicosOut, ProfissionalOut, HorarioOut, DiasAtendimento
)

servicos_router = APIRouter(prefix='/servicos', tags=['Serviços'])


# ====================================================================
# TODAS AS ROTAS USAM TOKEN JWT + verificar_acesso_empresa
# ====================================================================

@servicos_router.post("/{empresa_id}/cadastrar_servicos")
async def criar_servico(
    servico: ServicoSchema,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    """
    Cria um novo serviço para a empresa.
    Valida se os IDs dos profissionais informados pertencem à empresa.
    """
    empresa = acesso["empresa"]
    for id in servico.profissionais_ids:
        profissional = db.query(Profissional).filter(Profissional.id == id, Profissional.empresa_id == empresa.id).first()
        if not profissional:
            raise HTTPException(status_code=404, detail="Profissional não encontrado")
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
    return {"msg": "Serviço criado com sucesso", "id": novo.id, "nome": novo.nome,
    "preco:":novo.preco,"duracao":novo.duracao,"descricao":novo.descricao,"tempo_buffer":novo.tempo_buffer,"profissionais_nomes": [db.query(Profissional).filter(Profissional.id == id).first().nome for id in servico.profissionais_ids]}


@servicos_router.put("/{empresa_id}/servico/{id}")
async def atualizar_servico(
    id: int,
    dados: ServicoUpdate,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    """
    Atualiza dados de um serviço existente (nome, preço, duração, etc).
    Utiliza update_model_strict para atualizações parciais.
    """
    empresa = acesso["empresa"]
    servico = db.query(Servicos).filter(Servicos.id == id, Servicos.empresa_id == empresa.id).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    servico_atualizado = update_model_strict(db=db, model_instance=servico, update_schema=dados)
    return servico_atualizado


@servicos_router.delete("/{empresa_id}/servico/{id}")
async def deletar_servico(
    id: int,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    """
    Remove um serviço do banco de dados.
    """
    empresa = acesso["empresa"]
    servico = db.query(Servicos).filter(Servicos.id == id, Servicos.empresa_id == empresa.id).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    db.delete(servico)
    db.commit()
    return {"msg": "Serviço deletado com sucesso"}


@servicos_router.post("/{empresa_id}/cadastrar_profissionais")
async def criar_profissional(
    dados: ProfissionalCreate,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    """
    Cadastra um novo profissional vinculado à empresa.
    Se informados, valida e cadastra os horários de trabalho do profissional,
    garantindo que estejam dentro do horário de funcionamento da empresa.
    """
    empresa = acesso["empresa"]

    novo = Profissional(
        nome=dados.nome,
        empresa_id=empresa.id,
        funcao=dados.funcao,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)

    # Adicionar horários por dia da semana (se enviados)
    if dados.horarios:
        # Buscar horários da empresa para validar
        horarios_empresa = {
            h.dia_semana.value: h for h in db.query(HorarioFuncionamento).filter(
                HorarioFuncionamento.empresa_id == empresa.id
            ).all()
        }

        for horario in dados.horarios:
            # Validar que o dia existe na empresa
            h_empresa = horarios_empresa.get(horario.dia_semana.value)
            if not h_empresa:
                raise HTTPException(
                    400,
                    detail=f"A empresa não funciona no dia '{horario.dia_semana.value}'. Horário ignorado."
                )
            # Validar que o horário do profissional está dentro do horário da empresa
            if horario.horario_inicio < h_empresa.horario_inicio or horario.horario_fim > h_empresa.horario_fim:
                raise HTTPException(
                    400,
                    detail=f"Horário do profissional no dia '{horario.dia_semana.value}' "
                           f"({horario.horario_inicio}-{horario.horario_fim}) está fora do "
                           f"horário da empresa ({h_empresa.horario_inicio}-{h_empresa.horario_fim})"
                )

            novo_horario = HorarioProfissional(
                profissional_id=novo.id,
                dia_semana=horario.dia_semana,
                horario_inicio=horario.horario_inicio,
                horario_fim=horario.horario_fim
            )
            db.add(novo_horario)

        db.commit()
        db.refresh(novo)

    return {"msg": "Profissional cadastrado com sucesso", "id": novo.id, "nome": novo.nome}


@servicos_router.put("/{empresa_id}/profissional/{id}")
async def atualizar_profissional(
    id: int,
    dados: ProfissionalUpdate,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    empresa = acesso["empresa"]
    profissional = db.query(Profissional).filter(
        Profissional.id == id, Profissional.empresa_id == empresa.id
    ).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    
    # Tratar servicos_ids separadamente (campo de relacionamento)
    if dados.servicos_ids is not None:
        servicos = db.query(Servicos).filter(
            Servicos.id.in_(dados.servicos_ids), Servicos.empresa_id == empresa.id
        ).all()
        profissional.servicos = servicos

    # Tratar horários separadamente (substituir todos)
    if dados.horarios is not None:
        # Remover horários antigos
        db.query(HorarioProfissional).filter(
            HorarioProfissional.profissional_id == profissional.id
        ).delete()

        # Buscar horários da empresa para validar
        horarios_empresa = {
            h.dia_semana.value: h for h in db.query(HorarioFuncionamento).filter(
                HorarioFuncionamento.empresa_id == empresa.id
            ).all()
        }

        for horario in dados.horarios:
            h_empresa = horarios_empresa.get(horario.dia_semana.value)
            if not h_empresa:
                raise HTTPException(
                    400,
                    detail=f"A empresa não funciona no dia '{horario.dia_semana.value}'"
                )
            if horario.horario_inicio < h_empresa.horario_inicio or horario.horario_fim > h_empresa.horario_fim:
                raise HTTPException(
                    400,
                    detail=f"Horário no dia '{horario.dia_semana.value}' "
                           f"({horario.horario_inicio}-{horario.horario_fim}) fora do "
                           f"horário da empresa ({h_empresa.horario_inicio}-{h_empresa.horario_fim})"
                )

            novo_horario = HorarioProfissional(
                profissional_id=profissional.id,
                dia_semana=horario.dia_semana,
                horario_inicio=horario.horario_inicio,
                horario_fim=horario.horario_fim
            )
            db.add(novo_horario)

    # Atualizar campos simples (nome, funcao, ativo) via update_model_strict
    profissional_atualizado = update_model_strict(
        db=db, 
        model_instance=profissional, 
        update_schema=dados,
        exclude_fields=["servicos_ids", "horarios"]
    )
    return {"msg": "Profissional atualizado com sucesso"}


@servicos_router.delete("/{empresa_id}/profissional/{id}")
async def deletar_profissional(
    id: int,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    empresa = acesso["empresa"]
    profissional = db.query(Profissional).filter(
        Profissional.id == id, Profissional.empresa_id == empresa.id
    ).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    db.delete(profissional)
    db.commit()
    return {"msg": "Profissional deletado com sucesso"}


@servicos_router.post("/{empresa_id}/{servico_id}/ligar_profissionais_servicos")
async def adicionar_profissionais(
    servico_id: int,
    profissionais_ids: list[int],
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    """
    Estabelece o vínculo entre um serviço e vários profissionais (Many-to-Many).
    """
    empresa = acesso["empresa"]
    servico = db.query(Servicos).filter(
        Servicos.id == servico_id, Servicos.empresa_id == empresa.id
    ).first()
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    profissionais = db.query(Profissional).filter(
        Profissional.id.in_(profissionais_ids), Profissional.empresa_id == empresa.id
    ).all()

    servico.profissionais.extend(profissionais)
    db.commit()
    return {"msg": "Profissionais vinculados"}


@servicos_router.get("/{empresa_id}/listar_servicos_profissionais")
async def listar_servicos_profissionais(
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    empresa = acesso["empresa"]
    servicos = db.query(Servicos).filter(
        Servicos.empresa_id == empresa.id, Servicos.ativo == True
    ).all()
    
    resultado = []
    for servico in servicos:
        profissionais = [
            {"id": prof.id, "nome": prof.nome, "funcao": prof.funcao}
            for prof in servico.profissionais if prof.ativo
        ]
        resultado.append({
            "id": servico.id,
            "nome": servico.nome,
            "descricao": servico.descricao,
            "duracao": servico.duracao,
            "preco": servico.preco,
            "profissionais": profissionais
        })
    return resultado
