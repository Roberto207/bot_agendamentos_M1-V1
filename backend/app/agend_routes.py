#configurar esse arquivo com as rotas de agendamento que estao no main.py
from fastapi import FastAPI, Depends, HTTPException, Header, Security,APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import SessionLocal
from .schemas import AgendamentoCreate,StatusAgendamento,DiasAtendimento
from .models import Agendamento,Empresa,HorarioFuncionamento,Servicos,Cliente,Profissional
from .dependencies import get_db, verificar_api_key, verificar_acesso_empresa
from datetime import date, datetime, time, timedelta
import os
from dotenv import load_dotenv
from typing import Optional
from sqlalchemy import func,and_
from datetime import date,datetime,time,timedelta

#variaveis importantes para validar os horarios de atendimento e a data maxima de agendamento
data_maxima_agendamento = date.today() + timedelta(days=30)
#----------------------------------------------------------------
load_dotenv()
API_KEY = os.getenv("SECRET_KEY")


agendamentos_router = APIRouter(prefix='/agendamentos', tags=['Agendamentos'])


dias_map = {
    0: DiasAtendimento.segunda,
    1: DiasAtendimento.terca,
    2: DiasAtendimento.quarta,
    3: DiasAtendimento.quinta,
    4: DiasAtendimento.sexta,
    5: DiasAtendimento.sabado,
    6: DiasAtendimento.domingo
}

# ====================================================================
# ROTAS WHATSAPP (INTEGRAÇÃO)
# ====================================================================

