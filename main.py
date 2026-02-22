from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import base64
import qrcode
import io

app = FastAPI(
    title="API de Tokenización de Transferencias (Chile)",
    description="Microservicio para empaquetar datos bancarios chilenos en tokens y QRs.",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DatosBancarios(BaseModel):
    nombre: str  # <--- ¡AQUÍ AGREGAMOS EL NOMBRE!
    rut: str
    banco: str
    tipoCuenta: str
    numeroCuenta: str
    correo: str
    asunto: str

class PeticionToken(BaseModel):
    token: str

@app.post("/api/v1/generar-token", tags=["Generación"])
async def generar_token(datos: DatosBancarios):
    try:
        texto_json = json.dumps(datos.model_dump())
        token_bytes = base64.urlsafe_b64encode(texto_json.encode('utf-8'))
        token_str = token_bytes.decode('utf-8')
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(token_str)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        return {
            "token": token_str,
            "qr_imagen": f"data:image/png;base64,{qr_base64}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/interpretar-token", tags=["Decodificación"])
async def interpretar_token(peticion: PeticionToken):
    try:
        token_pegado = peticion.token
        padding = 4 - (len(token_pegado) % 4)
        if padding != 4:
            token_pegado += "=" * padding

        bytes_decodificados = base64.urlsafe_b64decode(token_pegado)
        return json.loads(bytes_decodificados.decode('utf-8'))
    except Exception:
        raise HTTPException(status_code=400, detail="Token corrupto o inválido.")