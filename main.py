from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
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
    return str(texto).strip().lower().replace("á", "a").replace(
        "é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")


# Crear endpoint que filtra por palabras clave
@app.get("/buscar_platos")
def buscar_platos(filtros: list[str] = Query(default=[])):
    resultados = []

    for _, fila in df.iterrows():
        texto_busqueda = (normalizar(fila.get("Sección", "")) + " " +
                          normalizar(fila.get("Alias", "")) + " " +
                          normalizar(fila.get("Tags", "")))

        if all(normalizar(palabra) in texto_busqueda for palabra in filtros):
            resultados.append({
                "nombre":
                fila.get("Nombre del plato", "").strip(),
                "descripcion":
                fila.get("Descripción", ""),
                "precio":
                fila.get("Precio ($)", ""),
                "id":
                fila.get("ID", "")
            })

    return {"platos": resultados}
