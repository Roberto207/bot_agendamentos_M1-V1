from sqlalchemy import Column, Integer, String, Date, Time, Enum, TIMESTAMP,ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import enum
from sqlalchemy.sql import func
from .schemas import StatusAgendamento,TipoServico


Base = Base

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    cnpj = Column(String(20), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    telefone = Column(String(20), nullable=False)
    horario_inicio = Column(Time(timezone=False), nullable=False)
    horario_fim = Column(Time(timezone=False), nullable=False)
    dias_atendimento = Column(String(255), nullable=False)  # Ex: "Segunda a Sexta"
    ramo_empresa = Column(String(255), nullable=False)  # Ex: "Barbearia", "Salão de Beleza"
    agendamentos = relationship("Agendamento", back_populates="empresa")

class Agendamento(Base):
    __tablename__ = "agendamentos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column('empresa_id',ForeignKey('empresas.id'), nullable=False)
    nome = Column(String(255), nullable=True)
    telefone = Column(String(20), nullable=False)
    data_servico = Column(Date, nullable=False)
    hora_inicio = Column(Time(timezone=False), nullable=False)
    hora_fim = Column(Time(timezone=False), nullable=False)
    status = Column(Enum(StatusAgendamento), default="confirmado", nullable=False)
    tipos_servico = Column(Enum(TipoServico), nullable=True)
    criado_em = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    empresa = relationship("Empresa", back_populates="agendamentos")