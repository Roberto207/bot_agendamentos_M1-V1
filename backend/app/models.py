from sqlalchemy import Column, Integer, String, Date, Time, Enum, TIMESTAMP
from .database import Base
import enum
from sqlalchemy.sql import func


Base = Base
class StatusAgendamento(str, enum.Enum):
    confirmado = "confirmado"
    cancelado = "cancelado"
    concluido = "concluido"

class TipoServico(str, enum.Enum):
    corte_cabelo = "corte_cabelo"
    barba = "barba"
    manicure = "manicure"
    maquiagem = "maquiagem"

class Agendamento(Base):
    __tablename__ = "agendamentos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=True)
    telefone = Column(String(20), nullable=False)
    data_servico = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fim = Column(Time, nullable=False)
    status = Column(Enum(StatusAgendamento), default="confirmado", nullable=False)
    tipos_servico = Column(Enum(TipoServico), nullable=True)
    criado_em = Column(TIMESTAMP, server_default=func.now(), nullable=False)