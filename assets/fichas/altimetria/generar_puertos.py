import xml.etree.ElementTree as ET
import json
import math
import os
import re


CARPETA_GPX = "gpx"
CARPETA_JSON = "json"

INTERVALO_ALTITUD = 100   # metros


os.makedirs(CARPETA_JSON, exist_ok=True)



def haversine(lat1, lon1, lat2, lon2):

    R = 6371000

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2)**2 +
        math.cos(lat1) *
        math.cos(lat2) *
        math.sin(dlon / 2)**2
    )

    return R * 2 * math.asin(math.sqrt(a))



def limpiar_id(nombre):

    nombre = nombre.lower()

    nombre = re.sub(
        r"[^a-z0-9]+",
        "_",
        nombre
    )

    return nombre.strip("_")



def interpolar_altitud(puntos, distancia):

    for i in range(1, len(puntos)):

        if puntos[i]["dist"] >= distancia:

            p1 = puntos[i-1]
            p2 = puntos[i]


            if p2["dist"] == p1["dist"]:
                return p1["ele"]


            porcentaje = (
                distancia - p1["dist"]
            ) / (
                p2["dist"] - p1["dist"]
            )


            return (
                p1["ele"] +
                (p2["ele"] - p1["ele"])
                * porcentaje
            )


    return puntos[-1]["ele"]




def procesar_gpx(archivo):

    print("Procesando:", archivo)


    ns = {
        "gpx":
        "http://www.topografix.com/GPX/1/1"
    }


    tree = ET.parse(archivo)
    root = tree.getroot()


    nombre = root.find(
        "gpx:metadata/gpx:name",
        ns
    )


    if nombre is not None:
        nombre = nombre.text
    else:
        nombre = os.path.basename(archivo)



    trkpts = root.findall(
        ".//gpx:trkpt",
        ns
    )


    puntos = []

    distancia = 0


    for i, pt in enumerate(trkpts):

        lat = float(pt.attrib["lat"])
        lon = float(pt.attrib["lon"])
        ele = float(
            pt.find("gpx:ele", ns).text
        )


        if i > 0:

            anterior = puntos[-1]

            distancia += haversine(
                anterior["lat"],
                anterior["lon"],
                lat,
                lon
            )


        puntos.append(
            {
                "dist": distancia,
                "lat": lat,
                "lon": lon,
                "ele": ele
            }
        )



    longitud_km = distancia / 1000


    altura_inicio = puntos[0]["ele"]

    altura_maxima = max(
        p["ele"] for p in puntos
    )


    desnivel = altura_maxima - altura_inicio


    pendiente_media = (
        desnivel / distancia * 100
    )



    pendiente_maxima = 0


    for i in range(1, len(puntos)):

        metros = (
            puntos[i]["dist"]
            -
            puntos[i-1]["dist"]
        )

        if metros > 5:

            pendiente = (
                (puntos[i]["ele"]
                 -
                 puntos[i-1]["ele"])
                /
                metros
                *
                100
            )

            pendiente_maxima = max(
                pendiente_maxima,
                pendiente
            )



    # ------------------------------
    # Perfil cada 100 metros
    # ------------------------------

    altimetria = []


    distancia_actual = 0


    while distancia_actual <= distancia:

        altimetria.append(
            {
                "kilometro":
                    round(
                        distancia_actual / 1000,
                        2
                    ),

                "altitud":
                    round(
                        interpolar_altitud(
                            puntos,
                            distancia_actual
                        )
                    )
            }
        )


        distancia_actual += INTERVALO_ALTITUD



    if altimetria[-1]["kilometro"] != round(longitud_km,2):

        altimetria.append(
            {
                "kilometro":
                    round(longitud_km,2),

                "altitud":
                    round(
                        puntos[-1]["ele"]
                    )
            }
        )



    resultado = {

        "id":
            limpiar_id(nombre),

        "nombre":
            nombre,

        "punto_inicio":
            "",

        "categoria":
            "",

        "vertiente":
            "",

        "pais":
            "",

        "region":
            "",

        "zona":
            "",

        "coordenadas_inicio":
            f'{puntos[0]["lat"]}, {puntos[0]["lon"]}',


        "longitud_km":
            round(longitud_km,2),


        "desnivel_m":
            round(desnivel),


        "altura_maxima_m":
            round(altura_maxima),


        "pendiente_media_porcentaje":
            round(pendiente_media,1),


        "pendiente_maxima_porcentaje":
            round(pendiente_maxima,1),


        "descripcion":
            "",


        "altimetria_puntos":
            altimetria,


        "puntos_clave":
            []
    }



    nombre_json = limpiar_id(
        os.path.splitext(
            os.path.basename(archivo)
        )[0]
    )


    salida = os.path.join(
        CARPETA_JSON,
        nombre_json + ".json"
    )


    with open(
        salida,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            resultado,
            f,
            indent=2,
            ensure_ascii=False
        )


    print(
        "Generado:",
        salida
    )





# ----------------------------------
# Procesar todos los GPX
# ----------------------------------

for archivo in os.listdir(CARPETA_GPX):

    if archivo.lower().endswith(".gpx"):

        procesar_gpx(
            os.path.join(
                CARPETA_GPX,
                archivo
            )
        )


print("\nFIN")