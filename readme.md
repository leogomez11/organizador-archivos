# Organizador Inteligente de Archivos

Herramienta desarrollada en Python para organizar archivos automáticamente en carpetas según reglas definidas por el usuario mediante un archivo JSON.

El proyecto incluye:
- Una versión de línea de comandos (CLI)
- Una versión con interfaz gráfica (GUI)

---

## Características
- Organización automática de archivos por extensión
- Reglas personalizables mediante `reglas.json`
- Modo simulación (no modifica el disco)
- Organización recursiva de subcarpetas
- Exclusión de carpetas y archivos
- Prevención de sobrescritura
- CLI y GUI separadas

---

## Estructura del proyecto

```
organizador-archivos/
│
├── cli/
│   └── main_cli.py
│
├── gui/
│   └── main_gui.py
│
├── reglas.json
├── README.md
├── LICENSE
└── .gitignore
```

---

## Requisitos
- Python 3.10 o superior
- Sistema operativo: Windows, Linux o macOS

---

## Uso – CLI

Ejemplo básico:

```bash
python main_cli.py --ruta "C:\Usuarios\Nombre\Descargas"
```

Modo simulación (por defecto):

```bash
python main_cli.py --ruta "C:\Descargas"
```

Aplicar cambios reales:

```bash
python main_cli.py --ruta "C:\Descargas" --apply
```

---

## Reglas (`reglas.json`)

Ejemplo:

```json
{
  "Imagenes": [".jpg", ".png"],
  "Documentos": [".pdf", ".docx"]
}
```

Si no se desean reglas personalizadas:

```json
{}
```

---

## Interfaz Gráfica (GUI)

La versión GUI permite organizar carpetas mediante una interfaz visual, sin necesidad de utilizar la línea de comandos.

---

## Estado del proyecto

Proyecto en desarrollo.
Las versiones ejecutables (`.exe`) se publicarán más adelante mediante GitHub Releases.

