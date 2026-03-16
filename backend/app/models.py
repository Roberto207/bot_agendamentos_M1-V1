from sqlalchemy import Column, Integer, String, Date, Time, Enum, TIMESTAMP,ForeignKey,Boolean,DECIMAL,Table,UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base
import enum
from sqlalchemy.sql import func
from .schemas import StatusAgendamento,DiasAtendimento


Base = Base

# Enum para níveis de acesso de usuários vinculados a empresas
class NivelAcesso(int, enum.Enum):
    operador = 1        # pode criar/editar agendamentos, serviços, profissionais
    gerenciador = 2     # operador + gerenciar dados da empresa
    admin_empresa = 3   # pode tudo na empresa (convidar, remover, editar, deletar)

class Empresa(Base):
    """
    Representa uma empresa cadastrada no sistema.
    Contém informações cadastrais básicas, chave de API e gerencia relacionamentos
    com horários, serviços, profissionais e usuários vinculados.
    """
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_usuario_criador = Column(Integer, ForeignKey("usuarios_site.id")) 
    nome = Column(String(255), nullable=False)
    cnpj = Column(String(20), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    telefone = Column(String(20), nullable=False)
    api_key = Column(String(255), nullable=False, unique=True)  # Chave de API para autenticação legado/externa
    codigo_convite = Column(String(32), nullable=True, unique=True)  # Código para convidar novos usuários colaboradores
    criado_em = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # horario_inicio = Column(Time(timezone=False), nullable=False)
    # horario_fim = Column(Time(timezone=False), nullable=False)
    
    horarios = relationship("HorarioFuncionamento", back_populates="empresa")
    
    ramo_empresa = Column(String(255), nullable=False)  # Ex: "Barbearia", "Salão de Beleza"
    endereco_empresa = Column(String(255), nullable=True)
    
    agendamentos = relationship("Agendamento", back_populates="empresa")

    servicos = relationship("Servicos", back_populates="empresa")

    vinculos = relationship("UsuarioEmpresa", back_populates="empresa", cascade="all, delete-orphan")

class HorarioFuncionamento(Base):
    """
    Define os horários de início e fim de funcionamento da empresa para cada dia da semana.
    """
    __tablename__ = "horarios_funcionamento"

    id = Column(Integer, primary_key=True, autoincrement=True)
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
    """
    Cadastro de clientes da empresa.
    Armazena dados de contato e histórico de agendamentos.
    """
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, unique=False)
    telefone = Column(String(20), nullable=False, unique=True)
    criado_em = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    agendamentos = relationship("Agendamento", back_populates="cliente")


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

    vinculos = relationship("UsuarioEmpresa", back_populates="usuario", foreign_keys="[UsuarioEmpresa.usuario_id]", cascade="all, delete-orphan")


# Tabela intermediária: conecta múltiplos usuários a múltiplas empresas com nível de acesso
class UsuarioEmpresa(Base):
    """
    Tabela de associação (vínculo) entre usuários e empresas.
    Define o nível de acesso (operador, gerenciador, admin) de um usuário dentro de uma empresa específica.
    """
    __tablename__ = "usuarios_empresas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios_site.id"), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    nivel = Column(Integer, nullable=False, default=NivelAcesso.operador.value)  # 1=operador, 2=gerenciador, 3=admin_empresa
    convidado_por = Column(Integer, ForeignKey("usuarios_site.id"), nullable=True)  # Log de quem realizou o convite
    criado_em = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("usuario_id", "empresa_id", name="uq_usuario_empresa"),
    )

    usuario = relationship("Usuario", back_populates="vinculos", foreign_keys=[usuario_id])
    empresa = relationship("Empresa", back_populates="vinculos")
    convidador = relationship("Usuario", foreign_keys=[convidado_por])


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
    """
    Representa um profissional que presta serviços em uma empresa.
    Possui horários de trabalho específicos e está vinculado a um ou mais serviços.
    """
    __tablename__ = "profissionais"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    funcao = Column(String(255), nullable=True) # Ex: "Cabeleireiro", "Barbeiro", "Manicure"
    ativo = Column(Boolean, default=True)

    # Colunas de horário legado mantidas temporariamente
    hora_inicio = Column(Time, nullable=True)
    hora_fim = Column(Time, nullable=True)

    agendamentos = relationship("Agendamento", back_populates="profissional")
    servicos = relationship(
        "Servicos",
        secondary=profissional_servico,
        back_populates="profissionais"
    )

    horarios = relationship("HorarioProfissional", back_populates="profissional", cascade="all, delete-orphan")


class HorarioProfissional(Base):
    """Horários de trabalho por dia da semana para cada profissional.
    Segue as mesmas regras dos horários da empresa."""
    __tablename__ = "horarios_profissional"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=False)
    dia_semana = Column(Enum(DiasAtendimento), nullable=False)
    horario_inicio = Column(Time, nullable=False)
    horario_fim = Column(Time, nullable=False)

    profissional = relationship("Profissional", back_populates="horarios")
