from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .dependencies import get_db, verificar_token, verificar_acesso_empresa
from .schemas import ConviteAceitarSchema, UsuarioEmpresaOut, AlterarNivelSchema
from .models import Empresa, Usuario, UsuarioEmpresa, NivelAcesso
import secrets

vinculos_router = APIRouter(prefix="/vinculos", tags=["Vínculos Empresa-Usuário"])


# --- GERAR CÓDIGO DE CONVITE (apenas admin_empresa, nível 3) ---
@vinculos_router.post("/{empresa_id}/gerar_convite")
async def gerar_convite(
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=3)),
    db: Session = Depends(get_db)
):
    empresa = acesso["empresa"]
    empresa.codigo_convite = secrets.token_hex(16)
    db.commit()
    db.refresh(empresa)
    return {
        "msg": "Código de convite gerado com sucesso",
        "codigo_convite": empresa.codigo_convite
    }


# --- ACEITAR CONVITE (qualquer usuário logado) ---
@vinculos_router.post("/aceitar_convite")
async def aceitar_convite(
    dados: ConviteAceitarSchema,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(verificar_token)
):
    empresa = db.query(Empresa).filter(
        Empresa.codigo_convite == dados.codigo_convite
    ).first()

    if not empresa:
        raise HTTPException(status_code=404, detail="Código de convite inválido ou expirado")

    # Verificar se já tem vínculo
    vinculo_existente = db.query(UsuarioEmpresa).filter(
        UsuarioEmpresa.usuario_id == usuario.id,
        UsuarioEmpresa.empresa_id == empresa.id
    ).first()

    if vinculo_existente:
        raise HTTPException(status_code=400, detail="Você já possui vínculo com esta empresa")

    # Também verificar se é o criador (já tem acesso automático)
    if empresa.id_usuario_criador == usuario.id:
        raise HTTPException(status_code=400, detail="Você é o criador desta empresa e já possui acesso total")

    novo_vinculo = UsuarioEmpresa(
        usuario_id=usuario.id,
        empresa_id=empresa.id,
        nivel=NivelAcesso.operador.value,  # entra como operador
        convidado_por=None  # convite via código, sem referência direta
    )
    db.add(novo_vinculo)
    db.commit()
    db.refresh(novo_vinculo)

    return {
        "msg": f"Vínculo criado com sucesso! Você agora é operador da empresa {empresa.nome}",
        "empresa_id": empresa.id,
        "empresa_nome": empresa.nome,
        "nivel": novo_vinculo.nivel
    }


# --- LISTAR VÍNCULOS DE UMA EMPRESA (admin_empresa, nível 3) ---
@vinculos_router.get("/{empresa_id}/listar", response_model=list[UsuarioEmpresaOut])
async def listar_vinculos(
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=3)),
    db: Session = Depends(get_db)
):
    empresa = acesso["empresa"]
    vinculos = db.query(UsuarioEmpresa).filter(
        UsuarioEmpresa.empresa_id == empresa.id
    ).all()
    return vinculos


# --- ALTERAR NÍVEL DE UM USUÁRIO (admin_empresa, nível 3) ---
@vinculos_router.put("/{empresa_id}/alterar_nivel")
async def alterar_nivel(
    dados: AlterarNivelSchema,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=3)),
    db: Session = Depends(get_db)
):
    if dados.novo_nivel not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Nível inválido. Use 1 (operador), 2 (gerenciador) ou 3 (admin_empresa)")

    empresa = acesso["empresa"]
    usuario_logado = acesso["usuario"]

    # Não pode alterar o próprio nível
    if dados.usuario_id == usuario_logado.id:
        raise HTTPException(status_code=400, detail="Você não pode alterar seu próprio nível")

    vinculo = db.query(UsuarioEmpresa).filter(
        UsuarioEmpresa.usuario_id == dados.usuario_id,
        UsuarioEmpresa.empresa_id == empresa.id
    ).first()

    if not vinculo:
        raise HTTPException(status_code=404, detail="Vínculo não encontrado para este usuário")

    vinculo.nivel = dados.novo_nivel
    db.commit()
    db.refresh(vinculo)

    niveis_nome = {1: "operador", 2: "gerenciador", 3: "admin_empresa"}
    return {
        "msg": f"Nível alterado para {niveis_nome.get(dados.novo_nivel, dados.novo_nivel)}",
        "usuario_id": dados.usuario_id,
        "novo_nivel": vinculo.nivel
    }


# --- REMOVER VÍNCULO (admin_empresa, nível 3) ---
@vinculos_router.delete("/{empresa_id}/remover/{usuario_id}")
async def remover_vinculo(
    usuario_id: int,
    acesso: dict = Depends(verificar_acesso_empresa(nivel_minimo=3)),
    db: Session = Depends(get_db)
):
    empresa = acesso["empresa"]
    usuario_logado = acesso["usuario"]

    # Não pode remover a si mesmo
    if usuario_id == usuario_logado.id:
        raise HTTPException(status_code=400, detail="Você não pode remover seu próprio vínculo")

    # Não pode remover o criador da empresa
    if usuario_id == empresa.id_usuario_criador:
        raise HTTPException(status_code=400, detail="Não é possível remover o criador da empresa")

    vinculo = db.query(UsuarioEmpresa).filter(
        UsuarioEmpresa.usuario_id == usuario_id,
        UsuarioEmpresa.empresa_id == empresa.id
    ).first()

    if not vinculo:
        raise HTTPException(status_code=404, detail="Vínculo não encontrado")

    db.delete(vinculo)
    db.commit()
    return {"msg": "Vínculo removido com sucesso"}


# --- MINHAS EMPRESAS (lista empresas do usuário logado) ---
@vinculos_router.get("/minhas_empresas")
async def minhas_empresas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(verificar_token)
):
    vinculos = db.query(UsuarioEmpresa).filter(
        UsuarioEmpresa.usuario_id == usuario.id
    ).all()

    # Também incluir empresas onde é criador (retrocompatibilidade)
    empresas_criadas = db.query(Empresa).filter(
        Empresa.id_usuario_criador == usuario.id
    ).all()
    empresas_criadas_ids = {e.id for e in empresas_criadas}

    resultado = []

    # Adicionar empresas criadas como admin
    for empresa in empresas_criadas:
        resultado.append({
            "empresa_id": empresa.id,
            "empresa_nome": empresa.nome,
            "nivel": 3,
            "origem": "criador"
        })

    # Adicionar empresas vinculadas (sem duplicar)
    niveis_nome = {1: "operador", 2: "gerenciador", 3: "admin_empresa"}
    for vinculo in vinculos:
        if vinculo.empresa_id not in empresas_criadas_ids:
            resultado.append({
                "empresa_id": vinculo.empresa_id,
                "empresa_nome": vinculo.empresa.nome,
                "nivel": vinculo.nivel,
                "nivel_nome": niveis_nome.get(vinculo.nivel, "desconhecido"),
                "origem": "convite"
            })

    return resultado
