#configurar esse arquivo com as rotas de agendamento que estao no main.py
from fastapi import FastAPI, Depends, HTTPException, Header, Security,APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import SessionLocal
from .dependencies import get_db,verificar_api_key
from .schemas import AgendamentoCreate,StatusAgendamento,DiasAtendimento
from .models import Agendamento,Empresa,HorarioFuncionamento,Servicos,Cliente
from datetime import date, datetime, time, timedelta
import os
from dotenv import load_dotenv
from sqlalchemy import func
from datetime import date,datetime,time,timedelta

#variaveis importantes para validar os horarios de atendimento e a data maxima de agendamento
data_maxima_agendamento = date.today() + timedelta(days=30)
#----------------------------------------------------------------
load_dotenv()
API_KEY = os.getenv("SECRET_KEY")


agendamentos_router = APIRouter(prefix='/agendamentos_whatssap',tags=['Agendamentos_Whatssap'])


dias_map = {
    0: DiasAtendimento.segunda,
    1: DiasAtendimento.terca,
    2: DiasAtendimento.quarta,
    3: DiasAtendimento.quinta,
    4: DiasAtendimento.sexta,
    5: DiasAtendimento.sabado,
    6: DiasAtendimento.domingo
}

@agendamentos_router.post("/criar_agendamento")
async def criar_agendamento_endpoint(
    agendamento: AgendamentoCreate,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):

    # buscar serviço
    servico = db.query(Servicos).filter(
        Servicos.nome == agendamento.nome_servico,
        Servicos.empresa_id == empresa.id
    ).first()

    if not servico:
        raise HTTPException(404, "Serviço não encontrado")

    hora_inicio = agendamento.hora_inicio

    # calcular hora fim
    hora_fim = (
        datetime.combine(agendamento.data_servico, hora_inicio) +
        timedelta(minutes=servico.duracao)
    ).time()

    # remover timezone se existir
    if hora_inicio.tzinfo:
        hora_inicio = hora_inicio.replace(tzinfo=None)

    if hora_fim.tzinfo:
        hora_fim = hora_fim.replace(tzinfo=None)


    conflito = db.query(Agendamento).filter(
        Agendamento.empresa_id == empresa.id,
        Agendamento.data_servico == agendamento.data_servico,
        Agendamento.hora_inicio < hora_fim,
        Agendamento.hora_fim > hora_inicio
    ).first()

    if conflito:
        raise HTTPException(400, "Horário já ocupado")


    # verificar dia da semana
    dia = dias_map[agendamento.data_servico.weekday()]

    horario_dia = db.query(HorarioFuncionamento).filter(
        HorarioFuncionamento.empresa_id == empresa.id,
        HorarioFuncionamento.dia_semana == dia
    ).first()

    if not horario_dia:
        raise HTTPException(400, "Empresa não atende nesse dia")

    # verificar horario de funcionamento
    if hora_inicio < horario_dia.horario_inicio or hora_fim > horario_dia.horario_fim:
        raise HTTPException(
            400,
            f"Fora do horário de atendimento. Horário nesse dia é das {horario_dia.horario_inicio} às {horario_dia.horario_fim}"
        )

    # validações de data
    if agendamento.data_servico > date.today() + timedelta(days=30):
        raise HTTPException(
            400,
            f"Data não pode ser maior que 30 dias. Máximo permitido: {date.today() + timedelta(days=30)}"
        )

    if agendamento.data_servico < date.today():
        raise HTTPException(
            400,
            f"Data {agendamento.data_servico} não pode ser menor que hoje {date.today()}"
        )

    if agendamento.data_servico == date.today() and hora_inicio < datetime.now().time():
        raise HTTPException(
            400,
            f"Horário {hora_inicio} já passou. Agora são {datetime.now().time()}"
        )

    # buscar cliente
    cliente = db.query(Cliente).filter(
        Cliente.telefone == agendamento.telefone_cliente
    ).first()

    # criar cliente se não existir
    if not cliente:
        cliente = Cliente(
            nome=agendamento.nome_cliente,
            telefone=agendamento.telefone_cliente,
            criado_em=datetime.now()
        )

        db.add(cliente)
        db.commit()
        db.refresh(cliente)

    # criar agendamento
    novo = Agendamento(
        empresa_id=empresa.id,
        nome_cliente=agendamento.nome_cliente,
        telefone_cliente=agendamento.telefone_cliente,
        data_servico=agendamento.data_servico,
        hora_inicio=hora_inicio,
        hora_fim=hora_fim,
        cliente_id=cliente.id,
        servico_id=servico.id,
        nome_servico=agendamento.nome_servico
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    return novo




@agendamentos_router.post("/cancelar_agendamento")
async def cancelar_agendamento(telefone: str,db: Session = Depends(get_db),empresa: Empresa = Depends(verificar_api_key)): #,_: None = Depends(verificar_api_key)
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
@agendamentos_router.post("/concluir_agendamento")
async def concluir_agendamento(telefone: str,db: Session = Depends(get_db),empresa: Empresa = Depends(verificar_api_key)):
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

@agendamentos_router.get("/horarios_disponiveis")
async def horarios_disponiveis(
    data_servico: date,
    nome_servico: str,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):

    dia = dias_map[data_servico.weekday()]

    horario_dia = db.query(HorarioFuncionamento).filter(
        HorarioFuncionamento.empresa_id == empresa.id,
        HorarioFuncionamento.dia_semana == dia
    ).first()

    if not horario_dia:
        raise HTTPException(400, "Empresa não atende nesse dia")

    servico = db.query(Servicos).filter(
        Servicos.nome == nome_servico,
        Servicos.empresa_id == empresa.id
    ).first()

    if not servico:
        raise HTTPException(404, "Serviço não encontrado")

    duracao = servico.duracao

    inicio = datetime.combine(data_servico, horario_dia.horario_inicio)
    fim = datetime.combine(data_servico, horario_dia.horario_fim)

    horarios_ocupados = db.query(
        Agendamento.hora_inicio,
        Agendamento.hora_fim
    ).filter(
        Agendamento.data_servico == data_servico,
        Agendamento.status == StatusAgendamento.confirmado,
        Agendamento.empresa_id == empresa.id
    ).all()

    horarios_disponiveis = []

    atual = inicio

    while atual + timedelta(minutes=duracao) <= fim:

        hora_inicio = atual.time()
        hora_fim = (atual + timedelta(minutes=duracao)).time()

        conflito = any(
            hora_inicio < ocupado[1] and hora_fim > ocupado[0]
            for ocupado in horarios_ocupados
        )

        if not conflito:
            horarios_disponiveis.append({
                "hora_inicio": hora_inicio.strftime("%H:%M"),
                "hora_fim": hora_fim.strftime("%H:%M")
            })

        atual += timedelta(minutes=duracao)

    return {
        "data_servico": data_servico,
        "duracao_servico": duracao,
        "horarios_disponiveis": horarios_disponiveis
    }



@agendamentos_router.get("/seus_agendamentos")
async def seus_agendamentos(telefone: str, db: Session = Depends(get_db),empresa: Empresa = Depends(verificar_api_key)):
    agendamentos = db.query(Agendamento).filter(Agendamento.telefone_cliente == telefone, Agendamento.empresa_id == empresa.id).order_by(Agendamento.data_servico.desc(), Agendamento.hora_inicio.desc()).limit(5).all()
    return {
        "agendamentos": [
            {
                "id": agendamento.id,
                "nome_cliente": agendamento.nome_cliente,
                "telefone_cliente": agendamento.telefone_cliente,
                "tipo_servico": agendamento.tipos_servico,
                "data_servico": agendamento.data_servico,
                "hora_inicio": agendamento.hora_inicio,
                "hora_fim": agendamento.hora_fim,
                "status": agendamento.status,
                "servico": agendamento.nome_servico
            }
            for agendamento in agendamentos
        ]
    }

