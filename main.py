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
        for plato in resultados[:5]:
            texto_respuesta += f"- {plato['nombre']}: {plato['descripcion']} (${plato['precio']})\n"
        return {"respuesta": texto_respuesta.strip()}

    return {"respuesta": "No encontré opciones con esas palabras. Podés decirme si querés algo con pescado, carne, sin TACC o bebidas."}
