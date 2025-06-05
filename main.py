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

# Nuevo endpoint estilo conversacional
@app.post("/chat")
def chat(request: RequestData):
    texto = normalizar(request.mensaje)

    if not texto:
        return {"respuesta": "¿Podés repetir tu pregunta?"}

    saludos = ["hola", "buenas", "qué tal", "buen día", "buenas noches", "cómo estás"]
    if any(saludo in texto for saludo in saludos):
        return {"respuesta": "¡Hola! ¿Querés que te muestre algunas opciones de nuestra carta? Podés decirme si tenés ganas de picar algo, comer carne, una pizza o tomar algo."}

    if any(palabra in texto for palabra in ["más info", "detalle", "descripción", "qué trae", "qué tiene"]):
        return {"respuesta": "¿De qué plato te gustaría que te cuente más? Podés decirme el nombre y te doy los detalles 😊"}

    if any(palabra in texto for palabra in ["precio", "cuánto", "vale", "sale"]):
        return {"respuesta": "Decime el nombre del plato y te digo el precio 😉"}

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
        nombres = [f"- {plato['nombre']}" for plato in resultados[:5]]
        texto_respuesta = "Mirá estas opciones que encontré para vos:\n\n" + "\n".join(nombres)
        texto_respuesta += "\n\n¿Querés que te cuente más sobre alguno? O si querés, te sugiero algo según lo que tengas ganas 😄"
        return {"respuesta": texto_respuesta.strip()}

    return {"respuesta": "No encontré nada con esas palabras 😓. Probá diciendo algo como carne, pizza, postre o bebida."}
