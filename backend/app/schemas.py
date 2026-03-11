from pydantic import BaseModel,field_validator
from datetime import date, time
from enum import Enum
from typing import List


class StatusAgendamento(str, Enum):
    confirmado = "confirmado"
    cancelado = "cancelado"
    concluido = "concluido"

import enum

class DiasAtendimento(str, enum.Enum):
    segunda = "segunda"
    terca = "terca"
    quarta = "quarta"
    quinta = "quinta"
    sexta = "sexta"
    sabado = "sabado"
    domingo = "domingo"

class Origem_Cliente(str, Enum):
    whatsapp = "WhatsApp"
    site = "Site"

class TipoServico(str, Enum):
    corte_cabelo = "corte_cabelo"
    barba = "barba"
    manicure = "manicure"
    maquiagem = "maquiagem"

class HorarioFuncionamentoCreate(BaseModel):
    dia_semana: DiasAtendimento
    horario_inicio: time
    horario_fim: time

class EmpresaCreate(BaseModel):
    nome: str
    cnpj: str
    email: str
    telefone: str
    ramo_empresa: str
    horarios: List[HorarioFuncionamentoCreate]
    

class AgendamentoCreate(BaseModel):
    nome_cliente: str
    telefone_cliente: str
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

class Cliente_Create(BaseModel):
    nome : str
    telefone : str
    senha : str
    email : str
    admin : bool = False
    ativo : bool = True