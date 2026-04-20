"""
Belchior Bot - Main Application
LLM-based WhatsApp bot using FastAPI + Redis
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
import redis
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Carrega variáveis do .env
load_dotenv()

app = FastAPI(title="Belchior Bot", version="2.0.0")

# Inicializa cliente Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Inicializa Redis
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "192.168.0.12"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD", "2323"),
    decode_responses=True
)

# Modelo de entrada
class MessageRequest(BaseModel):
    user_id: str
    message: str

# Modelo de saída
class MessageResponse(BaseModel):
    user_id: str
    response: str
    timestamp: str

@app.get("/health")
def health_check():
    """Verifica saúde do bot"""
    try:
        redis_client.ping()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"disconnected: {str(e)}"
    
    return {
        "status": "ok",
        "version": "2.0.0",
        "redis": redis_status
    }

@app.post("/chat")
def chat(request: MessageRequest) -> MessageResponse:
    """
    Processa mensagem do usuário
    Armazena histórico no Redis
    """
    try:
        # Chave do histórico
        history_key = f"chat_history:{request.user_id}"
        
        # Pega histórico do Redis
        history_json = redis_client.get(history_key)
        history = json.loads(history_json) if history_json else []
        
        # Adiciona mensagem do usuário
        history.append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Limita a 20 mensagens (contexto)
        if len(history) > 20:
            history = history[-20:]
        
        # Prepara mensagens pro Groq
        messages_for_groq = [
            {
                "role": "system",
                "content": "Você é um assistente útil e amigável chamado Belchior. Responda em português brasileiro de forma concisa (máximo 2-3 linhas). Seja direto e prático."
            }
        ]
        
        # Adiciona histórico (sem timestamps)
        for msg in history:
            messages_for_groq.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Chama Groq/Llama
        completion = groq_client.chat.completions.create(
            model=groq_model,
            messages=messages_for_groq,
            max_tokens=150,
            temperature=0.7,
        )
        
        response_text = completion.choices[0].message.content
        
        # Adiciona resposta ao histórico
        history.append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Salva histórico no Redis (24 horas de expiração)
        redis_client.setex(
            history_key,
            86400,
            json.dumps(history)
        )
        
        return MessageResponse(
            user_id=request.user_id,
            response=response_text,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{user_id}")
def get_history(user_id: str):
    """Retorna histórico de um usuário"""
    try:
        history_key = f"chat_history:{user_id}"
        history_json = redis_client.get(history_key)
        history = json.loads(history_json) if history_json else []
        
        return {
            "user_id": user_id,
            "messages": history,
            "total": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/history/{user_id}")
def clear_history(user_id: str):
    """Limpa histórico de um usuário"""
    try:
        history_key = f"chat_history:{user_id}"
        redis_client.delete(history_key)
        
        return {
            "user_id": user_id,
            "message": "Histórico deletado com sucesso"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 8001))
    
    uvicorn.run(app, host=host, port=port)
