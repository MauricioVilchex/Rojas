import os
from flask import Flask, request, render_template
from PIL import Image
import openai
import io
import uuid

app = Flask(__name__)

# ---------------------------------------------------------
# 1) CONFIGURAR TU API KEY DE OPENAI
# ---------------------------------------------------------
# Antes de arrancar el servidor, en Replit (o donde sea que despliegues)
# debes crear una variable de entorno llamada OPENAI_API_KEY con tu clave.
openai.api_key = os.getenv("OPENAI_API_KEY")

# ---------------------------------------------------------
# 2) Carpeta donde guardaremos imágenes temporales
# ---------------------------------------------------------
OUTPUT_FOLDER = "/tmp"
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        # Simplemente mostrar el formulario HTML
        return render_template("index.html")

    # Si es POST, procesamos la(s) imagen(es)
    archivos = request.files.getlist("imagenes")
    if not archivos or len(archivos) == 0:
        return render_template("index.html", error="No se seleccionaron imágenes.")

    resultado_urls = []  # Lista donde guardaremos cada URL de resultado

    # Este es el prompt fijo que se aplicará a todas las imágenes:
    prompt_fijo = (
        "Pudes copiar o inspirate de esta imagen sin derechos de autor de un diseño de tatuaje "
        "vertical, centrado y sin tocar los bordes de la imagen para que no se corte el diseño, "
        "utilizando una paleta en blanco y negro con contraste suave con detalles en rojo intenso. "
        "El fondo es completamente blanco con grises muy claros; puede ser rayos de luz blancos, "
        "nubes blancas, olas japonesas blancas, naturaleza, arabescos blancos o geometría blanca "
        "atrás del diseño; escoge uno de esos para crear armonía con el diseño. "
        "Las sombras se trabajan con técnicas que imitan carboncillo o aerógrafo."
    )

    # Recorremos cada archivo subido
    for archivo in archivos:
        try:
            # 3.1) Leer la imagen en memoria
            img_bytes = archivo.read()
            img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
        except Exception as e:
            print(f"Error al leer {archivo.filename}: {e}")
            continue  # Saltar esta imagen y seguir con la siguiente

        # 3.2) Crear una máscara completamente blanca del mismo tamaño
        mask = Image.new("RGBA", img.size, (255, 255, 255, 255))

        # 3.3) Generar nombres únicos para guardar estos archivos temporalmente
        uid = str(uuid.uuid4())
        original_path = os.path.join(OUTPUT_FOLDER, f"orig_{uid}.png")
        mask_path     = os.path.join(OUTPUT_FOLDER, f"mask_{uid}.png")

        # 3.4) Guardar la imagen original y la máscara en /tmp
        img.save(original_path)
        mask.save(mask_path)

        # 3.5) Llamar a la API de OpenAI para editar la imagen
        try:
            response = openai.Image.create_edit(
                image=open(original_path, "rb"),
                mask=open(mask_path, "rb"),
                prompt=prompt_fijo,
                n=1,
                size="1024x1024"
            )
        except Exception as api_err:
            print(f"Error en API con {archivo.filename}: {api_err}")
            continue  # Saltar esta imagen y seguir con la siguiente

        # 3.6) Extraer la URL resultante y guardarla
        url_salida = response["data"][0]["url"]
        resultado_urls.append(url_salida)

    # Si no obtuvimos ninguna URL, devolvemos un mensaje de error al HTML
    if len(resultado_urls) == 0:
        return render_template("index.html", error="Ocurrió un error procesando las imágenes.")

    # De lo contrario, pasamos la lista de URLs al template para mostrarlas
    return render_template("index.html", resultado_urls=resultado_urls)


if __name__ == "__main__":
    # Replit inyecta la variable PORT automáticamente; si no, usamos 5000
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
