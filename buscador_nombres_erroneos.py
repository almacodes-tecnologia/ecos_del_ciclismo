import json
import os
import unicodedata
from collections import defaultdict

def limpiar_texto(texto):
    if not texto: return ""
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode("utf-8")
    return texto.lower().strip()

def generar_id_ciclista(nombre):
    nombre_limpio = limpiar_texto(nombre)
    palabras = nombre_limpio.replace(",", "").split()
    palabras.sort()
    return "_".join(palabras)

def buscar_nombres_invertidos(ruta_base):
    # Diccionario: { id_unico: { "nombres_vistos": { "Nombre Original": [ficheros] } } }
    registro_ids = defaultdict(lambda: defaultdict(list))

    if not os.path.exists(ruta_base):
        print(f"Error: La carpeta {ruta_base} no existe.")
        return

    # 1. Escaneo de todos los ficheros
    for carrera_id in os.listdir(ruta_base):
        ruta_carrera = os.path.join(ruta_base, carrera_id)
        if "_old" in carrera_id or not os.path.isdir(ruta_carrera):
            continue

        for archivo_json in os.listdir(ruta_carrera):
            if not archivo_json.endswith(".json"):
                continue
            
            ruta_completa = os.path.join(ruta_carrera, archivo_json)
            try:
                with open(ruta_completa, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extraer nombres de todas las fuentes posibles del JSON
                    nombres_en_fichero = []
                    if "clasificacionGeneral" in data:
                        nombres_en_fichero.extend([r.get("nombre") for r in data["clasificacionGeneral"]])
                    if "etapas" in data:
                        for e in data["etapas"]:
                            nombres_en_fichero.append(e.get("nombre"))
                    
                    for nombre in nombres_en_fichero:
                        if nombre:
                            cid = generar_id_ciclista(nombre)
                            # Guardamos el nombre tal cual aparece y su ubicación
                            ubicacion = f"{carrera_id}/{archivo_json}"
                            if ubicacion not in registro_ids[cid][nombre]:
                                registro_ids[cid][nombre].append(ubicacion)

            except Exception as e:
                print(f"ARCHIVO CORRUPTO: {ruta_completa}")
                print(f"DETALLE DEL ERROR: {e}\n")

    # 2. Análisis de discrepancias
    print("\n" + "="*60)
    print("REPORTE DE NOMBRES INVERTIDOS O DISCORDANTES")
    print("="*60 + "\n")

    encontrados = False
    for cid, variantes in registro_ids.items():
        # Si un ID tiene más de una forma de escribirse (ej: 'tadej pogacar' y 'pogacar tadej')
        if len(variantes) > 1:
            encontrados = True
            print(f"ID ÚNICO DETECTADO: {cid}")
            for nombre_original, archivos in variantes.items():
                print(f"  - Escrito como: \"{nombre_original}\"")
                print(f"    Encontrado en: {', '.join(archivos)}")
            print("-" * 40)

    if not encontrados:
        print("No se han encontrado nombres invertidos. ¡Tu base de datos está limpia!")

if __name__ == "__main__":
    ruta_historial = "./assets/historial"
    buscar_nombres_invertidos(ruta_historial)