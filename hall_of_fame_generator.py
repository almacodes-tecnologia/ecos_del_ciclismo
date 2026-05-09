import json
import os
import unicodedata
from collections import defaultdict

# --- CONFIGURACIÓN DE PUNTUACIONES ---
CATEGORIAS = {
    "GT_TOUR": ["tour_de_francia"],
    "GT_GIRO_VUELTA": ["giro_de_italia", "vuelta_a_espana"],
    "MONUMENTOS": ["milan_san_remo", "tour_de_flandes", "paris_roubaix", "lieja_bastona_lieja", "giro_de_lombardia"],
    "MUNDIAL_JJOO": ["mundial_ciclismo_ruta", "mundial_ciclismo_contrarreloj", "jjoo_ciclismo_ruta", "jjoo_ciclismo_contrarreloj"],
    "WORLD_TOUR_TOP": ["paris_niza", "tirreno_adriatico", "criterium_du_dauphine", "tour_de_suiza", "strade_bianche", "amstel_gold_race"],
    "WORLD_TOUR_STD": ["volta_a_catalunya", "vuelta_al_pais_vasco", "tour_de_romandia", "clasica_san_sebastian", "gante_wevelgem", "e3_harelbeke", "flecha_valona", "bretagne_classic", "kuurne_bruselas_kuurne"]
}

PUNTOS = {
    "GT_TOUR": {"1": 200, "2": 120, "3": 80, "4": 50, "5": 40, "top10": 20, "etapa": 15, "montana": 30, "puntos": 30, "jovenes": 13},
    "GT_GIRO_VUELTA": {"1": 150, "2": 90, "3": 60, "4": 40, "5": 30, "top10": 15, "etapa": 12, "montana": 25, "puntos": 25, "jovenes": 10},
    "MONUMENTOS": {"1": 120, "2": 70, "3": 50, "4": 30, "5": 20, "top10": 10},
    "MUNDIAL_JJOO": {"1": 150, "2": 80, "3": 55},
    "WORLD_TOUR_TOP": {"1": 70, "2": 50, "3": 35, "etapa": 5},
    "WORLD_TOUR_STD": {"1": 50, "2": 45, "3": 25, "etapa": 3},
}

# Diccionario para unificar nombres de países con errores o variantes
MAPEO_PAISES = {
    "Belgica": "Bélgica",
    "Kazajistan": "Kazajistán",
    "Kazajstan": "Kazajistán",
    "EEUU": "Estados Unidos",
    "USA": "Estados Unidos",
    "United States": "Estados Unidos",
    "Alemania Occidental": "Alemania",
    "Alemania Oriental": "Alemania",
    "Holanda": "Países Bajos",
    "Paises Bajos": "Países Bajos",
    "Gran Bretaña": "Reino Unido"
}

# --- Lista de nombres que ignoramos completamente ---
NOMBRES_IGNORAR = {
    "espana", 
    "italia", 
    "francia", 
    "equipo nacional",
    "desconocido",
    "desierto",
    "varios",
    "astana",
    "cancelada",
    "/"
}

def limpiar_texto(texto):
    if not texto: return ""
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode("utf-8").lower().strip()

def generar_id_ciclista(nombre):
    palabras = limpiar_texto(nombre).replace(",", "").split()
    palabras.sort()
    return "_".join(palabras)

def obtener_categoria(id_carrera):
    for cat, lista in CATEGORIAS.items():
        if id_carrera in lista:
            return cat
    return "WORLD_TOUR_STD"

