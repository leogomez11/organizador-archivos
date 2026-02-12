# core/engine.py

import click
import shutil
import logging
import errno
from pathlib import Path
from typing import Iterable

from core.rules import detectar_categoria
from core.stats import Stats
from utils.fs_utils import crear_destinos, crear_carpetas_si_no_existe


def resolver_destino(archivo: Path, reglas: dict, destinos: dict) -> tuple[str, Path, bool]:
    extension = archivo.suffix.lower()
    categoria = detectar_categoria(extension, reglas)

    carpeta_destino = destinos.get(categoria, destinos["Others"])

    destino_final = carpeta_destino / archivo.name
    fue_renombrado = False

    if destino_final.exists():
        fue_renombrado = True
        contador = 1
        while True:
            nuevo_nombre = f"{archivo.stem}_copy{contador}{extension}"
            destino_final = carpeta_destino / nuevo_nombre
            if not destino_final.exists():
                break
            contador += 1

    return categoria, destino_final, fue_renombrado


# Exclusiones de seguridad innegociables
NUNCA_TOCAR_DIR = {"venv", "lib", "scripts", "include", ".git", "__pycache__"}
NUNCA_TOCAR_FILE = {"pyproject.toml", "pyvenv.cfg"}

def iterar_archivos(
    base: Path, recursive: bool, exclude: set, only: set, ignore_hidden: bool, stats: Stats
):
    exclude = {e.lower() for e in exclude}
    only = {o.lower() if o.startswith(".") else f".{o.lower()}" for o in only}

    fuente = base.rglob("*") if recursive else base.iterdir()

    for p in fuente:
        if not p.is_file():
            continue
        
        #Evitar carpetas de configuracion críticas
        try:
            relative = p.relative_to(base)
        except ValueError:
            continue

        if any(part.lower() in NUNCA_TOCAR_DIR for part in relative.parts[:-1]):
            continue

        
        #Evitar archivos de configuracion críticos
        if p.name.lower() in NUNCA_TOCAR_FILE:
            continue
        
        # filtro de archivos ocultos (basado en la ruta completa)
        if ignore_hidden and any(part.startswith(".") for part in p.parts):
            continue

        # calculo de ruta relativa respecto a la base
        ruta_relativa = p.relative_to(base)

        # filtro de exclusion (exclude)
        if any(part.lower() in exclude for part in ruta_relativa.parts):
            stats.registrar_excluidos()
            continue

        # filtro de extensiones permitidas (only)
        if only and p.suffix.lower() not in only:
            continue

        yield p


def mover_archivos(
    base: Path,
    reglas: dict,
    recursive: bool,
    exclude: set,
    only: set,
    ignore_hidden: bool,
    stats: Stats,
    lista_archivos=None,
    stop_event=None
):
    destinos = crear_destinos(base, reglas)
    
    fuente = lista_archivos if lista_archivos is not None else iterar_archivos(base, recursive, exclude, only, ignore_hidden, stats)
    
    for archivo in fuente:
        if stop_event and stop_event.is_set():
            yield "[!] Aborting internal operation..."
            return 
        categoria, destino_final, fue_renombrado = resolver_destino(
            archivo, reglas, destinos
        )
        if destino_final.parent == archivo.parent:
            stats.registrar_saltados()
            continue


        try:
            crear_carpetas_si_no_existe(destino_final.parent)
            shutil.move(str(archivo), str(destino_final))
            stats.registrar_procesados()
            if fue_renombrado:
                logging.warning(
                    f"File renamed due to collision: {archivo.name} → {destino_final.name}"
                )
                click.echo(
                    click.style(
                        f"File renamed due to collision: {archivo.name} → {destino_final.name}",
                        fg="yellow",
                    )
                )
                yield f"File renamed due to collision: {archivo.name} → {destino_final.name}"
            else:
                click.echo(f"Moved: {archivo.name} → {destino_final}")
                yield f"Moved: {archivo.name} → {destino_final}"

        except PermissionError as e:
            if e.errno == errno.EACCES:
                logging.error(f"ERROR {archivo.name} access denied")
                click.echo(f"Error {archivo.name} access denied")
                stats.registrar_error()
                yield f"ERROR {archivo.name} access denied"


            elif e.errno == errno.EAGAIN:
                logging.error(
                    f"ERROR File {archivo.name} is being used by another program"
                )
                click.echo(
                    f"ERROR File {archivo.name} is being used by another program"
                )
                stats.registrar_error()
                yield f"ERROR File {archivo.name} is being used by another program"


            else:
                logging.error(f"Security ERROR: {e}")
                click.echo(f"Security Error: {e}")
                stats.registrar_error()
                yield f"Security Error: {e}"


        except OSError as e:
            logging.error(f"ERROR Moving {archivo.name}: {e}")
            click.echo(f"Error moving {archivo.name}: {e}")
            stats.registrar_error()
            yield f"ERROR Moving {archivo.name}: {e}"

    click.echo(
        click.style(
            f"\nTotal files moved: {stats.procesados}",
            bold=True,
            fg="green",
        )
    )
    yield f"\nTotal files moved: {stats.procesados}"


def simulacion(
    base: Path,
    reglas: dict,
    recursive: bool,
    exclude: set,
    only: set,
    ignore_hidden: bool,
    stats: Stats,
    lista_archivos=None,
    stop_event=None
):
    total_archivos_simulados = 0
    destinos = crear_destinos(base, reglas)

    fuente = lista_archivos if lista_archivos is not None else iterar_archivos(base, recursive, exclude, only, ignore_hidden, stats)
    
    for archivo in fuente:
        if stop_event and stop_event.is_set():
            yield "[!] Aborting internal operation..."
            return
        categoria, destino_final, fue_renombrado = resolver_destino(
            archivo, reglas, destinos
        )

        if destino_final.parent == archivo.parent:
            stats.registrar_saltados()
            continue


        total_archivos_simulados += 1
        if fue_renombrado:
            click.echo(
                click.style(
                    f"[SIMULATION] File renamed due to collision: {archivo.name} → {destino_final.name}",
                    fg="yellow",
                )
            )
            yield f"[SIMULATION] File renamed due to collision: {archivo.name} → {destino_final.name}"
        else:
            click.echo(f"[SIMULATION] {archivo.name} → {destino_final}")
            yield f"[SIMULATION] {archivo.name} → {destino_final}"

    click.echo(
        click.style(
            f"\n[SIMULATION] Total files moved: {total_archivos_simulados}",
            bold=True,
            fg="blue",
        )
    )
    yield f"[SIMULATION] Total files moved: {total_archivos_simulados}"