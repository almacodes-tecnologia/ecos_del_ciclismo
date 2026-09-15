import json
import os
from pathlib import Path

# Directorio donde están los JSON individuales de los ciclistas
CARPETA_CICLISTAS = Path("./ciclistas")
# Archivo JSON índice general
ARCHIVO_INDICE = Path("ciclistas_index.json")

# Definición oficial de los Monumentos del ciclismo
MONUMENTOS_OFICIALES = {
    "Milán-San Remo",
    "Tour de Flandes",
    "París-Roubaix",
    "Lieja-Bastoña-Lieja",
    "Giro de Lombardía"
}

# Grandes Vueltas válidas
GRANDES_VUELTAS = {
    "Tour de Francia",
    "Giro d'Italia",
    "Vuelta a España"
}

def actualizar_indice_ciclistas():
    # 1. Cargar el índice existente si existe, o inicializar una lista vacía
    if ARCHIVO_INDICE.exists():
        with open(ARCHIVO_INDICE, "r", encoding="utf-8") as f:
            try:
                indice_actual = json.load(f)
            except json.JSONDecodeError:
                indice_actual = []
    else:
        indice_actual = []

    # Crear un diccionario para buscar rápidamente por 'id' y evitar duplicados
    ciclistas_dict = {c["id"]: c for c in indice_actual}

    # 2. Recorrer todos los archivos JSON de la carpeta /ciclistas/
    if not CARPETA_CICLISTAS.exists():
        print(f"Error: La carpeta '{CARPETA_CICLISTAS}' no existe.")
        return

    archivos_json = list(CARPETA_CICLISTAS.glob("*.json"))
    print(f"Se encontraron {len(archivos_json)} archivos en la carpeta.")

    contador_nuevos = 0
    contador_actualizados = 0

    for archivo in archivos_json:
        if archivo.resolve() == ARCHIVO_INDICE.resolve():
            continue

        try:
            with open(archivo, "r", encoding="utf-8") as f:
                datos_ciclista = json.load(f)

            carreras_ganadas_set = set()

            # A. Revisar Grandes Vueltas (si ganaron la general, puesto == "1")
            for resultado in datos_ciclista.get("resultadosGrandesVueltas", []):
                puesto = str(resultado.get("puesto", "")).strip()
                if puesto == "1":
                    carrera = resultado.get("carrera")
                    if carrera in GRANDES_VUELTAS:
                        carreras_ganadas_set.add(carrera)

            # B. Revisar Monumentos (filtrando estrictamente por los 5 oficiales)
            for resultado in datos_ciclista.get("resultadosMonumentos", []):
                puesto = str(resultado.get("puesto", "")).strip()
                if puesto == "1":
                    carrera = resultado.get("carrera")
                    # Validamos que sea uno de los 5 monumentos de verdad
                    if carrera in MONUMENTOS_OFICIALES:
                        carreras_ganadas_set.add(carrera)

            # C. Revisar Mundiales
            for resultado in datos_ciclista.get("resultadosMundiales", []):
                puesto = str(resultado.get("puesto", "")).strip()
                if puesto == "1":
                    carrera = resultado.get("carrera")
                    if carrera:
                        carreras_ganadas_set.add(carrera)

            # Extraer los campos requeridos para el índice
            ciclista_resumido = {
                "id": datos_ciclista.get("id"),
                "nombre": datos_ciclista.get("nombre"),
                "nacionalidad": datos_ciclista.get("nacionalidad"),
                "activo": datos_ciclista.get("activo"),
                "especialidad": datos_ciclista.get("especialidad", []),
                "genero": "masculino",
                "carreras_ganadas": sorted(list(carreras_ganadas_set))
            }

            # Validar que al menos tenga un 'id' para poder indexarlo
            if not ciclista_resumido["id"]:
                print(f"Aviso: El archivo {archivo.name} no contiene un campo 'id' válido. Se omite.")
                continue

            if ciclista_resumido["id"] in ciclistas_dict:
                contador_actualizados += 1
            else:
                contador_nuevos += 1

            ciclistas_dict[ciclista_resumido["id"]] = ciclista_resumido

        except Exception as e:
            print(f"Error leyendo el archivo {archivo.name}: {e}")

    # 3. Volver a convertir el diccionario en una lista
    nuevo_indice = list(ciclistas_dict.values())

    # 4. Guardar el resultado actualizado
    with open(ARCHIVO_INDICE, "w", encoding="utf-8") as f:
        json.dump(nuevo_indice, f, ensure_ascii=False, indent=4)

    print("\n¡Proceso completado con éxito!")
    print(f"- Ciclistas nuevos añadidos: {contador_nuevos}")
    print(f"- Ciclistas actualizados: {contador_actualizados}")
    print(f"- Total de ciclistas en '{ARCHIVO_INDICE}': {len(nuevo_indice)}")

if __name__ == "__main__":
    actualizar_indice_ciclistas()
