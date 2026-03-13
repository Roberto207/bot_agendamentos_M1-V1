from pydantic import BaseModel,field_validator
from datetime import date, time
from enum import Enum
from typing import List,Optional


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

# class Origem_Cliente(str, Enum):
#     whatsapp = "WhatsApp"
#     site = "Site"


    

class ServicoSchema(BaseModel):
    #telefone_empresa : str
    nome: str
    preco: float
    duracao: int
    descricao: Optional[str] = None
    tempo_buffer: int = 0

    class Config:
        from_attributes = True




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
    nome_servico: str
    #id_empresa: int

    @field_validator("hora_inicio")
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
        from_attributes = True

class Cliente_Create(BaseModel):
    nome : str
    telefone : str
    #senha : str
    email : Optional[str] = None
    criado_em : date

class LoginSchema(BaseModel):
    email : str
    senha : str

    class Config:
        from_attributes = True
    
class DeleteSchema(BaseModel):
    email: str

    class Config:
        from_attributes = True

class UsuarioSchema(BaseModel):
    nome: str
    email: str
    telefone: str
    senha: str
    admin: bool = False
    ativo: bool = True

    class Config:
        from_attributes = True