def procesar_ranking(ruta_base):
    db = defaultdict(lambda: {
        "puntos": 0, "pais": "Desconocido", "nombre_pantalla": "",
        "participaciones_gt": 0, "podiums_gt": 0,
        "participaciones_monumentos": 0, "podiums_monumentos": 0,
        "participaciones_mundiales": 0, "podiums_mundiales": 0,
        "victorias_totales": 0, "victorias_generales_gt": 0,
        "victorias_etapa_gt": 0, "victorias_monumentos": 0,
        "victorias_mundiales": 0
    })

    if not os.path.exists(ruta_base):
        print(f"❌ Error: carpeta {ruta_base} no existe.")
        return []

    for carrera_id in os.listdir(ruta_base):
        ruta_carrera = os.path.join(ruta_base, carrera_id)
        if "_old" in carrera_id or not os.path.isdir(ruta_carrera):
            continue

        cat = obtener_categoria(carrera_id)
        pts_esquema = PUNTOS.get(cat, PUNTOS["WORLD_TOUR_STD"])

        for archivo in os.listdir(ruta_carrera):
            if not archivo.endswith(".json"): continue
            ruta_json = os.path.join(ruta_carrera, archivo)

            try:
                with open(ruta_json, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"❌ ERROR en {ruta_json}: {e}")
                continue

            def sumar_puntos(nombre, pts, pais=None, tipo_v=None):
                # 1. Si el nombre es null (None) o vacío, o no hay puntos, ignoramos totalmente
                if not nombre or not isinstance(nombre, str) or pts <= 0: 
                    return
                
                # Ignorar nombres con "/" (Suele ser basura de equipos o errores de scraping)
                if "/" in nombre:
                    # Opcional: print(f"⚠️ Filtrando nombre inválido: {nombre}")
                    return
                
                nombre_lower = nombre.lower().strip()
                
                # Filtro de nombres basura del scraping
                if nombre_lower in NOMBRES_IGNORAR or nombre_lower == "none":
                    return

                # 2. Control de errores en el país (evita el error 'NoneType' has no attribute 'strip')
                if pais and isinstance(pais, str):
                    pais_limpio = pais.strip()
                    if "," in pais_limpio or len(pais_limpio) > 25:
                        print(f"🚨 ERROR DE FORMATO EN: {nombre} | País: {pais_limpio}")
                        return
                else:
                    pais_limpio = None

                # Generamos ID y guardamos nombre
                cid = generar_id_ciclista(nombre)
                if not db[cid]["nombre_pantalla"]:
                    db[cid]["nombre_pantalla"] = nombre
                
                db[cid]["puntos"] += pts
                
                # 3. Asignación inteligente de país
                if pais_limpio:
                    # Unificamos
                    if pais_limpio in MAPEO_PAISES:
                        pais_limpio = MAPEO_PAISES[pais_limpio]
                    
                    # Solo asignamos si no tenemos un país real todavía
                    if db[cid]["pais"] == "Desconocido":
                        db[cid]["pais"] = pais_limpio

                # 4. Contador de victorias (solo si hay nombre válido)
                if tipo_v:
                    db[cid]["victorias_totales"] += 1
                    # ... resto de tus contadores ...
                    if tipo_v == "general_gt": db[cid]["victorias_generales_gt"] += 1
                    elif tipo_v == "etapa_gt": db[cid]["victorias_etapa_gt"] += 1
                    elif tipo_v == "monumento": db[cid]["victorias_monumentos"] += 1
                    elif tipo_v == "mundial_jjoo": db[cid]["victorias_mundiales"] += 1

            # --- Clasificación General ---
            for res in data.get("clasificacionGeneral", []):
                nombre = res.get("nombre")
                puesto_raw = res.get("puesto")
                if not nombre or nombre in NOMBRES_IGNORAR or puesto_raw is None:
                    print(f"⚠️ AVISO: Ciclista ignorado o incompleto en {ruta_json} (Ciclista: {nombre}, Puesto: {puesto_raw})")
                    continue
                try: puesto = int(puesto_raw)
                except: continue

                cid = generar_id_ciclista(nombre)
                # participaciones/podiums
                if cat in ["GT_TOUR", "GT_GIRO_VUELTA"]:
                    if puesto <= 10: db[cid]["participaciones_gt"] += 1
                    if puesto <= 3: db[cid]["podiums_gt"] += 1
                elif cat == "MONUMENTOS":
                    if puesto <= 10: db[cid]["participaciones_monumentos"] += 1
                    if puesto <= 3: db[cid]["podiums_monumentos"] += 1
                elif cat == "MUNDIAL_JJOO":
                    db[cid]["participaciones_mundiales"] += 1
                    if puesto <= 3: db[cid]["podiums_mundiales"] += 1

                pts = pts_esquema.get(str(puesto), pts_esquema.get("top10", 0) if puesto <= 10 else 0)
                tipo_v = None
                if puesto == 1:
                    if cat in ["GT_TOUR", "GT_GIRO_VUELTA"]: tipo_v = "general_gt"
                    elif cat == "MONUMENTOS": tipo_v = "monumento"
                    elif cat == "MUNDIAL_JJOO": tipo_v = "mundial_jjoo"

                sumar_puntos(nombre, pts, res.get("pais"), tipo_v)

            # --- Etapas ---
            pts_e = pts_esquema.get("etapa", 0)
            for e in data.get("etapas", []):
                sumar_puntos(e.get("nombre"), pts_e, e.get("pais"), tipo_v="etapa_gt" if cat in ["GT_TOUR","GT_GIRO_VUELTA"] else None)

            # --- Maillots ---
            for k in ["Montana","Puntos","Jovenes"]:
                gan = data.get(f"ganador{k}")
                if gan:
                    pts_m = pts_esquema.get(k.lower(), 0)
                    sumar_puntos(gan.get("nombre"), pts_m, gan.get("pais"), tipo_v="maillot")

    # --- Lista final ordenada ---
    # --- Lista final ordenada filtrando ciclistas con 0 puntos ---
    resultado = []
    for v in db.values():
        if v["puntos"] <= 0:
            # ⚠️ Ciclista descartado por no tener puntos
            continue
        resultado.append({
            "nombre": v["nombre_pantalla"],
            "puntos": v["puntos"],
            "pais": v["pais"],
            "participaciones_gt": v["participaciones_gt"],
            "podiums_gt": v["podiums_gt"],
            "participaciones_monumentos": v["participaciones_monumentos"],
            "podiums_monumentos": v["podiums_monumentos"],
            "participaciones_mundiales": v.get("participaciones_mundiales",0),
            "podiums_mundiales": v.get("podiums_mundiales",0),
            "victorias_totales": v["victorias_totales"],
            "victorias_generales_gt": v["victorias_generales_gt"],
            "victorias_etapa_gt": v["victorias_etapa_gt"],
            "victorias_monumentos": v["victorias_monumentos"],
            "victorias_mundiales": v.get("victorias_mundiales",0)
        })

    # Orden final descendente por puntos
    return sorted(resultado, key=lambda x: x["puntos"], reverse=True)


if __name__ == "__main__":
    ruta_historial = "./assets/historial"
    hall_of_fame = procesar_ranking(ruta_historial)
    with open("hall_of_fame.json", "w", encoding="utf-8") as f:
        json.dump(hall_of_fame, f, indent=4, ensure_ascii=False)
    print(f"✅ Ranking filtrado generado: {len(hall_of_fame)} ciclistas.")
