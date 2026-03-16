from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .dependencies import get_db, verificar_api_key, verificar_api_key_empresa_create, verificar_token, verificar_acesso_empresa, update_model_strict
from .schemas import EmpresaCreate, EmpresaUpdate, EmpresaDetailOut, HorarioOut, ServicosOut, ProfissionalOut
from .models import Empresa, HorarioFuncionamento, Usuario, UsuarioEmpresa, NivelAcesso, Servicos, Profissional
import secrets



empresas_router = APIRouter(prefix="/empresa", tags=["Empresa"])

@empresas_router.post("/cadastrar_empresa")
async def cadastrar_empresa(
    empresa: EmpresaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(verificar_token)
):
    """
    Cadastra uma nova empresa no sistema.
    Requer um usuário logado. O criador se torna automaticamente o administrador da empresa.
    Gera uma API Key única para a empresa.
    """
    empresa_existente = db.query(Empresa).filter(Empresa.cnpj == empresa.cnpj).first() or db.query(Empresa).filter(Empresa.email == empresa.email).first()
    if empresa_existente:
        raise HTTPException(status_code = 404,detail = "empresa ja cadastrada,verifique o email ou o cnpj")
    api_key = secrets.token_hex(16)
    nova_empresa = Empresa(
        nome=empresa.nome,
        cnpj=empresa.cnpj,
        email=empresa.email,
        telefone=empresa.telefone,
        ramo_empresa=empresa.ramo_empresa,
        endereco_empresa=empresa.endereco_empresa,
        api_key=api_key,
        id_usuario_criador=usuario.id
    )

    db.add(nova_empresa)
    db.commit()
    db.refresh(nova_empresa)

    for horario in empresa.horarios:

        novo_horario = HorarioFuncionamento(
            empresa_id=nova_empresa.id,
            dia_semana=horario.dia_semana,
            horario_inicio=horario.horario_inicio,
            horario_fim=horario.horario_fim
        )

        db.add(novo_horario)

    # Criar vínculo automático: criador vira admin_empresa na tabela intermediária
    vinculo_criador = UsuarioEmpresa(
        usuario_id=usuario.id,
        empresa_id=nova_empresa.id,
        nivel=NivelAcesso.admin_empresa.value,
        convidado_por=None
    )
    db.add(vinculo_criador)

    db.commit()

    return {
        "id": nova_empresa.id,
        "nome": nova_empresa.nome,
        "api_key": api_key
    }

@empresas_router.get("/listar_empresas")
async def listar_empresas(db: Session = Depends(get_db), usuario: Usuario = Depends(verificar_token)):
    """
    Lista todas as empresas cadastradas.
    Acesso restrito a administradores globais do site (admin=True).
    """
    if not usuario.admin:
        raise HTTPException(status_code=403,detail="Acesso negado, apenas administradores podem acessar essa rota")
    
    empresas = db.query(Empresa).all()
    return empresas


@empresas_router.delete("/{empresa_id}")
async def deletar_empresa(
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=3)),
    db: Session = Depends(get_db)
):
    """
    Deleta permanentemente uma empresa e todos os seus dados vinculados (cascade).
    Apenas admin_empresa (nível 3), criador ou admin do site podem deletar.
    """
    """Apenas admin_empresa (nível 3), criador ou admin do site podem deletar"""
    empresa = acesso["empresa"]
    
    db.delete(empresa)
    db.commit()
    return {"msg": "Empresa deletada com sucesso"}


@empresas_router.put("/{empresa_id}")
async def atualizar_empresa(
    dados: EmpresaUpdate,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=3)),
    db: Session = Depends(get_db)
):
    """
    Atualiza dados cadastrais da empresa através do utilitário update_model_strict.
    Se horários forem enviados no corpo da requisição, os antigos são substituídos.
    Acesso restrito a administradores de empresa (Nível 3).
    """
    """Apenas admin_empresa (nível 3), criador ou admin do site podem atualizar.
    Se horarios forem enviados, os antigos são substituídos pelos novos."""
    empresa = acesso["empresa"]

    # Tratar horários separadamente (substituir todos se enviados)
    if dados.horarios is not None:
        # Remover horários antigos
        db.query(HorarioFuncionamento).filter(
            HorarioFuncionamento.empresa_id == empresa.id
        ).delete()

        # Adicionar novos
        for horario in dados.horarios:
            novo_horario = HorarioFuncionamento(
                empresa_id=empresa.id,
                dia_semana=horario.dia_semana,
                horario_inicio=horario.horario_inicio,
                horario_fim=horario.horario_fim
            )
            db.add(novo_horario)

    # Atualizar campos simples via update_model_strict
    empresa_atualizada = update_model_strict(
        db=db, 
        model_instance=empresa, 
        update_schema=dados,
        exclude_fields=["horarios"]
    )
    return empresa_atualizada


@empresas_router.get("/{empresa_id}/visualizar")
async def visualizar_empresa(
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=1)),
    db: Session = Depends(get_db)
):
    """
    Retorna uma visão consolidada da empresa, incluindo horários, serviços ativos e profissionais.
    Utilizada para alimentar o dashboard inicial de gerenciamento.
    Acesso permitido para qualquer colaborador vinculado (Nível 1+).
    """
    """Rota para visualizar detalhes da empresa.
    Disponível para: dono, admins do site, e qualquer usuário vinculado.
    Retorna: dados da empresa, horários de funcionamento, serviços e profissionais."""
    empresa = acesso["empresa"]

    # Horários de funcionamento da empresa
    horarios = [
        {
            "dia_semana": h.dia_semana.value,
            "horario_inicio": h.horario_inicio,
            "horario_fim": h.horario_fim
        }
        for h in empresa.horarios
    ]

    # Serviços ativos
    servicos = db.query(Servicos).filter(
        Servicos.empresa_id == empresa.id, Servicos.ativo == True
    ).all()
    servicos_out = [
        {
            "id": s.id,
            "nome": s.nome,
            "duracao": s.duracao,
            "preco": float(s.preco),
            "empresa_id": s.empresa_id,
            "descricao": s.descricao,
            "tempo_buffer": s.tempo_buffer,
            "ativo": s.ativo
        }
        for s in servicos
    ]

    # Profissionais ativos com seus serviços ofertados
    profissionais = db.query(Profissional).filter(
        Profissional.empresa_id == empresa.id, Profissional.ativo == True
    ).all()
    profissionais_out = []
    for p in profissionais:
        profissionais_out.append({
            "id": p.id,
            "nome": p.nome,
            "empresa_id": p.empresa_id,
            "funcao": p.funcao,
            "ativo": p.ativo,
            "servicos_ofertados": [s.nome for s in p.servicos],
            "horarios": [
                {
                    "dia_semana": h.dia_semana.value,
                    "horario_inicio": h.horario_inicio,
                    "horario_fim": h.horario_fim
                }
                for h in p.horarios
            ]
        })

    return {
        "id": empresa.id,
        "nome": empresa.nome,
        "cnpj": empresa.cnpj,
        "email": empresa.email,
        "telefone": empresa.telefone,
        "ramo_empresa": empresa.ramo_empresa,
        "endereco_empresa": empresa.endereco_empresa,
        "criado_em": empresa.criado_em,
        "horarios": horarios,
        "servicos": servicos_out,
        "profissionais": profissionais_out
    }