import json
import os

# --------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------
RESOLUCION = 0.1  # km (100 metros)

# --------------------------------------------
# PEDIR ARCHIVO
# --------------------------------------------
archivo = input("Archivo JSON: ").strip()

if archivo == "":
    archivo = "puerto.json"

if not os.path.exists(archivo):
    print("No existe ese archivo.")
    exit()

salida = archivo.replace(".json", "_interpolado.json")

# --------------------------------------------
# CARGAR JSON
# --------------------------------------------
with open(archivo, "r", encoding="utf-8") as f:
    datos = json.load(f)

puntos = datos["altimetria_puntos"]

resultado = []

# --------------------------------------------
# INTERPOLAR
# --------------------------------------------
for i in range(len(puntos) - 1):

    p1 = puntos[i]
    p2 = puntos[i + 1]

    km1 = p1["kilometro"]
    km2 = p2["kilometro"]

    alt1 = p1["altitud"]
    alt2 = p2["altitud"]

    distancia = km2 - km1

    km = km1

    while km < km2 - 1e-6:

        t = (km - km1) / distancia

        alt = round(alt1 + (alt2 - alt1) * t)

        resultado.append({
            "kilometro": round(km, 1),
            "altitud": alt
        })

        km += RESOLUCION

# Añadir el último punto original
resultado.append(puntos[-1])

datos["altimetria_puntos"] = resultado

# --------------------------------------------
# GUARDAR
# --------------------------------------------
with open(salida, "w", encoding="utf-8") as f:
    json.dump(datos, f, indent=2, ensure_ascii=False)

print()
print(f"Puntos originales : {len(puntos)}")
print(f"Puntos generados  : {len(resultado)}")
print(f"Guardado en       : {salida}")