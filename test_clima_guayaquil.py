import csv
from datetime import datetime

import pytest

import clima_guayaquil as clima


@pytest.fixture
def datos():
    return {
        "hourly": {
            "time": [
                "2024-01-01T00:00",
                "2024-01-01T12:00",
                "2024-01-01T23:00",
                "2024-01-02T10:00",
            ],
            "temperature_2m": [20.0, 30.0, None, 25.0],
        }
    }


def test_extraer_ultimas_24h_filtra_ventana_y_nulos(datos):
    registros = clima.extraer_ultimas_24h(datos, ahora=datetime(2024, 1, 2, 0, 0))
    assert registros == [("2024-01-01T00:00", 20.0), ("2024-01-01T12:00", 30.0)]


def test_extraer_ultimas_24h_sin_datos():
    assert clima.extraer_ultimas_24h({}, ahora=datetime(2024, 1, 2, 0, 0)) == []


def test_calcular_resumen():
    registros = [("2024-01-01T00:00", 20.0), ("2024-01-01T12:00", 31.0)]
    resumen = clima.calcular_resumen(registros)
    assert resumen["temperatura_promedio"] == 25.5
    assert resumen["temperatura_maxima"] == 31.0
    assert resumen["temperatura_minima"] == 20.0
    assert resumen["horas"] == 2
    assert resumen["inicio"] == "2024-01-01T00:00"
    assert resumen["fin"] == "2024-01-01T12:00"


def test_calcular_resumen_vacio():
    with pytest.raises(ValueError):
        clima.calcular_resumen([])


def test_guardar_csv(tmp_path):
    resumen = clima.calcular_resumen([("2024-01-01T00:00", 22.0)])
    ruta = clima.guardar_csv(resumen, tmp_path / "resumen_clima.csv")

    with open(ruta, newline="", encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))

    assert len(filas) == 1
    assert filas[0]["ciudad"] == "Guayaquil"
    assert filas[0]["temperatura_promedio"] == "22.0"


def test_obtener_datos_clima_usa_parametros_correctos(monkeypatch, datos):
    llamadas = {}

    class RespuestaFalsa:
        def raise_for_status(self):
            llamadas["status"] = True

        def json(self):
            return datos

    def get_falso(url, params, timeout):
        llamadas["url"] = url
        llamadas["params"] = params
        return RespuestaFalsa()

    monkeypatch.setattr(clima.requests, "get", get_falso)

    assert clima.obtener_datos_clima() == datos
    assert llamadas["url"] == clima.API_URL
    assert llamadas["params"]["hourly"] == "temperature_2m"
    assert llamadas["params"]["past_days"] == 1
    assert llamadas["status"] is True
