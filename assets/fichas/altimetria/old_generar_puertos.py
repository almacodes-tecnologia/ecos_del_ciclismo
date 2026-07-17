import xml.etree.ElementTree as ET
import json
import math
import os
import re

CARPETA_GPX = "gpx"
CARPETA_JSON = "json"
INTERVALO_ALTITUD = 100 

os.makedirs(CARPETA_JSON, exist_ok=True)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return R * 2 * math.asin(math.sqrt(a))

def limpiar_id(nombre):
    return re.sub(r"[^a-z0-9]+", "_", nombre.lower()).strip("_")

def interpolar_altitud(puntos, distancia):
    for i in range(1, len(puntos)):
        if puntos[i]["dist"] >= distancia:
            p1, p2 = puntos[i-1], puntos[i]
            if p2["dist"] == p1["dist"]: return p1["ele"]
            porcentaje = (distancia - p1["dist"]) / (p2["dist"] - p1["dist"])
            return p1["ele"] + (p2["ele"] - p1["ele"]) * porcentaje
    return puntos[-1]["ele"]

def procesar_gpx(archivo):
    print("Procesando:", archivo)
    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}
    tree = ET.parse(archivo)
    root = tree.getroot()

    nombre = root.find("gpx:metadata/gpx:name", ns)
    nombre_puerto = nombre.text if nombre is not None else os.path.basename(archivo)
    
    trkpts = root.findall(".//gpx:trkpt", ns)
    puntos = []
    distancia = 0
    for i, pt in enumerate(trkpts):
        lat = float(pt.attrib["lat"])
        lon = float(pt.attrib["lon"])
        ele = float(pt.find("gpx:ele", ns).text)
        if i > 0:
            distancia += haversine(puntos[-1]["lat"], puntos[-1]["lon"], lat, lon)
        puntos.append({"dist": distancia, "lat": lat, "lon": lon, "ele": ele})

    # 1. Perfil base (sin suavizar) para cálculos técnicos
    datos_crudos = []
    d_actual = 0
    while d_actual <= distancia:
        datos_crudos.append({"km": d_actual/1000, "ele": interpolar_altitud(puntos, d_actual)})
        d_actual += INTERVALO_ALTITUD

    # 2. Cálculos estadísticos (sobre datos crudos)
    pendiente_media = ((datos_crudos[-1]["ele"] - datos_crudos[0]["ele"]) / distancia) * 100
    
    # Umbral dinámico
    if pendiente_media < 5: umbral = 8
    elif pendiente_media < 7: umbral = 10
    elif pendiente_media < 9: umbral = 12
    elif pendiente_media < 11: umbral = 14
    else: umbral = 16

    pendiente_maxima = 0
    candidatos_clave = []
    
    for i in range(5, len(datos_crudos)):
        # Pendiente máxima (200m)
        p_max = ((datos_crudos[i]["ele"] - datos_crudos[i-2]["ele"]) / 200) * 100
        pendiente_maxima = max(pendiente_maxima, p_max)
        
        # Puntos clave (500m)
        p_clave = ((datos_crudos[i]["ele"] - datos_crudos[i-5]["ele"]) / 500) * 100
        if p_clave >= umbral:
            # Cálculo del punto medio de forma segura (usando índices enteros)
            # El punto medio entre i y i-5 es i - 2.5, 
            # pero para acceder al km usamos el promedio de los valores de km
            km_centro = (datos_crudos[i]["km"] + datos_crudos[i-5]["km"]) / 2
            
            candidatos_clave.append({
                "kilometro": round(km_centro, 2),
                "pendiente_porcentaje": round(p_clave, 1),
                "altitud": round((datos_crudos[i]["ele"] + datos_crudos[i-5]["ele"]) / 2),
                "nombre": f"Rampa {round(p_clave, 1)}%"
            })

    # 3. Filtrado y agrupación de puntos clave
    grupos = {}
    for c in candidatos_clave:
        km_idx = math.floor(c["kilometro"] + 0.5)
        if km_idx not in grupos or c["pendiente_porcentaje"] > grupos[km_idx]["pendiente_porcentaje"]:
            grupos[km_idx] = c
            
    puntos_clave = sorted(grupos.values(), key=lambda x: x["pendiente_porcentaje"], reverse=True)[:6]
    puntos_clave.sort(key=lambda x: x["kilometro"])
    # Asignar nombre final
    for p in puntos_clave:
        p["nombre"] = f"Rampa {p['pendiente_porcentaje']}%"

    # 4. Suavizado (Solo para visualización en gráfico)
    altimetria_visual = []
    for i in range(len(datos_crudos)):
        inicio = max(0, i - 2)
        fin = min(len(datos_crudos), i + 3)
        altimetria_visual.append({
            "kilometro": round(i * 0.1, 2),
            "altitud": round(sum(d["ele"] for d in datos_crudos[inicio:fin]) / (fin - inicio))
        })

    resultado = {
        "id": limpiar_id(nombre_puerto),
        "nombre": nombre_puerto,
        "longitud_km": round(distancia / 1000, 2),
        "pendiente_media_porcentaje": round(pendiente_media, 1),
        "pendiente_maxima_porcentaje": round(pendiente_maxima, 1),
        "altimetria_puntos": altimetria_visual,
        "puntos_clave": puntos_clave
    }
    
    salida = os.path.join(CARPETA_JSON, limpiar_id(nombre_puerto) + ".json")
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print("Generado:", salida)

for archivo in os.listdir(CARPETA_GPX):
    if archivo.lower().endswith(".gpx"):
        procesar_gpx(os.path.join(CARPETA_GPX, archivo))