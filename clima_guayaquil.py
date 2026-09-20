"""Resumen de temperaturas de Guayaquil de las ultimas 24 horas (Open-Meteo)."""

import argparse
import csv
from datetime import datetime, timedelta, timezone

import requests

API_URL = "https://api.open-meteo.com/v1/forecast"
LATITUD = -2.19
LONGITUD = -79.89
ZONA_HORARIA = "America/Guayaquil"
ARCHIVO_CSV = "resumen_clima.csv"


def obtener_datos_clima(latitud=LATITUD, longitud=LONGITUD, timeout=30):
    """Consulta Open-Meteo y devuelve el JSON con temperaturas horarias."""
    respuesta = requests.get(
        API_URL,
        params={
            "latitude": latitud,
            "longitude": longitud,
            "hourly": "temperature_2m",
            "past_days": 1,
            "forecast_days": 1,
            "timezone": ZONA_HORARIA,
        },
        timeout=timeout,
    )
    respuesta.raise_for_status()
    return respuesta.json()


def extraer_ultimas_24h(datos, ahora=None):
    """Devuelve las parejas (hora, temperatura) de las ultimas 24 horas."""
    horario = datos.get("hourly") or {}
    tiempos = horario.get("time") or []
    temperaturas = horario.get("temperature_2m") or []

    if ahora is None:
        ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    inicio = ahora - timedelta(hours=24)

    registros = []
    for tiempo, temperatura in zip(tiempos, temperaturas):
        if temperatura is None:
            continue
        marca = datetime.fromisoformat(tiempo)
        if marca.tzinfo is not None:
            marca = marca.replace(tzinfo=None)
        if inicio <= marca <= ahora:
            registros.append((tiempo, float(temperatura)))
    return registros


def calcular_resumen(registros):
    """Calcula promedio, maxima y minima a partir de los registros."""
    if not registros:
        raise ValueError("No hay temperaturas disponibles para resumir")

    temperaturas = [temperatura for _, temperatura in registros]
    return {
        "ciudad": "Guayaquil",
        "inicio": registros[0][0],
        "fin": registros[-1][0],
        "horas": len(temperaturas),
        "temperatura_promedio": round(sum(temperaturas) / len(temperaturas), 2),
        "temperatura_maxima": round(max(temperaturas), 2),
        "temperatura_minima": round(min(temperaturas), 2),
    }


def guardar_csv(resumen, ruta=ARCHIVO_CSV):
    """Guarda el resumen en un archivo CSV y devuelve la ruta usada."""
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(resumen.keys()))
        escritor.writeheader()
        escritor.writerow(resumen)
    return ruta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", default=ARCHIVO_CSV, help="ruta del CSV de salida")
    args = parser.parse_args()

    datos = obtener_datos_clima()
    registros = extraer_ultimas_24h(datos)
    resumen = calcular_resumen(registros)
    ruta = guardar_csv(resumen, args.salida)

    print(f"Horas analizadas: {resumen['horas']}")
    print(f"Promedio: {resumen['temperatura_promedio']} C")
    print(f"Maxima: {resumen['temperatura_maxima']} C")
    print(f"Minima: {resumen['temperatura_minima']} C")
    print(f"Resumen guardado en {ruta}")


if __name__ == "__main__":
    main()
