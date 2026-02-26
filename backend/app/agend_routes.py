#configurar esse arquivo com as rotas de agendamento que estao no main.py
from fastapi import FastAPI, Depends, HTTPException, Header, Security,APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import SessionLocal
from .crud import criar_agendamento,get_db,verificar_api_key
from .schemas import AgendamentoCreate
from .models import Agendamento,StatusAgendamento
import os
from dotenv import load_dotenv
from sqlalchemy import func
from datetime import date

load_dotenv()
API_KEY = os.getenv("SECRET_KEY")

agendamentos_router = APIRouter(prefix='/agendamentos',tags=['Agendamentos'],dependencies=[Depends(verificar_api_key)])
#@agendamentos_router.get('/')

# Endpoint para criar agendamento
@agendamentos_router.post("/criar_agendamento")
async def criar_agendamento_endpoint(
    agendamento: AgendamentoCreate,
    db: Session = Depends(get_db)
):
    if agendamento.data_servico < date.today():
        raise HTTPException(status_code=400, detail=f"Data do serviço {agendamento.data_servico} nao pode ser menor do que a data atual {date.today()}")
    
    return criar_agendamento(db, agendamento)

@agendamentos_router.post("/cancelar_agendamento")
async def cancelar_agendamento(telefone: str,db: Session = Depends(get_db)): #,_: None = Depends(verificar_api_key)
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
        return {
            "mensagem:": "agendamento cancelado com sucesso",
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
    print('bolas') 
#rota de concluir horario agendado
@agendamentos_router.post("/concluir_agendamento")
async def concluir_agendamento(telefone: str,db: Session = Depends(get_db)):
    agendamento = db.query(Agendamento).filter(Agendamento.telefone == telefone).order_by(Agendamento.id.desc()).first()
    if not agendamento:
        raise HTTPException(status_code=400,detail="agendamento nao encontrado")
    if agendamento.status in [StatusAgendamento.concluido, StatusAgendamento.cancelado]:
        raise HTTPException(status_code=400,detail=f"agendamento ja foi cancelado ou concluido")
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
