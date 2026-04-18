import os
import json
import httpx
from fastapi import FastAPI, HTTPException, Request
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Carregar variáveis de ambiente do .env local (do agente orquestrador)
load_dotenv(".env.orchestrator")

app = FastAPI(title="Agente IA Orquestrador WhatsApp")

import logging

# Configurações do LLM e API
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_MODEL = os.getenv("XAI_MODEL", "llama-3.3-70b-versatile")
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.groq.com/openai/v1")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Configurações da Meta Cloud API para envio de mensagens
# O token de acesso deve ser o "Permanent Token" gerado no Painel da Meta for Developers
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "").strip()
# ID do número de telefone cadastrado na Meta (Phone Number ID, NÃO o WABA ID)
META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID", "").strip()

if not XAI_API_KEY:
    logging.warning("XAI_API_KEY não configurada no .env.orchestrator. Algumas funcionalidades falharão.")

if not META_ACCESS_TOKEN:
    logging.warning("META_ACCESS_TOKEN não configurada. As respostas NÃO serão enviadas ao WhatsApp.")

if not META_PHONE_NUMBER_ID:
    logging.warning("META_PHONE_NUMBER_ID não configurada. As respostas NÃO serão enviadas ao WhatsApp.")

# Cliente OpenAI assíncrono conectado na Groq
client = AsyncOpenAI(api_key=XAI_API_KEY or "dummy_key_para_testes", base_url=XAI_BASE_URL)

# Memória em dicionário: telefone_cliente -> lista de mensagens da conversa
memory: Dict[str, List[dict]] = {}


