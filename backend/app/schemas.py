from pydantic import BaseModel,field_validator
from datetime import date, time
from enum import Enum


class StatusAgendamento(str, Enum):
    confirmado = "confirmado"
    cancelado = "cancelado"
    concluido = "concluido"


class TipoServico(str, Enum):
    corte_cabelo = "corte_cabelo"
    barba = "barba"
    manicure = "manicure"
    maquiagem = "maquiagem"

class EmpresaCreate(BaseModel):
    nome: str
    cnpj: str
    email: str
    telefone: str
    horario_inicio: time
    horario_fim: time
    dias_atendimento: str
    ramo_empresa: str

class AgendamentoCreate(BaseModel):
    nome: str
    telefone: str
    data_servico: date
    hora_inicio: time
    hora_fim: time
    tipos_servico: TipoServico
    #id_empresa: int

    @field_validator("hora_inicio", "hora_fim")
    @classmethod
    def remover_timezone(cls, v: time):
        if v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v


class AgendamentoResponse(BaseModel):
    id: int
    status: StatusAgendamento
    mensagem: str

    class Config:
        orm_mode = True