@agendamentos_router.post("/criar")
async def criar_agendamento_endpoint(
    agendamento: AgendamentoCreate,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):
    """
    Cria um novo agendamento via integração de WhatsApp.
    Valida horários da empresa, disponibilidade do profissional (ou seleciona um aleatório)
    e vincula ou cria o cadastro do cliente.
    """
    # --- Buscar serviço ---
    servico = db.query(Servicos).filter(
        Servicos.id == agendamento.servico_id,
        Servicos.empresa_id == empresa.id
    ).first()
    if not servico:
        raise HTTPException(404, detail="Serviço não encontrado")

    # --- Calcular hora fim e limpar microsegundos ---
    hora_inicio = agendamento.hora_inicio.replace(tzinfo=None, microsecond=0)
    hora_fim = (datetime.combine(agendamento.data_servico, hora_inicio) + timedelta(minutes=servico.duracao)).time()
    hora_fim = hora_fim.replace(microsecond=0)

    import random
    # --- Buscar profissional pelo ID informado ou escolher aleatoriamente ---
    if agendamento.profissional_id:
        profissional = db.query(Profissional).filter(
            Profissional.id == agendamento.profissional_id,
            Profissional.empresa_id == empresa.id
        ).first()
        if not profissional:
            raise HTTPException(400, detail="Profissional não existe ou não pertence à empresa")

        if profissional.hora_inicio is not None and hora_inicio < profissional.hora_inicio:
            raise HTTPException(400, detail=f"O profissional {profissional.nome} inicia o expediente às {profissional.hora_inicio}")
        if profissional.hora_fim is not None and hora_fim > profissional.hora_fim:
            raise HTTPException(400, detail=f"O profissional {profissional.nome} encerra o expediente às {profissional.hora_fim}")

        # Verifica conflito apenas para o profissional selecionado
        conflito = db.query(Agendamento).filter(
            Agendamento.profissional_id == profissional.id,
            Agendamento.data_servico == agendamento.data_servico,
            Agendamento.hora_inicio < hora_fim,
            Agendamento.hora_fim > hora_inicio,
            Agendamento.status == StatusAgendamento.confirmado
        ).first()
        if conflito:
            raise HTTPException(
                400,
                detail=f"Horário já ocupado pelo profissional {profissional.nome}"
            )
    else:
        profissionais_do_servico = servico.profissionais
        if not profissionais_do_servico:
            raise HTTPException(400, detail="Nenhum profissional cadastrado para este serviço")
        
        profissionais_disponiveis = []
        for prof in profissionais_do_servico:
            if not prof.ativo:
                continue
            
            if prof.hora_inicio is not None and hora_inicio < prof.hora_inicio:
                continue
            if prof.hora_fim is not None and hora_fim > prof.hora_fim:
                continue

            conflito = db.query(Agendamento).filter(
                Agendamento.profissional_id == prof.id,
                Agendamento.data_servico == agendamento.data_servico,
                Agendamento.hora_inicio < hora_fim,
                Agendamento.hora_fim > hora_inicio,
                Agendamento.status == StatusAgendamento.confirmado
            ).first()
            if not conflito:
                profissionais_disponiveis.append(prof)
        
        if not profissionais_disponiveis:
            raise HTTPException(400, detail="Nenhum profissional disponível para este horário")
        
        profissional = random.choice(profissionais_disponiveis)
        nome_profissional = profissional.nome

    # --- Verificar dia da semana e horário de funcionamento ---
    dia = dias_map[agendamento.data_servico.weekday()]
    horario_dia = db.query(HorarioFuncionamento).filter(
        HorarioFuncionamento.empresa_id == empresa.id,
        HorarioFuncionamento.dia_semana == dia
    ).first()
    if not horario_dia:
        raise HTTPException(400, detail="Empresa não atende nesse dia")
    if hora_inicio < horario_dia.horario_inicio or hora_fim > horario_dia.horario_fim:
        raise HTTPException(
            400,
            detail=f"Fora do horário de atendimento. Horário nesse dia é das {horario_dia.horario_inicio} às {horario_dia.horario_fim}"
        )

    # --- Validar data ---
    if agendamento.data_servico > date.today() + timedelta(days=30):
        raise HTTPException(
            400,
            detail=f"Data não pode ser maior que 30 dias. Máximo permitido: {date.today() + timedelta(days=30)}"
        )
    if agendamento.data_servico < date.today():
        raise HTTPException(
            400,
            detail=f"Data {agendamento.data_servico} não pode ser menor que hoje {date.today()}"
        )
    if agendamento.data_servico == date.today() and hora_inicio < datetime.now().time():
        raise HTTPException(
            400,
            detail=f"Horário {hora_inicio} já passou. Agora são {datetime.now().time()}"
        )

    # --- Buscar ou criar cliente ---
    cliente = db.query(Cliente).filter(Cliente.telefone == agendamento.telefone_cliente).first()
    if not cliente:
        cliente = Cliente(
            nome=agendamento.nome_cliente,
            telefone=agendamento.telefone_cliente,
            criado_em=datetime.now()
        )
        db.add(cliente)
        db.commit()
        db.refresh(cliente)

    # --- Criar agendamento ---
    novo = Agendamento(
        empresa_id=empresa.id,
        cliente_id=cliente.id,
        servico_id=servico.id,
        nome_cliente=agendamento.nome_cliente,
        telefone_cliente=agendamento.telefone_cliente,
        nome_servico=servico.nome,
        data_servico=agendamento.data_servico,
        hora_inicio=hora_inicio,
        hora_fim=hora_fim,
        profissional_id=profissional.id,
        status=StatusAgendamento.confirmado
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)

    return {"mensagem":"agendamento criado com sucesso", "agendamento_id":novo.id,
    "data_servico":novo.data_servico,
    "hora_inicio":novo.hora_inicio,
    "hora_fim":novo.hora_fim,
    "nome_profissional":profissional.nome,
    "servico":servico.nome,
    "status":novo.status} #novo




@agendamentos_router.post("/cancelar")
async def cancelar_agendamento(telefone: str, db: Session = Depends(get_db), empresa: Empresa = Depends(verificar_api_key)):
    """
    Cancela o último agendamento ativo vinculado ao número de telefone fornecido.
    """
    agendamento = db.query(Agendamento).filter(Agendamento.telefone_cliente == telefone).order_by(Agendamento.id.desc()).first()
    if not agendamento:
        raise HTTPException(status_code=400,detail="agendamento nao encontrado")
    if agendamento.status in [StatusAgendamento.concluido, StatusAgendamento.cancelado]:
        raise HTTPException(status_code=400,detail=f"agendamento ja foi cancelado ou concluido")
        # return {
        #     "agendamento": {
        #         "id": agendamento.id,
        #         "nome": agendamento.nome,
        #         "telefone": agendamento.telefone,
        #         "data_servico": agendamento.data_servico,
        #         "hora_inicio": agendamento.hora_inicio,
        #         "hora_fim": agendamento.hora_fim,
        #         "status": agendamento.status
        #     }
        # }
    else:
        agendamento.status = StatusAgendamento.cancelado
        db.commit()
        db.refresh(agendamento)
        return {
            "status:": agendamento.status,
            "mensagem:": "agendamento cancelado com sucesso"
        }
    print('bolas') 




