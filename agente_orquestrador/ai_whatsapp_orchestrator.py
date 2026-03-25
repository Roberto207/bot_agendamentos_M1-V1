import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import Dict, List

# Carregar variáveis de ambiente do .env local (do agente orquestrador)
load_dotenv(".env.orchestrator")

app = FastAPI(title="Agente IA Orquestrador WhatsApp")

# Configurações do LLM e API
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_MODEL = os.getenv("XAI_MODEL", "llama-3.3-70b-versatile")
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.groq.com/openai/v1")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

if not XAI_API_KEY:
    import logging
    logging.warning("XAI_API_KEY não configurada no .env.orchestrator. Algumas funcionalidades falharão.")

# Cliente OpenAI assíncrono conectado na Groq
client = AsyncOpenAI(api_key=XAI_API_KEY or "dummy_key_para_testes", base_url=XAI_BASE_URL)

# Memória em dicionário: telefone_cliente -> lista de mensagens da conversa
memory: Dict[str, List[dict]] = {}



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
            "description": "Cancela o último agendamento salvo pelo cliente logado atual.",
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
                
            return json.dumps({"error": "Ferramenta inexistente"})
            
        except Exception as e:
            return json.dumps({"error": str(e)})

@app.post("/webhook/whatsapp/{api_key}")
async def whatsapp_webhook(api_key: str, payload: dict):
    # A estrutura depende muito se é ZAPI, EvolutionAPI ou Zenvia Padrão
    # Seguindo o cURL do documento: {"from": "5511...", "message": "ola!"}
    from_number = payload.get("from")
    message = payload.get("message")
    
    if not from_number or not message:
        raise HTTPException(status_code=400, detail="Missing 'from' or 'message' property in JSON payload")
        
    # Inicializa memória da conversa se for a primeira vez
    if from_number not in memory:
        from datetime import datetime
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = f"""Você é um assistente virtual atencioso que faz agendamentos via WhatsApp.
Data e Hora atual: {agora}. Use isso como referência inflexível ao lidar com datas (ex: se o cliente pedir para 'amanhã', veja a data de hoje e some 1 dia. Se pedir para daqui x dias, adicione e transforme em YYYY-MM-DD).

O telefone do cliente está embutido. Seu objetivo é agendar o serviço de forma RÁPIDA e EFICIENTE.
NUNCA seja repetitivo. Se o cliente já fornecer as informações de serviço e horario, NÃO FAÇA novas perguntas; apenas certifique-se que você tenha o ID do serviço usando `ver_servicos` silenciosamente se ele não disse antes.

PASSO A PASSO DA CONVERSA (Execute passos condensados se possível):
1. Identificação: Pergunte o nome do cliente.
2. Serviço: Descubra o serviço lendo `ver_servicos` e ofereça os profissionais listados.
3. Data/Hora: Chame `ver_horarios_ocupados` para checar disponibilidade de vaga para a data do cliente. Se vier 'horarios_ocupados', você deve oferecer os horários restantes da loja.
4. Confirmação: Resuma.
5. Agendamento: Chame `criar_agendamento`.
6. Conclusão: Avise e chame `sincronizar_google`.
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
            return {"response": final_msg}
            
        else:
            final_msg = response_message.content
            memory[from_number].append({"role": "assistant", "content": final_msg})
            return {"response": final_msg}
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
