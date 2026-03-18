from pydantic import BaseModel,field_validator
from datetime import date, time,datetime
from enum import Enum
from typing import List,Optional


class StatusAgendamento(str, Enum):
    """Estados possíveis de um agendamento."""
    confirmado = "confirmado"
    cancelado = "cancelado"
    concluido = "concluido"

import enum

class DiasAtendimento(str, enum.Enum):
    """Dias da semana para controle de funcionamento."""
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

# --- Schemas de Criação (Input) ---

class EmpresaCreate(BaseModel):
    nome: str
    cnpj: str
    email: str
    telefone: str
    ramo_empresa: str
    endereco_empresa: Optional[str] = None
    horarios: List[HorarioFuncionamentoCreate] = []
    #horarios: List[HorarioFuncionamentoCreate]
    

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
    
class ChartDataPoint(BaseModel):
    label: str
    value: float

class HeatmapPoint(BaseModel):
    dia_semana: int  # 0-6
    hora: int        # 0-23
    valor: float

class PeriodoFiltro(str, enum.Enum):
    dia = "dia"
    semana = "semana"
    mes = "mes"

class DashboardStats(BaseModel):
    # Métricas Principais
    total_empresas: int
    total_agendamentos: int
    total_profissionais: int
    taxa_utilizacao: float
    taxa_cancelamento: float
    
    # Gráficos e Detalhes
    agendamentos_por_empresa: List[ChartDataPoint]
    agendamentos_por_dia: List[ChartDataPoint]
    top_profissionais: List[ChartDataPoint]
    
    # Novas métricas para drill-down
    crescimento_empresas: List[ChartDataPoint]
    empresas_por_status: List[ChartDataPoint]
    agendamentos_por_horario: List[ChartDataPoint]
    comparativo_periodo: List[ChartDataPoint]
    ranking_profissionais: List[ChartDataPoint]
    tempo_medio_profissional: List[ChartDataPoint]
    heatmap_ocupacao: List[HeatmapPoint]
    disponibilidade_vs_preenchido: List[ChartDataPoint]

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
    horarios: Optional[List[HorarioFuncionamentoCreate]] = None  # adicionar/substituir horários


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
    horarios: Optional[List[HorarioFuncionamentoCreate]] = None  # horários por dia da semana

class ProfissionalUpdate(BaseModel):
    nome: Optional[str] = None
    funcao: Optional[str] = None
    ativo: Optional[bool] = None
    servicos_ids: Optional[List[int]] = None
    horarios: Optional[List[HorarioFuncionamentoCreate]] = None  # substitui todos os horários


# --- Schemas para sistema multi-usuário por empresa ---

class ConviteAceitarSchema(BaseModel):
    codigo_convite: str

class UsuarioEmpresaOut(BaseModel):
    id: int
    usuario_id: int
    empresa_id: int
    nivel: int  # 1=operador, 2=gerenciador, 3=admin_empresa
    convidado_por: Optional[int] = None
    usuario_nome: Optional[str] = None
    criado_em: Optional[datetime] = None

    class Config:
        from_attributes = True

class AlterarNivelSchema(BaseModel):
    usuario_id: int
    novo_nivel: int  # 1, 2 ou 3

class UsuarioEmpresaCreate(BaseModel):
    usuario_id: int
    empresa_id: int
    nivel: int = 1  # default operador


# --- Schemas de saída (Out) ---

class HorarioOut(BaseModel):
    dia_semana: str
    horario_inicio: time
    horario_fim: time

    class Config:
        from_attributes = True

class ServicosOut(BaseModel):
    id: int
    nome: str
    duracao: int
    preco: float
    empresa_id: int
    descricao: Optional[str] = None
    tempo_buffer: int = 0
    ativo: bool = True

    class Config:
        from_attributes = True

class ProfissionalOut(BaseModel):
    id: int
    nome: str
    empresa_id: int
    funcao: Optional[str] = None
    ativo: bool = True
    servicos_ofertados: List[str] = []  # nomes dos serviços
    horarios: List[HorarioOut] = []

    class Config:
        from_attributes = True

class EmpresaDetailOut(BaseModel):
    id: int
    nome: str
    cnpj: str
    email: str
    telefone: str
    ramo_empresa: str
    endereco_empresa: Optional[str] = None
    criado_em: Optional[datetime] = None
    horarios: List[HorarioOut] = []
    servicos: List[ServicosOut] = []
    profissionais: List[ProfissionalOut] = []

    class Config:
        from_attributes = True

