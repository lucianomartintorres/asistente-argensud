from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Permitir CORS para que se pueda acceder desde Wix o cualquier frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar el archivo Excel al iniciar
df = pd.read_excel("Argensud_Menu_12.xlsx")

# Normalización de texto
def normalizar(texto):
    if pd.isna(texto):
        return ""
    return str(texto).strip().lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

# Endpoint antiguo (para filtros exactos)
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

# Modelo para /chat
class RequestData(BaseModel):
    mensaje: str

# Endpoint nuevo estilo chat
@app.post("/chat")
def chat(request: RequestData):
    texto = normalizar(request.mensaje)
    respuesta = ""

    if not texto:
        return {"respuesta": "¿Podés repetir tu pregunta?"}

    saludos = ["hola", "buenas", "qué tal", "buen día", "buenas noches", "cómo estás"]
    if any(saludo in texto for saludo in saludos):
        return {"respuesta": "¡Hola! ¿Querés ver algo de la carta? Podés decirme si buscás carne, pizzas, bebidas o postres."}

    resultados = []
    for _, fila in df.iterrows():
        texto_busqueda = (
            normalizar(fila.get("Sección", "")) + " " +
            normalizar(fila.get("Alias", "")) + " " +
            normalizar(fila.get("Tags", ""))
        )
        if any(palabra in texto_busqueda for palabra in texto.split()):
            resultados.append({
                "nombre": fila.get("Nombre del plato", "").strip(),
                "descripcion": fila.get("Descripción", ""),
                "precio": fila.get("Precio ($)", ""),
                "id": fila.get("ID", "")
            })

    if resultados:
        texto_respuesta = "Acá te paso algunas opciones que encontré:\n\n"
        for plato in resultados[:5]:  # Máximo 5 respuestas para no saturar
            texto_respuesta += f"- {plato['nombre']}: {plato['descripcion']} (${plato['precio']})\n"
        return {"respuesta": texto_respuesta.strip()}

    return {"respuesta": "No encontré opciones con esas palabras. Podés decirme si estás buscando carne, pescado, sin TACC o bebidas."}
