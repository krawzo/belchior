"""
Belchior Bot - Main Application
LLM-based WhatsApp bot using FastAPI
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

app = FastAPI(title="Belchior Bot", version="1.0.0")

# Inicializa cliente Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Modelo de entrada (o que WhatsApp manda pra gente)
class MessageRequest(BaseModel):
    user_id: str
    message: str

# Modelo de saída (o que a gente manda de volta)
class MessageResponse(BaseModel):
    user_id: str
    response: str

@app.get("/health")
def health_check():
    """Verifica se o bot tá rodando"""
    return {"status": "ok", "version": "1.0.0"}

@app.post("/chat")
def chat(request: MessageRequest) -> MessageResponse:
    """
    Processa mensagem do usuário e retorna resposta da IA
    """
    try:
        # Chama Groq/Llama
        completion = groq_client.chat.completions.create(
            model=groq_model,
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente útil e amigável. Responda em português brasileiro de forma concisa e clara."
                },
                {
                    "role": "user",
                    "content": request.message
                }
            ],
            max_tokens=200,  # Limita resposta (pra não ficar muito longa)
            temperature=0.7,  # Um pouco criativo mas não demais
        )
        
        # Extrai resposta
        response_text = completion.choices[0].message.content
        
        return MessageResponse(
            user_id=request.user_id,
            response=response_text
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 8000))
    
    uvicorn.run(app, host=host, port=port)
