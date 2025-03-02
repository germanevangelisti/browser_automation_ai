from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import BrowserAgent
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
import os
import httpx
from fastapi.responses import StreamingResponse
import asyncio
import base64
import io

load_dotenv()


class CommandRequest(BaseModel):
    command: str = ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    await agent.start_browser()
    yield
    await agent.close()


app = FastAPI(lifespan=lifespan)
agent = BrowserAgent()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar directorio de screenshots como estático
os.makedirs("screenshots", exist_ok=True)
app.mount("/screenshots", StaticFiles(directory="screenshots"), name="screenshots")


@app.post("/execute/")
async def execute_command(request: CommandRequest):
    response = await agent.execute_from_text(request.command)
    await agent.screenshot()
    return {"command": request.command, "response": response}


@app.get("/debug-url/")
async def get_debug_url():
    # Tomar captura de pantalla actualizada
    await agent.screenshot()
    return {"debug_url": agent.browser.debug_url}


@app.get("/browser-proxy/{path:path}")
async def browser_proxy(path: str, request: Request):
    """Proxy para el depurador de Chrome"""
    target_url = f"http://localhost:9222/{path}"
    
    # Obtener parámetros de consulta
    params = dict(request.query_params)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(target_url, params=params, follow_redirects=True)
        
    return StreamingResponse(
        content=response.aiter_bytes(),
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@app.websocket("/ws/browser")
async def websocket_browser(websocket: WebSocket):
    await websocket.accept()
    
    # Mantener la conexión activa mientras enviamos capturas
    try:
        while True:
            # Tomar captura de pantalla
            screenshot_bytes = await agent.browser.page.screenshot(type="jpeg", quality=70)
            
            # Codificar en base64 para enviar como texto a través de WebSocket
            base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Enviar al cliente
            await websocket.send_text(base64_screenshot)
            
            # Esperar un poco antes de enviar la siguiente captura
            await asyncio.sleep(0.2)  # 5 FPS aproximadamente
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
