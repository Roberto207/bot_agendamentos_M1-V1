from fastapi import APIRouter,Depends, HTTPException #criador de roteadores q gerenciam as rotas e o gerenciador de dependencias E o http pra mensagens de erro
from .dependencies import get_db,verificar_token #importando a dependencia de conexao com o banco de dados e a dependencia de verificacao da api key
from .main import bcrypt_context,SECRET_KEY,ALGORITHM,ACCESS_TOKEN_EXPIRE_MINUTES,oauth2_schema
from passlib.hash import bcrypt #importando as variaveis de criptografia e token do main
from jose import jwt,JWTError #usado pra criacao de jwts 
from datetime import datetime,timedelta, timezone #usado pra definir tempo de expiracao do token jwt
from sqlalchemy.orm import Session #usado pra criar a sessao do banco de dados
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm #usado pra definir o esquema de autenticacao do tipo oauth2 com senha e bearer token
from .models import Usuario
from .schemas import LoginSchema,DeleteSchema,UsuarioSchema,UsuarioUpdate



def criar_token(usuario_id,duracao_token = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    data_expiracao = datetime.now(timezone.utc) + duracao_token # data_expiracao = momento em q o token foi criado + tempo definido na variavel acess token...
    
    dicionario_infos = {"sub" : str(usuario_id),"expiration_date":data_expiracao.timestamp()} #dicionario q fala quais informacoes estarao presentes no jwt,nesse caso id e data_exp 
    
    jwt_codificado = jwt.encode(dicionario_infos,SECRET_KEY,algorithm=ALGORITHM) #a funcao q cria jwts,pede o dicionario com o q sera codificado,a chave de codificacao (secret_key) e o algoritmo de codificacao. tudo isso ja foi criado no env e armazenado no arquivo main
    return jwt_codificado

def autentificar_usuario(email,senha,session):
    usuario = session.query(Usuario).filter(Usuario.email==email).first() #vendo se o telefone inserido pelo cliente esta na database
    if not usuario:
        return False
    elif not bcrypt_context.verify(senha,usuario.senha): #verifica se a senha colocada no login é igual a senha descriptografada presente na database
        return False #se as senhas n coincidirem retorna falso 

    return usuario #so retorna usuario se passar por tdos os ifs




auth_site_router = APIRouter(prefix='/auth_site',tags=['Authentfication_Site']) #criando o roteador de clientes, com prefixo e tag

@auth_site_router.get('/')  #oq vem no parentesis,sera colocado na frente do prefixo
async def autentificar_cadastrar():
    #docstring explicando a rota,bom pra apis publicas
    """
    Rota pra cadastro,login e autentificacao de clientes vindos do site,ja que por enquanto pelo whatsap 
    nao é necessario autentificacao do cliente,mas futuramente pode ser que seja,entao ja deixamos essa 
    rota pronta pra quando chegar nessa etapa do projeto. Nessa rota o cliente pode se cadastrar e fazer 
    login, e a resposta da api vai ser um token jwt q o cliente pode usar pra acessar rotas protegidas da 
    api,como por exemplo as rota de agendamento pelo site, onde o cliente precisa estar autenticado pra criar 
    um agendamento. O token jwt tem um tempo de expiracao definido na variavel ACCESS_TOKEN_EXPIRE_MINUTES,
    entao o cliente precisa fazer login novamente depois desse tempo pra obter um novo token jwt.
    """
    return {'mensagem' : 'voce acessou a rota padrao de autentificacao','autentificado' : True} #é possivel passar mais de uma informacao no dicionario,aqui mandamos o true q o usuario esta autentificado,claro q nao foi autentificado de vdd mas por enquanto deixamos assim 


@auth_site_router.post('/cadastro')
async def cadastrar_usuario(usuario : UsuarioSchema,db : Session = Depends(get_db)):
    """
    ola
    """
    usuario_existente = db.query(Usuario).filter(Usuario.email == usuario.email).first() #verificando se o email do usuario ja esta cadastrado na database, se tiver, nao pode cadastrar de novo
    if usuario_existente:
        raise HTTPException(status_code=400,detail="Email já cadastrado") #se o email ja estiver cadastrado, retorna um erro 400 com a mensagem "email ja cadastrado"
    
    senha_hash = bcrypt_context.hash(usuario.senha) #a senha do usuario é criptografada usando o bcrypt antes de ser armazenada no banco de dados, isso é importante pra segurança dos dados dos usuarios, caso o banco de dados seja comprometido, as senhas dos usuarios estarao protegidas
    
    novo_usuario = Usuario(
        nome = usuario.nome,
        telefone = usuario.telefone,
        senha = senha_hash,
        email = usuario.email,
        criado_em = datetime.now(),
        admin = usuario.admin,
        ativo = usuario.ativo

    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return {"mensagem": "Usuário cadastrado com sucesso",}


@auth_site_router.post('/login')
#versao login sem dados formulario que é algo opcional pra termos permissao nas docs do fastapi mas o frontend funciona perfeitamente sem o parametro dados_formulario
async def login(loginschema : LoginSchema ,db: Session = Depends(get_db)):
    """
    Essa rota é usada para autentificar um usuario ja cadastrado no sistema,ela recebe um objeto do tipo LoginSchema com o
    email e senha do usuario,verifica se as credenciais estao corretas e se estiverem,gera um token JWT de acesso e um 
    token de refresh (opcional) e retorna ambos os tokens para o usuario
    """
    
    
    usuario = autentificar_usuario(email=loginschema.email,senha=loginschema.senha,session=db) #aplicando a funcao 
    
    if not usuario:
        raise HTTPException(status_code=400,detail="email nao encontrado no sistema ou credenciais invalidas")
    
    else:
        access_token = criar_token(usuario.id)
        refresh_token = criar_token(usuario.id,duracao_token= timedelta(days=7)) #token secundario usado qnd o access token expira pra dar mais tempo ao usaurio e ele n preicsar fazer o login novamente. esse token é opcional
        return {
            "mensagem": "login feito com sucesso",
            "access_token": access_token,
            "refresh_token":refresh_token,
            "token_type" : "Bearer"
        }

@auth_site_router.post('/login_formula')
async def login_formula(dados_formulario : OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):
    
    """
    Autentica um usuário já cadastrado utilizando OAuth2PasswordRequestForm.
    Valida email e senha e, se corretos, retorna um token JWT de acesso
    (e opcionalmente um refresh token).

    Essa rota é opcional e existe para facilitar a autenticação via
    documentação automática do FastAPI, funcionando como alternativa
    à rota de login tradicional que utiliza LoginSchema.
    """
    
    
    usuario = autentificar_usuario(dados_formulario.username,dados_formulario.password,session=db) #aplicando a funcao 
    
    if not usuario:
        raise HTTPException(status_code=400,detail="email nao encontrado no sistema ou credenciais invalidas")
    else:
        access_token = criar_token(usuario.id)
        #refresh_token = criar_token(usuario.id,duracao_token= timedelta(days=7)) #token secundario usado qnd o access token expira pra dar mais tempo ao usaurio e ele n preicsar fazer o login novamente. esse token é opcional
        return {
            "access_token": access_token,
            "token_type" : "Bearer"
        }


@auth_site_router.get("/refresh_token")
#toda funcao de endpoint das rotas que tiver como parametro a Depends(verificar_token) sera restrita a usuarios autentificados com token ativo
async def usar_refresh_token(usuario: Usuario = Depends(verificar_token)): #funcao pra usar o refresh token qnd o acess token expira parametros = o parametro usuario tem valor do tipo database Usuario e o seu valor padrao vem da funcao verificar(token) q é uma dependencia
    """
    Rota pra gerar refresh token,ela é acessada quando o access token expira,ela recebe o usuario autenticado atraves do 
    token expirado e gera um novo access token pra ele. O refresh token é opcional e pode ser implementado de acordo com 
    as necessidades do sistema,mas a ideia geral é que ele tenha um tempo de expiração mais longo que o access token e s
    eja usado para gerar novos access tokens sem precisar que o usuário faça login novamente.
    """



    #criando novo token
    access_token = criar_token(usuario.id)
    return {
            "access_token ": access_token,
            "token_type" : "Bearer"
        }






@auth_site_router.delete("/deletar_usuario")
async def deletar_usuario(
    dados: DeleteSchema,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(verificar_token)
):
    """
    Rota para deletar um usuário do sistema. Ela recebe um objeto do tipo DeleteSchema com o email do usuário a ser deletado,
    uma sessão do banco de dados e o usuário autenticado através do token JWT. A função verifica o nivel de acesso do 
    usuario e executa a funcao
    """
    
    
    
    
    
    if usuario.admin == False and usuario.email != dados.email:
        raise HTTPException(403, "Voce nao tem permissao para deletar esse usuario")
    stmt = select(Usuario).where(Usuario.email == dados.email)
    usuario_a_deletar = db.execute(stmt).scalar_one_or_none()

    if not usuario_a_deletar:
        raise HTTPException(404, "Usuário não encontrado")

    db.delete(usuario_a_deletar)
    db.commit()

    return {"msg": f"Usuário {dados.email} deletado com sucesso"}

@auth_site_router.put("/atualizar_usuario")
async def atualizar_usuario(
    dados: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(verificar_token)
):
    """
    Rota para atualizar os dados do usuário. O e-mail é imutável e não pode ser alterado.
    """
    if dados.nome is not None:
        usuario.nome = dados.nome
    if dados.telefone is not None:
        usuario.telefone = dados.telefone
    if dados.senha is not None:
        usuario.senha = bcrypt_context.hash(dados.senha)
        
    db.commit()
    db.refresh(usuario)
    return {"msg": "Dados atualizados com sucesso", "usuario": {"nome": usuario.nome, "telefone": usuario.telefone}}
