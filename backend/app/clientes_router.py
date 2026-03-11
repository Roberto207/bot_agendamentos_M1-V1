from fastapi import APIRouter,Depends, HTTPException #criador de roteadores q gerenciam as rotas e o gerenciador de dependencias E o http pra mensagens de erro
from .dependencies import get_db,verificar_token #importando a dependencia de conexao com o banco de dados e a dependencia de verificacao da api key
from .main import bcrypt_context,SECRET_KEY,ALGORITMH,ACCESS_TOKEN_EXPIRE_MINUTES
from passlib.hash import bcrypt #importando as variaveis de criptografia e token do main
from jose import jwt,JWTError #usado pra criacao de jwts 
from datetime import datetime,timedelta, timezone #usado pra definir tempo de expiracao do token jwt
from sqlalchemy.orm import Session #usado pra criar a sessao do banco de dados
from fastapi.security import OAuth2PasswordRequestForm #usado pra definir o esquema de autenticacao do tipo oauth2 com senha e bearer token
from .models import Cliente,Empresa
from .schemas import Cliente_Create,Origem_Cliente

def criar_token(usuario_id,duracao_token = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    data_expiracao = datetime.now(timezone.utc) + duracao_token # data_expiracao = momento em q o token foi criado + tempo definido na variavel acess token...
    
    dicionario_infos = {"sub" : str(usuario_id),"expiration_date":data_expiracao.timestamp()} #dicionario q fala quais informacoes estarao presentes no jwt,nesse caso id e data_exp 
    
    jwt_codificado = jwt.encode(dicionario_infos,SECRET_KEY,algorithm=ALGORITMH) #a funcao q cria jwts,pede o dicionario com o q sera codificado,a chave de codificacao (secret_key) e o algoritmo de codificacao. tudo isso ja foi criado no env e armazenado no arquivo main
    return jwt_codificado

def autentificar_cliente(telefone,senha,session):
    cliente = session.query(Cliente).filter(Cliente.telefone==telefone).first() #vendo se o telefone inserido pelo cliente esta na database
    if not cliente:
        return False
    elif not bcrypt_context.verify(senha,cliente.senha): #verifica se a senha colocada no login é igual a senha descriptografada presente na database
        return False #se as senhas n coincidirem retorna falso 

    return cliente #so retorna cliente se passar por tdos os ifs

clientes_auth_router = APIRouter(prefix='/clientes_auth',tags=['Clientes_Auth']) #criando o roteador de clientes, com prefixo e tag

@clientes_auth_router.get('/')  #oq vem no parentesis,sera colocado na frente do prefixo
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


@clientes_auth_router.post('/cadastro')
async def cadastrar_cliente(cliente : Cliente_Create,db : Session = Depends(get_db)):
    """
    ola
    """
    cliente_existente = db.query(Cliente).filter(Cliente.telefone == cliente.telefone).first() or db.query(Cliente).filter(Cliente.email == cliente.email).first() #verificando se o telefone do cliente ja esta cadastrado na database, se tiver, nao pode cadastrar de novo
    if cliente_existente:
        raise HTTPException(status_code=400,detail="Telefone ou email já cadastrado") #se o telefone ja estiver cadastrado, retorna um erro 400 com a mensagem "telefone ja cadastrado"
    senha_hash = bcrypt_context.hash(cliente.senha) #a senha do cliente é criptografada usando o bcrypt antes de ser armazenada no banco de dados, isso é importante pra segurança dos dados dos clientes, caso o banco de dados seja comprometido, as senhas dos clientes estarao protegidas
    novo_cliente = Cliente(
        nome = cliente.nome,
        telefone = cliente.telefone,
        senha = senha_hash,
        email = cliente.email,
        criado_em = datetime.now(),
        origem = Origem_Cliente.site,
        admin = cliente.admin,
        ativo = cliente.ativo

    )

    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)
    return {"mensagem": "Cliente cadastrado com sucesso",}