async def send_whatsapp_reply(destinatario: str, mensagem: str) -> None:
    """
    Envia uma mensagem de texto de volta ao usuário via Meta WhatsApp Cloud API.

    Args:
        destinatario: Número de telefone do destinatário no formato internacional sem '+' (ex: 5511999990000)
        mensagem:     Texto da resposta a ser enviada
    """
    if not META_ACCESS_TOKEN or not META_PHONE_NUMBER_ID:
        logging.warning(
            f"[send_whatsapp_reply] META_ACCESS_TOKEN ou META_PHONE_NUMBER_ID ausentes. "
            f"Mensagem para {destinatario} NÃO foi enviada."
        )
        return

    # URL da Graph API para envio de mensagens
    url = f"https://graph.facebook.com/v19.0/{META_PHONE_NUMBER_ID}/messages"

    # Payload exigido pela Meta Cloud API
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": destinatario,
        "type": "text",
        "text": {"preview_url": False, "body": mensagem}
    }

    headers = {
        "Authorization": f"Bearer {META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as http_client:
        try:
            resp = await http_client.post(url, json=payload, headers=headers, timeout=10.0)
            if resp.status_code == 200:
                logging.info(f"[send_whatsapp_reply] Mensagem enviada a {destinatario}. Resposta Meta: {resp.text}")
            else:
                logging.error(
                    f"[send_whatsapp_reply] Falha ao enviar para {destinatario}. "
                    f"Status: {resp.status_code} | Corpo: {resp.text}"
                )
        except Exception as e:
            logging.error(f"[send_whatsapp_reply] Exceção ao enviar mensagem: {e}")


def normalizar_telefone_br(numero: str) -> str:
    """
    Normaliza números de celular brasileiros recebidos via WhatsApp.

    O WhatsApp às vezes envia números antigos sem o 9º dígito:
      Ex: 556294395922 (12 dígitos) → deveria ser 5562994395922 (13 dígitos)

    Regra:
      - Começa com '55' (código do Brasil)
      - Tem 12 dígitos no total: 55 + DDD(2) + número antigo(8)
      - Insere '9' após o DDD: 55 + DDD(2) + '9' + número(8) = 13 dígitos

    Args:
        numero: Número recebido no formato E.164 sem '+' (ex: '556294395922')

    Returns:
        Número normalizado com 13 dígitos para celulares brasileiros
    """
    if numero and numero.startswith("55") and len(numero) == 12:
        # Formato antigo: 55 + DDD(2 dígitos) + número(8 dígitos) → inserir '9' após DDD
        ddd = numero[2:4]       # ex: '62'
        num_sem_9 = numero[4:]  # ex: '94395922'
        numero_corrigido = f"55{ddd}9{num_sem_9}"
        logging.info(f"[normalizar_telefone_br] {numero} → {numero_corrigido} (9º dígito inserido automaticamente)")
        return numero_corrigido
    return numero


tools = [
    {
        "type": "function",
        "function": {
            "name": "ver_servicos",
            "description": "Busca a lita de serviços da empresa para apresentar ao cliente.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_horarios_ocupados",
            "description": "Verifica os horários já reservados no sistema num determinado dia para que você liste apenas o que estiver livre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data_servico": {"type": "string", "description": "Formato exigido pela API: YYYY-MM-DD"},
                    "profissional_id": {"type": "string", "description": "ID do profissional, se fornecido"}
                },
                "required": ["data_servico"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "criar_agendamento",
            "description": "Cria de fato o agendamento depois que o cliente confirmar as informações.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_cliente": {"type": "string", "description": "Nome coletado na conversa"},
                    "data_servico": {"type": "string", "description": "YYYY-MM-DD"},
                    "hora_inicio": {"type": "string", "description": "HH:MM"},
                    "nome_servico": {"type": "string", "description": "Nome exato idêntico ao serviço lido no ver_servicos"},
                    "servico_id": {"type": "string", "description": "ID numérico correspondente ao serviço escolhido."},
                    "profissional_id": {"type": "string", "description": "ID numérico do profissional escolhido (se possuir)"}
                },
                "required": ["nome_cliente", "data_servico", "hora_inicio", "nome_servico", "servico_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancelar_agendamento",
            "description": "Cancela o último agendamento salvo pelo cliente. ATENÇÃO: NUNCA chame essa função durante a criação de um novo agendamento. SÓ USE esta função se o cliente disser explicitamente a palavra 'cancelar' ou pedir claramente para desmarcar seu agendamento atual.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sincronizar_google",
            "description": "Ferramenta a ser chamada impreterivelmente sempre após um agir da criação de agendamento confirmado na API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agendamento_id": {"type": "string", "description": "O ID do agendamento q retornou no post criar_agendamento"}
                },
                "required": ["agendamento_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_info_empresa",
            "description": "Busca as informações públicas da empresa (nome, email, endereço, ramo de atuação e descrição). Use esta ferramenta para apresentar a empresa ao cliente quando ele solicitar informações sobre o local.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_dados_cliente",
            "description": "Retorna os dados cadastrais do cliente que está conversando com você no momento (nome, email, telefone, data de cadastro). Use APENAS quando o próprio cliente perguntar sobre os seus dados cadastrados. NUNCA repasse dados de outras pessoas.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

async def execute_tool(name: str, args: dict, api_key: str, telefone: str) -> str:
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient() as http_client:
        try:
            if name == "ver_servicos":
                resp = await http_client.get(f"{API_BASE_URL}/agendamentos/servicos_disponiveis", headers=headers)
                return resp.text
            
            elif name == "ver_horarios_ocupados":
                data = args.get("data_servico")
                prof_id = args.get("profissional_id")
                url = f"{API_BASE_URL}/agendamentos/horarios_ocupados?data_servico={data}"
                if prof_id:
                    url += f"&profissional_id={int(prof_id)}"
                resp = await http_client.get(url, headers=headers)
                return resp.text
                
            elif name == "criar_agendamento":
                payload = {
                    "nome_cliente": args.get("nome_cliente"),
                    "telefone_cliente": telefone,
                    "data_servico": args.get("data_servico"),
                    "hora_inicio": args.get("hora_inicio"),
                    "nome_servico": args.get("nome_servico"),
                    "servico_id": int(args.get("servico_id"))
                }
                if args.get("profissional_id"):
                    payload["profissional_id"] = int(args.get("profissional_id"))
                resp = await http_client.post(f"{API_BASE_URL}/agendamentos/criar", json=payload, headers=headers)
                return resp.text
                
            elif name == "cancelar_agendamento":
                resp = await http_client.post(f"{API_BASE_URL}/agendamentos/cancelar?telefone={telefone}", headers=headers)
                return resp.text
                
            elif name == "sincronizar_google":
                # Mock integration until actual Google APIs are placed
                agend_id = args.get("agendamento_id")
                return json.dumps({"status": "success", "msg": f"O Agendamento {agend_id} foi adicionado no Google Calendar e Sheets internamente."})
                
            elif name == "ver_info_empresa":
                resp = await http_client.get(f"{API_BASE_URL}/agendamentos/info_empresa", headers=headers)
                return resp.text
                
            elif name == "ver_dados_cliente":
                # A API key e o telefone do cliente já garantem que só retornará dados dele
                resp = await http_client.get(f"{API_BASE_URL}/agendamentos/meus_dados?telefone={telefone}", headers=headers)
                return resp.text
                
            return json.dumps({"error": "Ferramenta inexistente"})
            
        except Exception as e:
            return json.dumps({"error": str(e)})

@app.get("/webhook/whatsapp/{api_key}")
async def verificar_webhook_meta(api_key: str, hub_mode: str = None, hub_challenge: str = None, hub_verify_token: str = None):
    """
    Endpoint GET exigido pela Meta para verificação inicial do webhook.
    A Meta faz uma requisição GET com os parâmetros hub.mode, hub.challenge e hub.verify_token.
    Se o token bater, retornamos o hub.challenge para confirmar o registro do webhook.
    """
    import logging
    import os

    # Token de verificação definido no .env.orchestrator
    token_esperado = os.getenv("META_VERIFY_TOKEN", "roberto_whatsapp_token_2026")

    logging.info(f"[Webhook GET] mode={hub_mode}, token_recebido={hub_verify_token}, token_esperado={token_esperado}")

    if hub_mode == "subscribe" and hub_verify_token == token_esperado:
        # Retorna o challenge como texto puro (a Meta exige isso)
        from fastapi.responses import PlainTextResponse
        logging.info("[Webhook GET] Verificação bem-sucedida. Retornando challenge.")
        return PlainTextResponse(content=hub_challenge)

    logging.warning("[Webhook GET] Falha na verificação do token.")
    raise HTTPException(status_code=403, detail="Token de verificação inválido ou modo inválido.")


@app.post("/webhook/whatsapp/{api_key}")
async def whatsapp_webhook(api_key: str, request: Request):
    """
    Recebe eventos do WhatsApp via Meta Cloud API.

    Usando Request diretamente (em vez de `payload: dict`) para aceitar qualquer
    corpo JSON enviado pela Meta, inclusive notificações de status sem mensagem.

    A Meta envia dois tipos principais de evento:
      1. Mensagem nova   → entry[0].changes[0].value.messages existe
      2. Status update   → entry[0].changes[0].value.statuses existe (entrega/leitura)

    Também aceita o formato simplificado usado nos testes:
    {"from": "5511...", "message": "Olá!"}
    """
    # Lê o corpo como JSON — em caso de falha retorna 200 para a Meta não reenviar
    try:
        payload = await request.json()
    except Exception as json_err:
        logging.warning(f"[Webhook POST] Corpo inválido (não é JSON): {json_err}")
        return {"status": "ignored", "reason": "corpo não é JSON válido"}

    logging.info(f"[Webhook POST] Payload recebido: {payload}")

    from_number: Optional[str] = None
    message: Optional[str] = None
    eh_payload_meta = False  # flag para saber se veio da Meta

    # ---------------------------------------------------------------
    # Tenta parsear o formato real da Meta WhatsApp Cloud API
    # ---------------------------------------------------------------
    try:
        entry_list = payload.get("entry", [])
        if entry_list:
            changes = entry_list[0].get("changes", [])
            if changes:
                value = changes[0].get("value", {})

                # ---- Notificações de STATUS (entrega, leitura) ----
                # A Meta envia 'statuses' em vez de 'messages' nesses casos
                if value.get("statuses"):
                    status_info = value["statuses"][0]
                    logging.info(
                        f"[Webhook POST] Evento de status recebido: "
                        f"id={status_info.get('id')} status={status_info.get('status')}"
                    )
                    # Retorna 200 imediatamente — a Meta não pode reenviar isso
                    return {"status": "ok", "event": "status_update"}

                messages_list = value.get("messages", [])

                # ---- Payload Meta sem mensagem (ex: template, etc.) ----
                if not messages_list:
                    logging.info("[Webhook POST] Payload Meta sem 'messages'. Ignorando silenciosamente.")
                    return {"status": "ok", "event": "no_message"}

                eh_payload_meta = True
                msg_obj = messages_list[0]

                # Extrai o número de origem e normaliza para o formato brasileiro de 13 dígitos
                from_number = normalizar_telefone_br(msg_obj.get("from", ""))

                # Extrai o texto de acordo com o tipo de mensagem
                tipo = msg_obj.get("type", "text")
                if tipo == "text":
                    message = msg_obj.get("text", {}).get("body")
                elif tipo == "interactive":
                    # Mensagens de botão/lista de resposta rápida
                    interactive = msg_obj.get("interactive", {})
                    if interactive.get("type") == "button_reply":
                        message = interactive.get("button_reply", {}).get("title")
                    elif interactive.get("type") == "list_reply":
                        message = interactive.get("list_reply", {}).get("title")
                else:
                    # Tipo não suportado (áudio, imagem, etc.)
                    logging.warning(f"[Webhook POST] Tipo de mensagem não suportado: {tipo}")
                    # Retorna 200 para a Meta não reenviar (mas ignora a mensagem)
                    return {"status": "ignored", "reason": f"Tipo '{tipo}' não suportado"}
    except Exception as parse_err:
        logging.warning(f"[Webhook POST] Falha ao parsear formato Meta: {parse_err}")

    # ---------------------------------------------------------------
    # Fallback: formato simplificado usado nos testes locais
    # {"from": "5511...", "message": "Olá!"}
    # ---------------------------------------------------------------
    if not from_number:
        from_number = payload.get("from")
    if not message:
        message = payload.get("message")

    # ---------------------------------------------------------------
    # Validação final — só retorna erro se não for payload da Meta
    # (a Meta nunca deve receber 400 pois causa reenvio em loop)
    # ---------------------------------------------------------------
    if not from_number or not message:
        if eh_payload_meta:
            # Payload da Meta sem mensagem extraível — retorna 200 silenciosamente
            logging.warning(f"[Webhook POST] Payload Meta sem 'from'/'message' extraíveis. Ignorando.")
            return {"status": "ok", "event": "unprocessable"}
        # Payload de teste local inválido — retorna 400 normalmente
        logging.error(f"[Webhook POST] 400 - 'from' ou 'message' ausentes. Payload: {payload}")
        raise HTTPException(status_code=400, detail="Missing 'from' or 'message' property in JSON payload")
        
    # Inicializa memória da conversa se for a primeira vez
    if from_number not in memory:
        from datetime import datetime
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = f"""Você é um assistente virtual atencioso que faz agendamentos via WhatsApp.
Data e Hora atual: {agora}. Use isso como referência inflexível ao lidar com datas (ex: se o cliente pedir para 'amanhã', veja a data de hoje e some 1 dia. Se pedir para daqui x dias, adicione e transforme em YYYY-MM-DD).

O telefone do cliente está embutido. Seu objetivo é agendar o serviço de forma RÁPIDA, EFICIENTE e NATURAL.
NUNCA seja repetitivo. Se o cliente já fornecer as informações de serviço e horario, NÃO FAÇA novas perguntas; apenas certifique-se que você tenha o ID do serviço usando `ver_servicos` silenciosamente se ele não disse antes.

ATENÇÃO CRÍTICA (REGRAS DE CONVERSAÇÃO):
1. NUNCA chame a ferramenta `cancelar_agendamento` para limpar agendamentos antigos quando for criar um novo. Ela deleta o histórico do cliente. SÓ chame essa ferramenta se o cliente pedir expressamente para CANCELAR.
2. Você pode usar a ferramenta `ver_info_empresa` para conhecer o local onde você trabalha e repassar essas infos ao cliente se ele perguntar.
3. Você tem acesso à ferramenta `ver_dados_cliente`. Se o cliente quiser saber se tem cadastro ou quais seus dados, use essa ferramenta.
4. NUNCA EXIJA MÚLTIPLAS CONFIRMAÇÕES. Se você resumiu o agendamento e o cliente respondeu "sim", "pode marcar", "ok" ou similar, CHAME IMEDIATAMENTE a ferramenta `criar_agendamento` sem perguntar mais nada.
5. NUNCA ENVIE JSON OU SCHEMAS PARA O CLIENTE. Quando usar ferramentas (como `sincronizar_google`), faça isso de forma invisível. Suas mensagens devem ser 100% em texto natural e amigável (ex: "Agendamento criado com sucesso! Você tem um agendamento na quarta-feira... Vou sincronizar com nossa agenda.").

PASSO A PASSO DA CONVERSA (Execute passos condensados se possível):
1. Identificação: Pergunte o nome do cliente.
2. Serviço: Descubra o serviço lendo `ver_servicos` e ofereça os profissionais listados.
3. Data/Hora: Chame `ver_horarios_ocupados` para checar disponibilidade de vaga para a data do cliente. Se vier 'horarios_ocupados', você deve oferecer os horários restantes da loja.
4. Confirmação ÚNICA: Faça um resumo das informações e peça confirmação.
5. Agendamento: Assim que o cliente confirmar, chame `criar_agendamento` imediatamente.
6. Conclusão: Avise o cliente usando LINGUAGEM NATURAL e, na mesma resposta, chame `sincronizar_google` silenciosamente.
"""
        memory[from_number] = [{"role": "system", "content": prompt}]
        
    memory[from_number].append({"role": "user", "content": message})
    
    try:
        # Pede resposta pro Groq
        response = await client.chat.completions.create(
            model=XAI_MODEL,
            messages=memory[from_number],
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # Caso decida usar function calling (tools)
        if response_message.tool_calls:
            # Serializar devidamente à memória (dict structure instead of pure object helps prevent API bugs)
            msg_to_store = {
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": []
            }
            
            for tc in response_message.tool_calls:
                msg_to_store["tool_calls"].append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })
            memory[from_number].append(msg_to_store)
            
            # Percorrer executando
            for tool_call in response_message.tool_calls:
                f_name = tool_call.function.name
                f_args = json.loads(tool_call.function.arguments)
                
                tool_result = await execute_tool(f_name, f_args, api_key, from_number)
                
                memory[from_number].append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": f_name,
                    "content": str(tool_result)
                })
                
            # Chama a IA de volta já com o resultado da rota (Backend)
            second_response = await client.chat.completions.create(
                model=XAI_MODEL,
                messages=memory[from_number]
            )
            final_msg = second_response.choices[0].message.content
            memory[from_number].append({"role": "assistant", "content": final_msg})
            # Envia a resposta de volta via Meta Cloud API
            await send_whatsapp_reply(destinatario=from_number, mensagem=final_msg)
            return {"response": final_msg}
            
        else:
            final_msg = response_message.content
            memory[from_number].append({"role": "assistant", "content": final_msg})
            # Envia a resposta de volta via Meta Cloud API
            await send_whatsapp_reply(destinatario=from_number, mensagem=final_msg)
            return {"response": final_msg}
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