#rota de concluir horario agendado
@agendamentos_router.post("/concluir")
async def concluir_agendamento(telefone: str, db: Session = Depends(get_db), empresa: Empresa = Depends(verificar_api_key)):
    """
    Marca o último agendamento do cliente como concluído.
    Valida se o horário do serviço já passou antes de permitir a conclusão.
    """
    agendamento = db.query(Agendamento).filter(Agendamento.telefone_cliente == telefone).order_by(Agendamento.id.desc()).first()
    if not agendamento:
        raise HTTPException(status_code=400,detail="agendamento nao encontrado")
    if agendamento.status in [StatusAgendamento.concluido, StatusAgendamento.cancelado]:
        raise HTTPException(status_code=400,detail=f"agendamento ja foi cancelado ou concluido")

    if agendamento.data_servico > date.today():
        raise HTTPException(status_code=400,detail=f"agendamento ainda nao pode ser concluido, data do serviço {agendamento.data_servico} é maior do que a data atual {date.today()}")
    
    if agendamento.data_servico == date.today() and agendamento.hora_fim > datetime.now().time():
        raise HTTPException(status_code=400,detail=f"agendamento ainda nao pode ser concluido, horario do serviço {agendamento.hora_fim} é maior do que o horario atual {datetime.now().time()}")

    else:
        agendamento.status = StatusAgendamento.concluido
        db.commit()
        db.refresh(agendamento)
        return {
            "mensagem:": "agendamento concluido com sucesso",
            "agendamento": {
                "id": agendamento.id,
                "nome_cliente": agendamento.nome_cliente,
                "telefone_cliente": agendamento.telefone_cliente,
                "data_servico": agendamento.data_servico,
                "hora_inicio": agendamento.hora_inicio,
                "hora_fim": agendamento.hora_fim,
                "status": agendamento.status
            }
        }

#rota de mostrar todos os horarios disponiveis

@agendamentos_router.get("/horarios_ocupados")
async def horarios_ocupados(
    data_servico: date,
    profissional_id: int | None = None,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):
    """
    Retorna a lista de horários já reservados para uma determinada data.
    Pode filtrar por um profissional específico ou retornar o status de todos.
    """
    query = db.query(Agendamento).filter(
        Agendamento.empresa_id == empresa.id,
        Agendamento.data_servico == data_servico,
        Agendamento.status == StatusAgendamento.confirmado
    )

    if profissional_id:
        # Filtra apenas um profissional específico
        query = query.filter(Agendamento.profissional_id == profissional_id)
        agendamentos = query.order_by(Agendamento.hora_inicio).all()

        horarios = []
        for ag in agendamentos:
            horarios.append({
                "hora_inicio": ag.hora_inicio.strftime("%H:%M"),
                "hora_fim": ag.hora_fim.strftime("%H:%M"),
                "profissional": ag.profissional.nome if ag.profissional else "Não atribuído",
                "cliente": ag.nome_cliente,
                "servico": ag.nome_servico
            })

        return {
            "data_servico": data_servico,
            "profissional_id": profissional_id,
            "horarios_ocupados": horarios
        }
    else:
        # Retorna todos os horários ocupados agrupados por profissional da empresa
        profissionais = db.query(Profissional).filter(
            Profissional.empresa_id == empresa.id,
            Profissional.ativo == True
        ).all()
        
        agendamentos = query.order_by(Agendamento.hora_inicio).all()
        
        resultado_profissionais = []
        for prof in profissionais:
            # Pega os agendamentos apenas desse profissional
            agends_prof = [ag for ag in agendamentos if ag.profissional_id == prof.id]
            horarios_prof = []
            for ag in agends_prof:
                horarios_prof.append({
                    "hora_inicio": ag.hora_inicio.strftime("%H:%M"),
                    "hora_fim": ag.hora_fim.strftime("%H:%M"),
                    "cliente": ag.nome_cliente,
                    "servico": ag.nome_servico
                })
            
            resultado_profissionais.append({
                "profissional_id": prof.id,
                "profissional_nome": prof.nome,
                "horarios_ocupados": horarios_prof
            })
            
        return {
            "data_servico": data_servico,
            "profissionais": resultado_profissionais
        }




