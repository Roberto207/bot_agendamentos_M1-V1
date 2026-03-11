#configurar esse arquivo com as rotas de agendamento que estao no main.py
from fastapi import FastAPI, Depends, HTTPException, Header, Security,APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import SessionLocal
from .dependencies import criar_agendamento,get_db,verificar_api_key
from .schemas import AgendamentoCreate,StatusAgendamento
from .models import Agendamento,Empresa
import os
from dotenv import load_dotenv
from sqlalchemy import func
from datetime import date,datetime,time,timedelta

#variaveis importantes para validar os horarios de atendimento e a data maxima de agendamento
#inicio_atendimento = empresa.horario_inicio().time()
#fim_atendimento = empresa.horario_fim().time()
# inicio_atendimento = datetime.strptime("08:00", "%H:%M").time()
# fim_atendimento = datetime.strptime("18:00", "%H:%M").time()
data_maxima_agendamento = date.today() + timedelta(days=30)
#----------------------------------------------------------------


load_dotenv()
API_KEY = os.getenv("SECRET_KEY")

agendamentos_router = APIRouter(prefix='/agendamentos',tags=['Agendamentos'])
#@agendamentos_router.get('/')


# Endpoint para criar agendamento
@agendamentos_router.post("/criar_agendamento")
async def criar_agendamento_endpoint(
    agendamento: AgendamentoCreate,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):
    inicio_atendimento = empresa.horario_inicio
    fim_atendimento = empresa.horario_fim

    hora_inicio = agendamento.hora_inicio
    hora_fim = agendamento.hora_fim

    # remover timezone se existir
    if inicio_atendimento.tzinfo:
        inicio_atendimento = inicio_atendimento.replace(tzinfo=None)

    if fim_atendimento.tzinfo:
        fim_atendimento = fim_atendimento.replace(tzinfo=None)

    if hora_inicio.tzinfo:
        hora_inicio = hora_inicio.replace(tzinfo=None)

    if hora_fim.tzinfo:
        hora_fim = hora_fim.replace(tzinfo=None)

    if agendamento.hora_inicio < inicio_atendimento or agendamento.hora_fim > fim_atendimento:
        raise HTTPException(
            status_code=400,
            detail=f"Horario de atendimento é das {inicio_atendimento} às {fim_atendimento}"
        )

    if agendamento.data_servico > data_maxima_agendamento:
        raise HTTPException(status_code=400, detail=f"Data do serviço {agendamento.data_servico} nao pode ser maior do que 30 dias a partir da data atual {date.today()}, data máxima permitida é {date.today() + timedelta(days=30)}")
    
    if agendamento.data_servico < date.today():
        raise HTTPException(status_code=400, detail=f"Data do serviço {agendamento.data_servico} nao pode ser menor do que a data atual {date.today()}")
    
    if agendamento.data_servico == date.today() and agendamento.hora_inicio < datetime.now().time():
        raise HTTPException(status_code=400, detail=f"Horario do serviço {agendamento.hora_inicio} nao pode ser menor do que o horario atual {datetime.now().time()}")
    
    

    
    
    #timedelta oq é 
    return await criar_agendamento(db, agendamento, empresa)




@agendamentos_router.post("/cancelar_agendamento")
async def cancelar_agendamento(telefone: str,db: Session = Depends(get_db),empresa: Empresa = Depends(verificar_api_key)): #,_: None = Depends(verificar_api_key)
    agendamento = db.query(Agendamento).filter(Agendamento.telefone == telefone).order_by(Agendamento.id.desc()).first()
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
    agendamento = db.query(Agendamento).filter(Agendamento.telefone == telefone).order_by(Agendamento.id.desc()).first()
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
                "nome": agendamento.nome,
                "telefone": agendamento.telefone,
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
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(verificar_api_key)
):

    inicio = empresa.horario_inicio.hour
    fim = empresa.horario_fim.hour

    horarios_ocupados = db.query(
        Agendamento.hora_inicio,
        Agendamento.hora_fim
    ).filter(
        Agendamento.data_servico == data_servico,
        Agendamento.status == StatusAgendamento.confirmado,
        Agendamento.empresa_id == empresa.id
    ).all()

    horarios_disponiveis = []

    for hora in range(inicio, fim):
        hora_inicio = time(hora, 0)
        hora_fim = time(hora + 1, 0)

        conflito = any(
            hora_inicio < ocupado[1] and hora_fim > ocupado[0]
            for ocupado in horarios_ocupados
        )

        if not conflito:
            horarios_disponiveis.append({
                "hora_inicio": hora_inicio.strftime("%H:%M"),
                "hora_fim": hora_fim.strftime("%H:%M")
            })

    return {
        "data_servico": data_servico,
        "horarios_disponiveis": horarios_disponiveis
    }



@agendamentos_router.get("/seus_agendamentos")
async def seus_agendamentos(telefone: str, db: Session = Depends(get_db),empresa: Empresa = Depends(verificar_api_key)):
    agendamentos = db.query(Agendamento).filter(Agendamento.telefone == telefone, Agendamento.empresa_id == empresa.id).order_by(Agendamento.data_servico.desc(), Agendamento.hora_inicio.desc()).limit(5).all()
    return {
        "agendamentos": [
            {
                "id": agendamento.id,
                "nome": agendamento.nome,
                "telefone": agendamento.telefone,
                "tipo_servico": agendamento.tipos_servico,
                "data_servico": agendamento.data_servico,
                "hora_inicio": agendamento.hora_inicio,
                "hora_fim": agendamento.hora_fim,
                "status": agendamento.status
            }
            for agendamento in agendamentos
        ]
    }