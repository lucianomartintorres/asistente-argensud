from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import openai
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Habilitar CORS para que se pueda acceder desde Wix u otros orígenes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar el archivo Excel
df = pd.read_excel("Argensud_Menu_12.xlsx")

# Función para normalizar texto
def normalizar(texto):
    if pd.isna(texto):
        return ""
    return str(texto).strip().lower() \
        .replace("á", "a").replace("é", "e") \
        .replace("í", "i").replace("ó", "o").replace("ú", "u")

# Endpoint para búsqueda filtrada de platos
@app.get("/buscar_platos")
def buscar_platos(filtros: list[str] = Query(default=[])):
    resultados = []
    for _, fila in df.iterrows():
        texto_busqueda = (
            normalizar(fila.get("Sección", "")) + " " +
            normalizar(fila.get("Alias", "")) + " " +
            normalizar(fila.get("Tags", ""))
        )
        if all(normalizar(palabra) in texto_busqueda for palabra in filtros):
            resultados.append({
                "nombre": fila.get("Nombre del plato", "").strip(),
                "descripcion": fila.get("Descripción", ""),
                "precio": fila.get("Precio ($)", ""),
                "id": fila.get("ID", "")
            })
    return {"platos": resultados}

# Clase para recibir el mensaje del usuario en /chat
class ChatInput(BaseModel):
    message: str

# Endpoint para diálogo con OpenAI
@app.post("/chat")
def chat(input: ChatInput):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    respuesta = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Sos un mozo muy simpático del restaurante Argensud. Solo podés hablar del menú, historia del edificio y turismo de San Julián. No inventes platos ni respondas cosas que no sepas."},
            {"role": "user", "content": input.message}
        ]
    )
    return {"respuesta": respuesta.choices[0].message.content}
