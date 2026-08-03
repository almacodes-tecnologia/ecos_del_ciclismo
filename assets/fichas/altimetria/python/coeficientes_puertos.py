import json
import os
import math


def get_altitud_en_km(puntos, km):
    """Interpolación lineal de altitud basada en la posición km."""
    for i in range(len(puntos) - 1):
        if puntos[i]['kilometro'] <= km <= puntos[i + 1]['kilometro']:

            p1, p2 = puntos[i], puntos[i + 1]

            if p2['kilometro'] == p1['kilometro']:
                return p1['altitud']

            fraccion = (
                (km - p1['kilometro']) /
                (p2['kilometro'] - p1['kilometro'])
            )

            return (
                p1['altitud'] +
                fraccion *
                (p2['altitud'] - p1['altitud'])
            )

    return puntos[-1]['altitud']


def calcular_coeficiente(puntos, detalle):

    if len(puntos) < 2:
        return 0.0


    # ==========================
    # FACTORES AJUSTABLES
    # ==========================

    inc_fatiga = 0.0025


    pen_km = 0.0005

    bonos = {
        8: 35.0,
        15: 70.0,
        25: 150.0,
        40: 225.0
    }

    mults = {
        10: 1.10,
        12: 1.25,
        15: 1.50
    }


    coeficiente = 0.0

    fatiga = 1.0

    bonus_acumulado = 0.0

    sufrimiento = 0

    # Nuevo: kilómetros con pendiente sostenida
    bonus_pendiente_sostenida  = 0.0


    flags = {
        8: False,
        15: False,
        25: False,
        40: False
    }


    longitud = puntos[-1]['kilometro']


    # ==========================
    # RECORRIDO KM A KM
    # ==========================

    for km in range(0, math.ceil(longitud)):

        siguiente_km = min(km + 1.0, longitud)

        distancia = siguiente_km - km

        if distancia <= 0:
            continue


        alt_inicio = get_altitud_en_km(
            puntos,
            km
        )

        alt_fin = get_altitud_en_km(
            puntos,
            siguiente_km
        )


        pendiente = (
            ((alt_fin - alt_inicio) / (distancia * 1000.0))
            * 100.0
        )


        # -------------------------
        # Pendiente sostenida
        # Premia puertos largos
        # con esfuerzo continuo
        # -------------------------

        if pendiente >= 6:

            bonus_pendiente_sostenida += (
                distancia *
                math.pow(max(0, pendiente - 5), 1.05)
            )


        # -------------------------
        # Recuperación
        # -------------------------

        if pendiente <= 0:

            fatiga = max(
                1.0,
                fatiga * 0.95
            )

            sufrimiento = max(
                0,
                sufrimiento - 2
            )

            continue



        # -------------------------
        # Penalización longitud
        # -------------------------

        factor_longitud = max(
            0.95,
            1.0 - (km * pen_km)
        )



        # -------------------------
        # Bonus pendiente extrema
        # -------------------------

        if pendiente >= 15:

            factor_pendiente = mults[15]

        elif pendiente >= 12:

            factor_pendiente = mults[12]

        elif pendiente >= 10:

            factor_pendiente = mults[10]

        else:

            factor_pendiente = 1.0



        # -------------------------
        # Esfuerzo
        # -------------------------

        coeficiente += (
            math.pow(pendiente, 1.75)
            * fatiga
            * factor_longitud
            * factor_pendiente
        )



        # -------------------------
        # Sufrimiento acumulado
        # -------------------------

        if pendiente >= 15:

            sufrimiento += 10

        elif pendiente >= 12:

            sufrimiento += 7

        elif pendiente >= 10:

            sufrimiento += 5

        elif pendiente >= 8:

            sufrimiento += 2



        # -------------------------
        # Bonus sufrimiento
        # -------------------------

        for valor, puntos_bonus in bonos.items():

            if not flags[valor] and sufrimiento >= valor:

                bonus_acumulado += puntos_bonus

                flags[valor] = True



        # -------------------------
        # Fatiga
        # -------------------------

        incremento = inc_fatiga


        if pendiente >= 15:

            incremento *= 3.0

        elif pendiente >= 12:

            incremento *= 2.2

        elif pendiente >= 10:

            incremento *= 1.6

        elif pendiente >= 8:

            incremento *= 1.3



        fatiga += incremento



    # ==========================
    # BONUS SUFRIMIENTO
    # ==========================

    coeficiente += bonus_acumulado



    # ==========================
    # BONUS PENDIENTE SOSTENIDA
    # ==========================



    coeficiente += bonus_pendiente_sostenida * 1.7
    # ==========================
    # CORRECCIÓN MUROS
    # ==========================

    if sufrimiento < 30:

        p_max = detalle.get(
            'pendiente_maxima_porcentaje',
            0
        )


        if p_max >= 28:

            bonus_muro = 1.65

        elif p_max >= 26:

            bonus_muro = 1.50

        elif p_max >= 23:

            bonus_muro = 1.35

        elif p_max >= 20:

            bonus_muro = 1.30

        else:

            bonus_muro = 1.0



        if bonus_muro > 1.0:

            factor_longitud_muro = (
                1.0 +
                (
                    detalle.get('longitud_km', 0)
                    * 0.001
                )
            )


            coeficiente *= (
                bonus_muro *
                factor_longitud_muro
            )



    return round(pow(coeficiente, 0.98))





# ==========================
# EJECUCIÓN PRINCIPAL
# ==========================

def main():

    print(f"{'PUERTO':<40} | {'COEFICIENTE'}")
    print("-" * 55)


    for archivo in os.listdir('.'):

        if archivo.endswith('.json') and not archivo.startswith('nuevo_'):

            try:

                with open(
                    archivo,
                    'r',
                    encoding='utf-8-sig'
                ) as f:

                    data = json.load(f)


                    coef = calcular_coeficiente(
                        data['altimetria_puntos'],
                        data
                    )


                    print(
                        f"{data.get('nombre', archivo):<40} | {coef}"
                    )


            except Exception as e:

                print(
                    f"Error procesando {archivo}: {e}"
                )



if __name__ == "__main__":
    main()