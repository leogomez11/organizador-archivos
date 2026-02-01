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

    carpeta_destino = destinos.get(categoria, destinos["otros"])

    destino_final = carpeta_destino / archivo.name
    fue_renombrado = False

    if destino_final.exists():
        fue_renombrado = True
        contador = 1
        while True:
            nuevo_nombre = f"{archivo.stem}_copia{contador}{extension}"
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
    
    #Fuente: Para evitar errores en los scripts GUI y CLI
    fuente = lista_archivos if lista_archivos is not None else iterar_archivos(base, recursive, exclude, only, ignore_hidden, stats)
    
    for archivo in fuente:
        if stop_event and stop_event.is_set():
            yield "[!] Abortando operación interna..."
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
                    f"Archivo renombrado por colisión: {archivo.name} → {destino_final.name}"
                )
                click.echo(
                    click.style(
                        f"Archivo renombrado por colisión: {archivo.name} → {destino_final.name}",
                        fg="yellow",
                    )
                )
                yield f"Archivo renombrado por colisión: {archivo.name} → {destino_final.name}"
            else:
                click.echo(f"Movido: {archivo.name} → {destino_final}")
                yield f"Movido: {archivo.name} → {destino_final}"

        except PermissionError as e:
            if e.errno == errno.EACCES:
                # En el caso de que el usuario no tenga permisos en el sistema de archivos
                logging.error(f"ERROR {archivo.name} no tiene permiso de acceso")
                click.echo(f"Error {archivo.name} no tiene permiso de acceso")
                stats.registrar_error()
                yield f"ERROR {archivo.name} no tiene permiso de acceso"


            elif e.errno == errno.EAGAIN:
                # En el caso de que el archivo esté bloqueado por otro programa (en uso)
                logging.error(
                    f"ERROR El archivo {archivo.name} está siendo usado por otro programa"
                )
                click.echo(
                    f"ERROR El archivo {archivo.name} está siendo usado por otro programa"
                )
                stats.registrar_error()
                yield f"ERROR El archivo {archivo.name} está siendo usado por otro programa"


            else:
                # Otros errores de permiso generales
                logging.error(f"ERROR de seguridad: {e}")
                click.echo(f"Error de seguridad: {e}")
                stats.registrar_error()
                yield f"Error de seguridad: {e}"


        except OSError as e:
            logging.error(f"ERROR Al mover {archivo.name}: {e}")
            click.echo(f"Error moviendo {archivo.name}: {e}")
            stats.registrar_error()
            yield f"ERROR Al mover {archivo.name}: {e}"

    click.echo(
        click.style(
            f"\nTotal de archivos movidos: {stats.procesados}",
            bold=True,
            fg="green",
        )
    )
    yield f"\nTotal de archivos movidos: {stats.procesados}"


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
            yield "[!] Abortando operación interna..."
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
                    f"[SIMULACIÓN] Archivo renombrado por colisión: {archivo.name} → {destino_final.name}",
                    fg="yellow",
                )
            )
            yield f"[SIMULACIÓN] Archivo renombrado por colisión: {archivo.name} → {destino_final.name}"
        else:
            click.echo(f"[SIMULACIÓN] {archivo.name} → {destino_final}")
            yield f"[SIMULACIÓN] {archivo.name} → {destino_final}"

    click.echo(
        click.style(
            f"\n[SIMULACIÓN] Total de archivos movidos: {total_archivos_simulados}",
            bold=True,
            fg="blue",
        )
    )
    yield f"[SIMULACIÓN] Total de archivos movidos: {total_archivos_simulados}"

