from pydantic import BaseModel,field_validator
from datetime import date, time,datetime
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




class ServicoSchema(BaseModel):
    nome: str
    descricao: str | None = None
    duracao: int
    tempo_buffer: int = 0
    preco: float
    profissionais_ids: List[int]

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
    endereco_empresa: Optional[str] = None
    horarios: List[HorarioFuncionamentoCreate]
    

class AgendamentoCreate(BaseModel):
    nome_cliente: str
    telefone_cliente: str
    data_servico: date
    hora_inicio: time
    nome_servico: str
    profissional_id: Optional[int] = None
    servico_id: int
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
    criado_em : Optional[date] = None

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

class EmpresaUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    ramo_empresa: Optional[str] = None
    endereco_empresa: Optional[str] = None


class EmpresaOut(BaseModel):
    id: int
    nome: str
    telefone: str | None
    ramo_empresa: str | None
    endereco_empresa: str | None
    criado_em: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Permite converter SQLAlchemy -> Pydantic

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    senha: Optional[str] = None

class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str
    telefone: str
    ativo: bool
    criado_em: Optional[datetime] = None

    class Config:
        from_attributes = True

class ServicoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    duracao: Optional[int] = None
    tempo_buffer: Optional[int] = None
    preco: Optional[float] = None
    ativo: Optional[bool] = None

class ProfissionalCreate(BaseModel):
    nome: str
    funcao: str
    hora_inicio: Optional[time] = None
    hora_fim: Optional[time] = None

class ProfissionalUpdate(BaseModel):
    nome: Optional[str] = None
    funcao: Optional[str] = None
    ativo: Optional[bool] = None
    hora_inicio: Optional[time] = None
    hora_fim: Optional[time] = None
    servicos_ids: Optional[List[int]] = None