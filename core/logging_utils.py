# core/logging_utils.py

import sys
import logging
from pathlib import Path


def obtener_ruta_config(archivo_config: str) -> Path:
    archivo = Path(archivo_config)

    # 1. Valid explicit path
    if archivo.is_absolute() and archivo.exists():
        return archivo

    # 2. PyInstaller executable
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
        candidato = base / archivo_config
        if candidato.exists():
            return candidato

        # Internal fallback (_MEIPASS)
        if hasattr(sys, "_MEIPASS"):
            candidato = Path(sys._MEIPASS) / archivo_config
            if candidato.exists():
                return candidato

    # 3. Normal script
    if archivo.exists():
        return archivo

    return archivo  # Let leer_json handle the error


def obtener_ruta_base():
    """
    Returns the script directory path to configure the log
    """
    if getattr(sys, "frozen", False):
        # Case: executable
        return Path(sys.executable).parent.resolve()
    else:
        # Case: Normal script (.py)
        return Path(__file__).parent.resolve()


def log_config(log_file, log_level):
    # Process paths
    ruta_log = log_file
    ruta_log.mkdir(parents=True, exist_ok=True)

    # Available levels
    niveles = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    nivel_seleccionado = niveles.get(log_level.upper())

    # Root logger config
    logger = logging.getLogger()
    logger.setLevel(nivel_seleccionado)

    if logger.hasHandlers():
        logger.handlers.clear()

    # Define message format
    formato = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # General handler
    archivo_general = ruta_log / "organization.log"
    archivo_handler = logging.FileHandler(archivo_general, mode="a", encoding="utf-8")
    archivo_handler.setFormatter(formato)
    logger.addHandler(archivo_handler)

    # ERROR handler (ERROR and CRITICAL only)
    archivo_errores = ruta_log / "error.log"
    error_handler = logging.FileHandler(archivo_errores, mode="a", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formato)
    logger.addHandler(error_handler)