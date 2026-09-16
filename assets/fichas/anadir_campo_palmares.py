#Añado palmares si el ciclista tiene archivo .txt con su palmares

import json
import re
from pathlib import Path

# Directorios de trabajo
CARPETA_TXT_PALMARES = Path("./ciclistas/palmares")
CARPETA_CICLISTAS = Path("./ciclistas")

def parsear_texto_palmares(contenido_txt):
    """
    Convierte el texto plano del palmarés en un diccionario Python
    organizado por años, dividiendo frases compuestas del tipo 'A, más B'.
    """
    palmares_dict = {}
    anio_actual = None

    lineas = contenido_txt.splitlines()
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue

        # Ignorar cabeceras sueltas si las hubiera
        if linea.lower() in ["palmarés", "palmares"]:
            continue

        # Comprobar si la línea es un año (ej. 2014, 2025)
        if re.match(r"^\d{4}$", linea):
            anio_actual = linea
            if anio_actual not in palmares_dict:
                palmares_dict[anio_actual] = []
        elif anio_actual:
            # Procesar frases con "más" (ej. "Tour de Polonia, más 2 etapas")
            if " más " in linea:
                partes = linea.split(" más ")
                for parte in partes:
                    parte_limpia = parte.strip()
                    if parte_limpia:
                        palmares_dict[anio_actual].append(parte_limpia)
            else:
                palmares_dict[anio_actual].append(linea)

    return palmares_dict

def actualizar_palmares_ciclistas():
    if not CARPETA_TXT_PALMARES.exists():
        print(f"Error: La carpeta de textos '{CARPETA_TXT_PALMARES}' no existe.")
        return

    if not CARPETA_CICLISTAS.exists():
        print(f"Error: La carpeta de ciclistas '{CARPETA_CICLISTAS}' no existe.")
        return

    archivos_txt = list(CARPETA_TXT_PALMARES.glob("*.txt"))
    print(f"Se encontraron {len(archivos_txt)} archivos TXT de palmarés.")

    actualizados = 0
    no_encontrados = 0

    for archivo_txt in archivos_txt:
        # El nombre del archivo txt es el id del ciclista (ej. rafal_majka.txt -> id: rafal_majka)
        id_ciclista = archivo_txt.stem
        archivo_json = CARPETA_CICLISTAS / f"{id_ciclista}.json"

        if not archivo_json.exists():
            print(f"Aviso: No se encontró el archivo JSON para '{id_ciclista}' en {archivo_json}")
            no_encontrados += 1
            continue

        try:
            # 1. Leer el contenido del txt del palmarés
            with open(archivo_txt, "r", encoding="utf-8") as f:
                contenido_txt = f.read()

            # 2. Parsear el texto a un diccionario de palmarés estructurado
            nuevo_palmares = parsear_texto_palmares(contenido_txt)

            # 3. Abrir el JSON del ciclista
            with open(archivo_json, "r", encoding="utf-8") as f:
                datos_ciclista = json.load(f)

            # 4. Actualizar o crear el campo palmares
            datos_ciclista["palmares"] = nuevo_palmares

            # 5. Guardar los cambios en el JSON del ciclista manteniendo formato ordenado
            with open(archivo_json, "w", encoding="utf-8") as f:
                json.dump(datos_ciclista, f, ensure_ascii=False, indent=4)

            print(f"-> Palmarés actualizado con éxito para: {id_ciclista}")
            actualizados += 1

        except Exception as e:
            print(f"Error procesando al ciclista {id_ciclista}: {e}")

    print("\n--- PROCESO FINALIZADO ---")
    print(f"Ciclistas actualizados correctamente: {actualizados}")
    print(f"Archivos JSON no encontrados: {no_encontrados}")

if __name__ == "__main__":
    actualizar_palmares_ciclistas()