@agendamentos_router.get("/seus_agendamentos")
async def seus_agendamentos(telefone: str, db: Session = Depends(get_db), empresa: Empresa = Depends(verificar_api_key)):
    """
    Retorna os últimos 5 agendamentos realizados pelo cliente (identificado pelo telefone).
    """
    agendamentos = db.query(Agendamento).filter(Agendamento.telefone_cliente == telefone, Agendamento.empresa_id == empresa.id).order_by(Agendamento.data_servico.desc(), Agendamento.hora_inicio.desc()).limit(5).all()
    return {
        "agendamentos": [
            {
                "id": agendamento.id,
                "nome_cliente": agendamento.nome_cliente,
                "telefone_cliente": agendamento.telefone_cliente,
                "data_servico": agendamento.data_servico,
                "hora_inicio": agendamento.hora_inicio,
                "hora_fim": agendamento.hora_fim,
                "status": agendamento.status,
                "servico": agendamento.nome_servico
            }
            for agendamento in agendamentos
        ]
    }

# ====================================================================
# ROTAS ADMIN (GERENCIAMENTO)
# ====================================================================

@agendamentos_router.get("/empresa/{empresa_id}/listar")
async def listar_agendamentos_admin(
    empresa_id: int,
    data: Optional[date] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    profissional_id: Optional[int] = None,
    db: Session = Depends(get_db),
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1))
):
    """
    Lista agendamentos de uma empresa com filtros para administração.
    Nível mínimo: colaborador (1).
    """
    query = db.query(Agendamento).filter(Agendamento.empresa_id == empresa_id)
    
    if data:
        query = query.filter(Agendamento.data_servico == data)
    
    if data_inicio:
        query = query.filter(Agendamento.data_servico >= data_inicio)
    
    if data_fim:
        query = query.filter(Agendamento.data_servico <= data_fim)
    
    if profissional_id:
        query = query.filter(Agendamento.profissional_id == profissional_id)
        
    agendamentos = query.order_by(Agendamento.data_servico.desc(), Agendamento.hora_inicio.desc()).all()
    
    return [
        {
            "id": a.id,
            "nome_cliente": a.nome_cliente,
            "telefone_cliente": a.telefone_cliente,
            "data_servico": a.data_servico,
            "hora_inicio": a.hora_inicio.strftime("%H:%M") if a.hora_inicio else None,
            "hora_fim": a.hora_fim.strftime("%H:%M") if a.hora_fim else None,
            "status": a.status,
            "servico": a.nome_servico,
            "profissional": a.profissional.nome if a.profissional else "Não atribuído"
        }
        for a in agendamentos
    ]

@agendamentos_router.post("/empresa/{empresa_id}/{agendamento_id}/cancelar_admin")
async def cancelar_agendamento_admin(
    empresa_id: int,
    agendamento_id: int,
    db: Session = Depends(get_db),
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1))
):
    """
    Cancela um agendamento via painel administrativo.
    """
    agendamento = db.query(Agendamento).filter(
        Agendamento.id == agendamento_id,
        Agendamento.empresa_id == empresa_id
    ).first()
    
    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
        
    agendamento.status = StatusAgendamento.cancelado
    db.commit()
    return {"msg": "Agendamento cancelado com sucesso"}

@agendamentos_router.post("/empresa/{empresa_id}/{agendamento_id}/concluir_admin")
async def concluir_agendamento_admin(
    empresa_id: int,
    agendamento_id: int,
    db: Session = Depends(get_db),
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1))
):
    """
    Conclui um agendamento via painel administrativo.
    """
    agendamento = db.query(Agendamento).filter(
        Agendamento.id == agendamento_id,
        Agendamento.empresa_id == empresa_id
    ).first()
    
    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
        
    agendamento.status = StatusAgendamento.concluido
    db.commit()
    return {"msg": "Agendamento concluído com sucesso"}
