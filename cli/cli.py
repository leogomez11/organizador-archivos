# cli.py

import time
import logging
from pathlib import Path

import click

from core.engine import mover_archivos, simulacion
from core.rules import leer_json
from core.stats import Stats
from core.logging_utils import (
    obtener_ruta_base,
    obtener_ruta_config,
    log_config,
)


__version__ = "1.0.0"


def es_raiz_proyecto(ruta: Path) -> bool:
    """
    Verifica si la ruta contiene archivos del entorno de desarrollo
    """
    #archivos que definen la raiz del proyecto
    indicadores = [
        "pyproject.toml",  # Configuración de Poetry/Pip
        "pyvenv.cfg",       # Configuración de Entorno Virtual
        "requirements.txt", # Lista de dependencias
        ".gitignore",       # Repositorio Git
        "setup.py"          # Instalación de paquetes antiguos
    ]
    
    #retorna true si AL MENOS UNO existe en la ruta
    return any((ruta / archivo).exists() for archivo in indicadores)



@click.version_option(
    __version__,
    prog_name="Organizador de Archivos"
)
@click.command()
@click.option(
    "--ruta",
    help="Ubicacion a organizar",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=Path),
    required=True,
)
@click.option(
    "--recursive",
    is_flag=True,
    help="Procesa archivos dentro de subcarpetas"
)
@click.option(
    "--config",
    type=click.Path(dir_okay=False, readable=True, path_type=Path),
    default=lambda: obtener_ruta_base() / "reglas.json",
    help="Archivo JSON con reglas de organizacion",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Nombres de carpetas o archivos a excluir"
)
@click.option(
    "--only",
    multiple=True,
    help="Extensiones a mover solamente"
    )
@click.option(
    "--ignore-hidden",
    is_flag=True,
    help="Ignorar archivos y carpetas ocultos"
)
@click.option(
    "--log-file",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, path_type=Path),
    default= lambda: obtener_ruta_base() / "logs",
    help="Directorio donde se guardarán los logs.",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Nivel de detalle del log.",
)
@click.option(
    "--apply",
    is_flag=True,
    help="Ejecuta los cambios en el disco."
)
@click.option(
    "--yes",
    "-y", is_flag=True,
    help="Omite la confirmación manual."
)
def cli(
    ruta, ignore_hidden, recursive, exclude, only, config, log_file, log_level, apply, yes
):
    #Configuracion para contador de archivos/errores
    stats = Stats()
    
    # Configuracion contador de ejecucion
    start_time = time.perf_counter()

    # Configuracion del log
    ruta_log_obj = Path(log_file)
    log_config(ruta_log_obj, log_level)
    logging.info(f"Iniciando organizador de archivos {__version__}")
    
    # Resolver la ruta del archivo de reglas (Soporte para PyInstaller/Local)
    ruta_config_final = obtener_ruta_config(config)
    
    # Carga de reglas
    reglas = leer_json(ruta_config_final, stats)

    if reglas is None:
        logging.error("Error leyendo reglas.json")
        click.echo("Error leyendo reglas.json")
        stats.registrar_error()
        return
    
    # Seleccion de archivos especificos y excluidos
    carpetas_destino = {k.lower() for k in reglas.keys()}
    exclude_set = {e.lower() for e in exclude}
    exclude_set.update(carpetas_destino) #Evita organizar carpetas ya organizadas
    only_set = set(only)
    
    
    # RESOLVER RUTA (Convertir "." o "../" en rutas reales como "C:/Usuarios/Proyectos")
    ruta_objetivo = ruta.resolve()
    ruta_actual = Path.cwd().resolve()
    
    # PRIMER FILTRO
    if ruta_objetivo == ruta_actual:
        click.echo(click.style("\n[!] ADVERTENCIA: Directorio de trabajo detectado.", fg="yellow", bold=True))
        if not click.confirm("¿Deseas continuar bajo tu propio riesgo?"):
            return #Aborta si el usuario dice No
    
    if es_raiz_proyecto(ruta_objetivo):
        click.echo(click.style("\n[!] ERROR DE SEGURIDAD", fg="red", bold=True))
        click.echo(f"La ubicación '{ruta_objetivo}' contiene archivos de configuración crítica.")
        click.echo("Se abortó la operación para proteger el entorno virtual y el proyecto.")
        logging.error(f"Intento de ejecución bloqueado en raíz de proyecto: {ruta}")
        return 
    
    
    #MODO SIMULACION
    if not apply:
        click.echo(click.style("\n[MODO SIMULACIÓN] No se realizarán cambios reales.", fg="blue", bold=True))
        for _ in simulacion(ruta_objetivo, reglas, recursive, exclude_set, only_set, ignore_hidden,stats, lista_archivos=None, stop_event=None):
            pass #No hacemos nada con el yield y obliga al script a ejecutarse
        click.echo(click.style("\nPara aplicar estos cambios, usa el flag: --apply", fg="yellow"))
    
    #MODO EJECUCION
    else:
        # Confirmación extra antes de aplicar (Opcional, pero recomendada)
        if yes or click.confirm(click.style(f"¿Confirmas aplicar los cambios en {ruta_objetivo}?", fg="red", bold=True)):
            for _ in mover_archivos(
                ruta_objetivo, reglas, recursive, exclude_set, only_set, ignore_hidden, stats, lista_archivos=None, stop_event=None
            ):
                pass #Igual que en simulacion, ignora el yield
        else:
            click.echo("Operación abortada.")
            return

    # Calculo tiempo total ejecucion
    end_time = time.perf_counter()
    tiempo_total = end_time - start_time

    # --- RESUMEN FINAL ---
    click.echo(click.style("\n" + "=" * 30, fg="bright_black"))
    click.echo(click.style("RESUMEN DE OPERACIÓN", bold=True))
    click.echo(f"Tiempo total: {tiempo_total:.4f} seg")
    click.echo(f"Archivos Procesados: {stats.procesados}")
    click.echo(f"Archivos Saltados:   {stats.saltados}")
    click.echo(f"Archivos Excluidos:  {stats.excluidos}")
    click.echo(
        click.style(
            f"Errores críticos:    {stats.errores}",
            fg="red" if stats.errores > 0 else "white",
        )
    )
    click.echo(click.style("=" * 30, fg="bright_black"))

    # Log del resumen
    logging.info(
        f"Sesión finalizada. Procesados: {stats.procesados}, Saltados: {stats.saltados}, Excluidos: {stats.excluidos}, Errores: {stats.errores}"
    )