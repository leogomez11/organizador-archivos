# utils/fs_utils.py

import click
from pathlib import Path


def crear_destinos(base: Path, reglas: dict) -> dict:
    destinos = {categoria: base / categoria for categoria in reglas.keys()}
    destinos.setdefault("otros", base / "otros")
    return destinos


def crear_carpetas_si_no_existe(destino_final: Path):
    if not destino_final.exists():
        destino_final.mkdir(parents=True, exist_ok=True)
        click.echo(f"Carpeta {destino_final.name} creada con exito.")