from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

df = pd.read_excel("Argensud_Menu_12.xlsx")

def normalizar(texto):
    if pd.isna(texto):
        return ""
    return str(texto).strip().lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

class RequestData(BaseModel):
    mensaje: str

# Memoria temporal por IP
ultima_mencion = {}

@app.post("/chat")
def chat(request: Request, data: RequestData):
    mensaje = normalizar(data.mensaje)
    ip = request.client.host
    ultima_mencion_plato = ultima_mencion.get(ip)

    if not mensaje:
        return {"respuesta": "¿Podés repetir tu pregunta?"}

    # SALUDOS
    saludos = ["hola", "buenas", "qué tal", "buen día", "buenas noches", "cómo estás"]
    if any(saludo in mensaje for saludo in saludos):
        return {"respuesta": "¡Hola! ¿Querés que te muestre algunas opciones de nuestra carta? Podés decirme si tenés ganas de picar algo, comer carne, una pizza o tomar algo."}

    # DESCRIPCIÓN
    if any(p in mensaje for p in ["más info", "detalle", "descripción", "qué trae", "qué tiene"]):
        if ultima_mencion_plato:
            return {"respuesta": f"Te cuento: {ultima_mencion_plato['descripcion']} 😊\n¿Querés saber el precio o te sugiero algo más?"}
        else:
            return {"respuesta": "¿De qué plato querés que te cuente? Podés decirme el nombre y te doy los detalles."}

    # PRECIO
    if any(p in mensaje for p in ["precio", "cuánto", "vale", "sale"]):
        if ultima_mencion_plato:
            return {"respuesta": f"El precio es ${ultima_mencion_plato['precio']} 😉\n¿Querés que te sugiera otro similar o algo para acompañar?"}
        else:
            return {"respuesta": "Decime el nombre del plato y te digo el precio."}

    # BUSQUEDA DE PLATOS
    resultados = []
    for _, fila in df.iterrows():
        texto_busqueda = (
            normalizar(fila.get("Sección", "")) + " " +
            normalizar(fila.get("Alias", "")) + " " +
            normalizar(fila.get("Tags", "")) + " " +
            normalizar(fila.get("Nombre del plato", ""))
        )
        if any(palabra in texto_busqueda for palabra in mensaje.split()):
            resultados.append({
                "nombre": fila.get("Nombre del plato", "").strip(),
                "descripcion": fila.get("Descripción", ""),
                "precio": fila.get("Precio ($)", ""),
                "id": fila.get("ID", "")
            })

    if resultados:
        ultima_mencion[ip] = resultados[0]
        nombres = [f"- {plato['nombre']}" for plato in resultados[:5]]
        texto_respuesta = "Mirá estas opciones que encontré para vos:\n\n" + "\n".join(nombres)
        texto_respuesta += "\n\n¿Querés que te cuente más sobre alguno? O si querés, te sugiero algo según lo que tengas ganas 😄"
        return {"respuesta": texto_respuesta.strip()}

    # SUGERENCIAS SI NO ENCUENTRA
    sugerencias = {
        "carne": "¿Te interesan milanesas, bifes o alguna tabla para compartir?",
        "mariscos": "Podés probar algo con langostinos o centolla. ¿Querés que te muestre?",
        "pizza": "Tenemos varias opciones de pizza, incluso para compartir. ¿Querés verlas?",
        "sin tacc": "Tenemos opciones sin TACC para que disfrutes tranquilo. ¿Querés que te las muestre?",
        "postre": "Tenemos torta vasca, helado y otros postres. ¿Querés algo dulce para el final?"
    }

    for clave, sugerencia in sugerencias.items():
        if clave in mensaje:
            return {"respuesta": sugerencia}

    return {"respuesta": "No encontré nada con esas palabras 😓. Probá diciendo algo como carne, pizza, postre o bebida."}
