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
    Checks if the path contains development environment files
    """
    # Files that define the project root
    indicadores = [
        "pyproject.toml",     # Poetry/Pip configuration
        "pyvenv.cfg",         # Virtual Environment configuration
        "requirements.txt",   # Dependencies list
        ".gitignore",         # Git repository
        "setup.py"            # Legacy package installation
    ]
    
    # Returns true if AT LEAST ONE exists in the path
    return any((ruta / archivo).exists() for archivo in indicadores)



@click.version_option(
    __version__,
    prog_name="File Organizer"
)
@click.command()
@click.option(
    "--ruta",
    help="Location to organize",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True, path_type=Path),
    required=True,
)
@click.option(
    "--recursive",
    is_flag=True,
    help="Process files within subfolders"
)
@click.option(
    "--config",
    type=click.Path(dir_okay=False, readable=True, path_type=Path),
    default=lambda: obtener_ruta_base() / "reglas.json",
    help="JSON file with organization rules",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Names of folders or files to exclude"
)
@click.option(
    "--only",
    multiple=True,
    help="Extensions to move only"
    )
@click.option(
    "--ignore-hidden",
    is_flag=True,
    help="Ignore hidden files and folders"
)
@click.option(
    "--log-file",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, path_type=Path),
    default= lambda: obtener_ruta_base() / "logs",
    help="Directory where logs will be saved.",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Log detail level.",
)
@click.option(
    "--apply",
    is_flag=True,
    help="Execute changes to disk."
)
@click.option(
    "--yes",
    "-y", is_flag=True,
    help="Skip manual confirmation."
)
def cli(
    ruta, ignore_hidden, recursive, exclude, only, config, log_file, log_level, apply, yes
):
    # Configuration for files/errors counter
    stats = Stats()
    
    # Execution timer configuration
    start_time = time.perf_counter()

    # Log configuration
    ruta_log_obj = Path(log_file)
    log_config(ruta_log_obj, log_level)
    logging.info(f"Starting file organizer {__version__}")
    
    # Resolve rules file path (PyInstaller/Local support)
    ruta_config_final = obtener_ruta_config(config)
    
    # Load rules
    reglas = leer_json(ruta_config_final, stats)

    if reglas is None:
        logging.error("Error reading reglas.json")
        click.echo("Error reading reglas.json")
        stats.registrar_error()
        return
    
    # Selection of specific and excluded files
    carpetas_destino = {k.lower() for k in reglas.keys()}
    exclude_set = {e.lower() for e in exclude}
    exclude_set.update(carpetas_destino) # Avoid organizing already organized folders
    only_set = set(only)
    
    
    # RESOLVE PATH (Convert "." or "../" into real paths like "C:/Users/Projects")
    ruta_objetivo = ruta.resolve()
    ruta_actual = Path.cwd().resolve()
    
    # FIRST FILTER
    if ruta_objetivo == ruta_actual:
        click.echo(click.style("\n[!] WARNING: Working directory detected.", fg="yellow", bold=True))
        if not click.confirm("Do you wish to continue at your own risk?"):
            return # Abort if user says No
    
    if es_raiz_proyecto(ruta_objetivo):
        click.echo(click.style("\n[!] SECURITY ERROR", fg="red", bold=True))
        click.echo(f"The location '{ruta_objetivo}' contains critical configuration files.")
        click.echo("Operation aborted to protect the virtual environment and project.")
        logging.error(f"Execution attempt blocked at project root: {ruta}")
        return 
    
    
    # SIMULATION MODE
    if not apply:
        click.echo(click.style("\n[SIMULATION MODE] No real changes will be made.", fg="blue", bold=True))
        for _ in simulacion(ruta_objetivo, reglas, recursive, exclude_set, only_set, ignore_hidden, stats, lista_archivos=None, stop_event=None):
            pass # We do nothing with the yield, forcing script execution
        click.echo(click.style("\nTo apply these changes, use the flag: --apply", fg="yellow"))
    
    # EXECUTION MODE
    else:
        # Extra confirmation before applying
        if yes or click.confirm(click.style(f"Confirm applying changes in {ruta_objetivo}?", fg="red", bold=True)):
            for _ in mover_archivos(
                ruta_objetivo, reglas, recursive, exclude_set, only_set, ignore_hidden, stats, lista_archivos=None, stop_event=None
            ):
                pass # Same as simulation, ignore yield
        else:
            click.echo("Operation aborted.")
            return

    # Calculate total execution time
    end_time = time.perf_counter()
    tiempo_total = end_time - start_time

    # --- FINAL SUMMARY ---
    click.echo(click.style("\n" + "=" * 30, fg="bright_black"))
    click.echo(click.style("OPERATION SUMMARY", bold=True))
    click.echo(f"Total Time:       {tiempo_total:.4f} sec")
    click.echo(f"Files Processed:  {stats.procesados}")
    click.echo(f"Files Skipped:    {stats.saltados}")
    click.echo(f"Files Excluded:   {stats.excluidos}")
    click.echo(
        click.style(
            f"Critical Errors:  {stats.errores}",
            fg="red" if stats.errores > 0 else "white",
        )
    )
    click.echo(click.style("=" * 30, fg="bright_black"))

    # Summary log
    logging.info(
        f"Session finished. Processed: {stats.procesados}, Skipped: {stats.saltados}, Excluded: {stats.excluidos}, Errors: {stats.errores}"
    )