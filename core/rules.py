# core/rules.py

from pathlib import Path
import logging
import json
import click


def detectar_categoria(extension, reglas):
    for categoria, extensiones in reglas.items():
        if extension in extensiones:
            return categoria
    return "otros"



def leer_json(ruta_config: Path, stats: Stats):
    if not ruta_config.is_file():
        logging.error(f"No se encontró el archivo de reglas: {ruta_config}")
        click.echo(f"ERROR: No se encontró el archivo de reglas: {ruta_config}")
        stats.registrar_error()
        return None

    try:
        with ruta_config.open("r", encoding="utf-8") as f:
            data = json.load(f)
            
            if not isinstance(data, dict):
                raise ValueError("reglas.json inválido: debe ser un objeto JSON ({})")

        return {
            k: {ext if ext.startswith(".") else f".{ext}" for ext in map(str.lower, vals)}
            for k, vals in data.items()
        }


    except json.JSONDecodeError as e:
        click.echo(f"ERROR: JSON inválido: {e}")
        logging.error(f"JSON inválido: {e}")
        stats.registrar_error()
        return None  # Devolver None para indicar fallo de lectura/formato
