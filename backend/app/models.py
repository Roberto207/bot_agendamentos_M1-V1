from sqlalchemy import Column, Integer, String, Date, Time, Enum, TIMESTAMP,ForeignKey,Boolean,DECIMAL,Table
from sqlalchemy.orm import relationship
from .database import Base
import enum
from sqlalchemy.sql import func
from .schemas import StatusAgendamento,DiasAtendimento


Base = Base

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True,autoincrement=True)#index true significa
    id_usuario_criador = Column(Integer,ForeignKey("usuarios_site.id")) 
    nome = Column(String(255), nullable=False)
    cnpj = Column(String(20), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    telefone = Column(String(20), nullable=False)
    api_key = Column(String(255), nullable=False, unique=True)  # Chave de API para autenticação
    
    # horario_inicio = Column(Time(timezone=False), nullable=False)
    # horario_fim = Column(Time(timezone=False), nullable=False)
    
    horarios = relationship("HorarioFuncionamento", back_populates="empresa")
    
    ramo_empresa = Column(String(255), nullable=False)  # Ex: "Barbearia", "Salão de Beleza"
    endereco_empresa = Column(String(255), nullable=True)
    
    agendamentos = relationship("Agendamento", back_populates="empresa")

    servicos = relationship("Servicos", back_populates="empresa")

class HorarioFuncionamento(Base):
    __tablename__ = "horarios_funcionamento"

    id = Column(Integer, primary_key=True,autoincrement=True)

    empresa_id = Column(Integer, ForeignKey("empresas.id"))

    dia_semana = Column(Enum(DiasAtendimento), nullable=False)

    horario_inicio = Column(Time, nullable=False)

    horario_fim = Column(Time, nullable=False)

    empresa = relationship("Empresa", back_populates="horarios")

class Agendamento(Base):
    __tablename__ = "agendamentos"

    id = Column(Integer, primary_key=True, index=True,autoincrement=True)

    empresa_id = Column('empresa_id',ForeignKey('empresas.id'), nullable=False)

    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=True)

    servico_id = Column(Integer, ForeignKey('servicos.id'), nullable=False)

    nome_cliente = Column(String(255), nullable=False)

    telefone_cliente = Column(String(20), nullable=False)

    nome_servico = Column(String(255), nullable=False)
    
    data_servico = Column(Date, nullable=False)

    hora_inicio = Column(Time(timezone=False), nullable=False)

    hora_fim = Column(Time(timezone=False), nullable=False)

    status = Column(Enum(StatusAgendamento), default="confirmado", nullable=False)

    profissional_id = Column(Integer, ForeignKey("profissionais.id"),nullable=True)

    criado_em = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    empresa = relationship("Empresa", back_populates="agendamentos")

    cliente = relationship("Cliente", back_populates="agendamentos")

    servico = relationship("Servicos", back_populates="agendamentos")

    profissional = relationship("Profissional",back_populates="agendamentos")


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, unique=False)
    telefone = Column(String(20), nullable=False, unique=True)
    #senha = Column(String(255), nullable=True)
    #origem = Column(Enum(Origem_Cliente), nullable=True)  # Ex: "WhatsApp", "Site"
    criado_em = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    agendamentos = relationship("Agendamento", back_populates="cliente")
    # admin = Column(Boolean, default=False)
    # ativo = Column(Boolean, default=True)


class Usuario(Base):
    __tablename__ = "usuarios_site"

    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    telefone = Column(String(20), nullable=False, unique=False)
    senha = Column(String(255), nullable=False)
    criado_em = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    admin = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)



profissional_servico = Table(
    "profissional_servico",
    Base.metadata,
    Column("profissional_id", ForeignKey("profissionais.id"), primary_key=True),
    Column("servico_id", ForeignKey("servicos.id"), primary_key=True)
)
class Servicos(Base):
    __tablename__ = "servicos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    empresa_id = Column(Integer, ForeignKey('empresas.id'), nullable=False, index=True)

    nome = Column(String(255), nullable=False)
    
    descricao = Column(String(255), nullable=True)

    duracao = Column(Integer, nullable=False)  # duração em minutos

    tempo_buffer = Column(Integer, default=0) #tempo adicional para limpeza ou preparação entre agendamentos, em minutos

    preco = Column(DECIMAL(10,2), nullable=False)  # valor monetário

    ativo = Column(Boolean, default=True)

    empresa = relationship("Empresa", back_populates="servicos")
    
    agendamentos = relationship("Agendamento", back_populates="servico")

    profissionais = relationship(
        "Profissional",
        secondary=profissional_servico,
        back_populates="servicos"
    )





class Profissional(Base):
    __tablename__ = "profissionais"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    empresa_id = Column(Integer,ForeignKey("empresas.id"),nullable=False,index=True)

    nome = Column(String(255),nullable=False)

    funcao = Column(String(255),nullable=True) # Ex: "Cabeleireiro", "Barbeiro", "Manicure"

    ativo = Column(Boolean,default=True)

    hora_inicio = Column(Time, nullable=True)
    hora_fim = Column(Time, nullable=True)

    agendamentos = relationship("Agendamento",back_populates="profissional")

    servicos = relationship(
        "Servicos",
        secondary=profissional_servico,
        back_populates="profissionais"
    )
