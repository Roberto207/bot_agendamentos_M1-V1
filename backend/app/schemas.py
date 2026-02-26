from pydantic import BaseModel
from datetime import date, time
from .models import StatusAgendamento, TipoServico

class AgendamentoCreate(BaseModel):
    nome: str
    telefone: str
    data_servico: date
    hora_inicio: time
    hora_fim: time
    tipos_servico: TipoServico

class AgendamentoResponse(BaseModel):
    id: int
    status: StatusAgendamento
    mensagem: str

    class Config:
        orm_mode = True