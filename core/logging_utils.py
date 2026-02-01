# core/logging_utils.py

import sys
import logging
from pathlib import Path


def obtener_ruta_config(archivo_config: str) -> Path:
    archivo = Path(archivo_config)

    # 1. Ruta explícita válida
    if archivo.is_absolute() and archivo.exists():
        return archivo

    # 2. Ejecutable PyInstaller
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
        candidato = base / archivo_config
        if candidato.exists():
            return candidato

        # fallback interno (_MEIPASS)
        if hasattr(sys, "_MEIPASS"):
            candidato = Path(sys._MEIPASS) / archivo_config
            if candidato.exists():
                return candidato

    # 3. Script normal
    if archivo.exists():
        return archivo

    return archivo  # para que leer_json maneje el error



def obtener_ruta_base():
    """
    Retorna la ruta del directorio del script para configurar el log
    """
    if getattr(sys, "frozen", False):
        # Caso: ejecutable
        return Path(sys.executable).parent.resolve()
    else:
        # Caso: Script normal (.py)
        return Path(__file__).parent.resolve()


def log_config(log_file, log_level):
    # Procesar rutas
    ruta_log = log_file
    ruta_log.mkdir(parents=True, exist_ok=True)

    # Niveles disponibles
    niveles = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    nivel_seleccionado = niveles.get(log_level.upper())

    # Confi logger raiz
    logger = logging.getLogger()
    logger.setLevel(nivel_seleccionado)

    if logger.hasHandlers():
        logger.handlers.clear()

    # Definir el formato de mensaje
    formato = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler general
    archivo_general = ruta_log / "organizacion.log"
    archivo_handler = logging.FileHandler(archivo_general, mode="a", encoding="utf-8")
    archivo_handler.setFormatter(formato)
    logger.addHandler(archivo_handler)

    # Handler de ERRORES (solo ERROR y CRITICAL)
    archivo_errores = ruta_log / "errores.log"
    error_handler = logging.FileHandler(archivo_errores, mode="a", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formato)
    logger.addHandler(error_handler)

