#gui_simple.py

#--- IMPORTACIONES ---#
import tkinter as tk
import threading
from pathlib import Path
from tkinter import messagebox, filedialog, ttk
from tkinter import scrolledtext as st

from core.engine import iterar_archivos, mover_archivos, simulacion
from core.stats import Stats


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        #self.tk.call("tk", "scaling", 1.0)
        
        # Colores del tema
        COLOR_BG = "#FFFFFF"      # Blanco fondo
        COLOR_PRIMARY = "#FFC107" # Amarillo moderno (Amber)
        COLOR_TEXT = "#212529"    # Gris oscuro/negro
        COLOR_SURFACE = "#F8F9FA" # Gris muy claro para bordes
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure(bg=COLOR_BG)
        
        # Fuente Global
        self.style.configure(".", font=("Segoe UI", 10), background=COLOR_BG, foreground=COLOR_TEXT)
        
        self.title("Organizador de archivos")
        self.geometry(self.calculo_geometry(550, 280))
        
        self.ruta_icono = Path(__file__).parent / "assets" / "mi_logo.ico"
        
        try:
            self.iconbitmap(self.ruta_icono)
        except Exception as e:
            print(f"No se pudo cargar el icono: {e}")
        
        # Configuración de Botones
        self.style.configure("TButton", padding=8, relief="flat", background="#495057", foreground="#FFFFFF", font=("Segoe UI", 10))
        self.style.map("TButton",
                       background=[("active", "#343A40"), ("disabled", "#ADB5BD")],
                       foreground=[("active", "#FFFFFF")])
        # Botón de Acción (Accent) - Amarillo con texto oscuro
        self.style.configure("Accent.TButton", 
                            background=COLOR_PRIMARY, 
                            foreground=COLOR_TEXT, 
                            font=("Segoe UI", 10, "bold"))
        self.style.map("Accent.TButton", 
                       background=[("active", "#FFCA28")])
        
        # Barra de progreso (Acorde al amarillo)
        self.style.configure(
            "Verde.Horizontal.TProgressbar",
            troughcolor="#E0E0E0",   
            background=COLOR_PRIMARY,
            bordercolor="#212529",
            lightcolor=COLOR_PRIMARY,
            darkcolor=COLOR_PRIMARY,
            thickness=18,            
            borderwidth=1
        )

        # Estilo para Labels y Frames
        self.style.configure("TLabel", background=COLOR_BG)
        self.style.configure("TFrame", background=COLOR_BG)
        
        
        #Datos por defecto para alojar en funciones
        self.EXCLUDE = {
            # Windows: Papelera y Sistema
            "$recycle.bin", 
            "recycler", 
            "system volume information", 
            "msocache",
            "config.msi",
    
            # macOS/Linux: Papelera y Temporales
            ".trashes", 
            ".trash", 
            ".spotlight-v100", 
            ".fseventsd",
            "lost+found",
    
            # Archivos de volcado y paginación (Opcional)
            "pagefile.sys", 
            "hiberfil.sys", 
            "dumpstack.log.tmp",
            
            # Directorios de desarrollo/entorno
            "venv", "lib", "scripts", "include", ".git", "__pycache__",
    
            # Archivos de configuración crítica
            "pyproject.toml", "pyvenv.cfg"
        }
        self.ONLY = []
        self.IGNORE_HIDDEN = True
        self.RECURSIVE = False
        self.REGLAS = {
            'Imagenes': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'],
            'Videos': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.webm'],
            'Audios': ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'],
            'Documentos': ['.txt', '.doc', '.docx', '.odt', '.rtf', '.md'],
            'Hojas_calculo': ['.xls', '.xlsx', '.ods', '.csv'],
            'Presentaciones': ['.ppt', '.pptx', '.odp'],
            'Pdf': ['.pdf'],
            'Comprimidos': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
            'Ejecutables': ['.exe', '.msi', '.bat', '.cmd', '.sh'],
            'Codigo': ['.py', '.js', '.java', '.html', '.css', '.json', '.xml', '.yaml'],
            'Bases_datos': ['.db', '.sqlite', '.mdb', '.accdb'],
            'Fuentes': ['.ttf', '.otf', '.woff', '.woff2']
        }
        
        
        
        #Cancelar evento para agregar un boton cancelar y evitar errores
        self.cancelar_evento = threading.Event()
        
        self._crear_widgets()
    
    
    
    #Funcion para calcular el centro de la pantalla
    def calculo_geometry(self, ancho, alto):
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()
        
        x = (ancho_pantalla // 2) - (ancho // 2)
        y = (alto_pantalla // 2) - (alto // 2) - 30
        return f"{ancho}x{alto}+{x}+{y}"



    #Funcion para crear los widgets de la interfaz
    def _crear_widgets(self):
        # Contenedor principal con margen
        self.columnconfigure(0, weight=1) #Permite expansión horizontal
        self.rowconfigure(0, weight=1) #Permite expansión vertical
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1) #El entry se expandirá
        
        # Título
        ttk.Label(
            main_frame, 
            text="Organizador de Archivos", 
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")
    
        # Selección de Ruta
        ttk.Label(main_frame, text="Carpeta a procesar:").grid(row=1, column=0, sticky="w")
        
        #Aqui se colocará la ruta a organizar
        self.ruta_var = tk.StringVar(value=str(Path.home() / "Desktop"))
        entry_ruta = ttk.Entry(main_frame, textvariable=self.ruta_var, width=45)
        entry_ruta.grid(row=2, column=0, padx=(0, 10), pady=10, sticky="ew")
    
        boton_examinar = ttk.Button(main_frame, text="🔍 Cambiar", command=self._seleccion_ruta)
        boton_examinar.grid(row=2, column=1, sticky="e")
        
        #Separador visual
        ttk.Separator(main_frame, orient="horizontal").grid(row=3, column=0, columnspan=2, pady=15, sticky="ew")
        
        #Botones de acción
        botones_frame = ttk.Frame(main_frame)
        botones_frame.grid(row=4, column=0, columnspan=2, sticky="ew")
    
        #Configurar pasos para que los botones se distribuyan
        botones_frame.columnconfigure(0, weight=1)
        botones_frame.columnconfigure(1, weight=1)
        
        
        self.boton_simular = ttk.Button(
            botones_frame, 
            text="Simular Proceso", 
            command=self.abrir_simulacion
        )
        self.boton_simular.grid(row=0, column=0, padx=5, sticky="ew")
    
        self.boton_mover = ttk.Button(
            botones_frame, 
            text="🚀 Iniciar Organización", 
            command=self.abrir_organizacion, 
            style="Accent.TButton"
        )
        self.boton_mover.grid(row=0, column=1, padx=5, sticky="ew")
    
        
        
    #Funcion para boton_examinar
    def _seleccion_ruta(self):
        seleccion = filedialog.askdirectory(initialdir=str(self.ruta_var.get()), title="Seleccionar Carpeta")
        if seleccion:
            self.ruta_var.set(seleccion)
    
    
    #Funcion para boton_simular
    def abrir_simulacion(self):
        """
        Funcion: Abrir la ventana de simulacion. Utilizada por 'boton_simular'
        """
        Ventana_proceso(self, modo="simular")
        

    def abrir_organizacion(self):
        """
        Funcion: Abrir la ventana de organizacion. Utilizada por 'boton_mover'
        """
        Ventana_proceso(self, modo="organizar")
        
    
    
    def _alternar_botones(self, estado="normal"):
        """Habilita o deshabilita los botones principales"""
        self.boton_simular.config(state=estado)
        self.boton_mover.config(state=estado)
        
    
    def _progressbar_ejecutar_proceso(self, modo="organizar", ventana_hija=None):
        """
        Funcion: itera archivos, se encarga de simular/mover archivos en el hilo secundario
        y actualiza lo que se muestra en la interfaz (hilo primario) con 'self.after()'
        """
        
        #BLOQUEO
        self._alternar_botones("disabled")
        
        try:
            ruta_base = Path(self.ruta_var.get())
            local_stats = Stats()
            
            archivos_lista = list(iterar_archivos(
                base=ruta_base,
                recursive=self.RECURSIVE,
                exclude=self.EXCLUDE,
                only=self.ONLY,
                ignore_hidden=self.IGNORE_HIDDEN,
                stats= local_stats
            ))
    
            total = len(archivos_lista)
            
            if total == 0:
                self.after(0, lambda: messagebox.showinfo("Aviso", "No hay archivos para procesar."))
                return 
            
            #Asignamos el numero de progreso
            self.after(0, lambda t=total: self._init_progreso(ventana_hija, t))
            
    
            # 2. Seleccionar motor (Generador)
            motor = mover_archivos if modo == "organizar" else simulacion
    
            # 3. Consumir el generador y actualizar UI
            gen = motor(
                base=ruta_base,
                reglas=self.REGLAS,
                recursive=self.RECURSIVE,
                exclude=self.EXCLUDE,
                only=self.ONLY,
                ignore_hidden=self.IGNORE_HIDDEN,
                stats= local_stats,
                lista_archivos = archivos_lista,
                stop_event = self.cancelar_evento
            )

            for i, mensaje in enumerate(gen, 1):
                #Verificacion de cancelacion
                if self.cancelar_evento.is_set():
                    self.after(0, lambda: ventana_hija.area_log.insert(tk.END, "\n[!] PROCESO CANCELADO POR EL USUARIO.\n"))
                    break
            
                #Actualizacion segura del UI
                self.after(0, lambda m=mensaje, v=i: self._actualizar_gui_hija(ventana_hija, ventana_hija.area_log, m, v, total))
            
        except Exception as e:
           self.after(0, lambda ex=e: messagebox.showerror("Error Crítico", f"{ex}"))
        finally:
            self.after(0, lambda: self._alternar_botones("normal"))
            
            if not self.cancelar_evento.is_set():
                self.after(0, lambda: messagebox.showinfo(
                    "Proceso", f"{modo.capitalize()} finalizada."
                    ))

    def _init_progreso(self, ventana, total):
        """
        Asignamos el numero total de archivos a procesar y procesados.
        definimos la funcion para evitar interferir entre el hilo principal y secundario
        """
        ventana.progreso["value"] = 0
        ventana.progreso["maximum"] = total
        ventana.label_estado.config(text=f"Procesando: 0/{total}")
    
    
    def _actualizar_gui_hija(self, ventana, log, msj, val, tot):
        """Metodo axuliar para ejecutar el hilo principal"""
        try:
            log.insert(tk.END, f"{msj}\n")
            log.see(tk.END)
            if val <= tot:
                ventana.progreso["value"] = val
                ventana.label_estado.config(text=f"Procesando: {val}/{tot}")
                ventana.update_idletasks()
                ventana.update()
        except tk.TclError:
            pass # La ventana se cerró
    
    
    def _cancelar_proceso(self):
        """Activa la señal de parada"""
        self.cancelar_evento.set()
    
    
    def _iniciar_hilo(self, modo, ventana_hija):
        """
        Inicia el hilo secundario (procesos sub-interfaz)
        """
        #reinicia el evento antes de empezar
        self.cancelar_evento.clear()
        
        #Restringimos la x al metodo de cancelar
        ventana_hija.protocol("WM_DELETE_WINDOW", ventana_hija._al_cerrar)
        
        t = threading.Thread(
            target=self._progressbar_ejecutar_proceso,
            args=(modo, ventana_hija)
        )
        t.start()



class Ventana_proceso(tk.Toplevel):
    def __init__(self, padre, modo):
        super().__init__(padre)
        self.padre = padre
        self.configure(bg="#FFFFFF")
        
        self.title("Simulación" if modo == "simular" else "Organización")
        self.geometry(padre.calculo_geometry(650, 520))
        self.transient(padre) #Ventana asociada a la principal
        self.iconbitmap(padre.ruta_icono) #Seleccion del icono
        self.focus_force() # Forzar el foco inicial
        
        
        self.label_estado = ttk.Label(self, text="Preparando proceso...", font=("Segoe UI", 10))
        self.label_estado.pack(side="top", pady=(15, 5))
        
        self.progreso = ttk.Progressbar(
            self,
            orient="horizontal",
            mode="determinate",
            style="Verde.Horizontal.TProgressbar"
        )
        self.progreso.pack(side="top", fill="x", padx=40, pady=5)
        
        # Botón Cancelar
        self.btn_cancelar = ttk.Button(self, text="Cancelar proceso", command=padre._cancelar_proceso)
        self.btn_cancelar.pack(side="bottom", pady=20)
        
        self.area_log = st.ScrolledText(
            self, 
            font=("Consolas", 10), 
            bg="#FDFDFD", 
            fg="#333333", 
            padx=10, 
            pady=15,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#E9ECEF" # Borde sutil
        )
        self.area_log.pack(expand=True, fill="both", padx=20, pady=10)
        
        #Limpieza: Borra contenido previo por si hay reejecucion
        self.area_log.configure(state='normal')
        self.area_log.delete("1.0", tk.END)
        self.after(
            0,
            lambda: self.area_log.insert(
                tk.END, f"--- Iniciando {modo} ---\n"
            )
        )
        
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)
        
        try:
            if modo == "simular":
                padre._iniciar_hilo(modo="simular", ventana_hija=self)
            else:
                padre._iniciar_hilo(modo="organizar", ventana_hija=self)
                
        except Exception as e:
            print("ERROR EN HILO GUI:", e)
            import traceback
            traceback.print_exc()
        
    
    def _al_cerrar(self):
        self.padre._cancelar_proceso() #Detiene el hilo
        self.padre._alternar_botones("normal") #Libera botones
        self.grab_release()
        self.padre.focus_force() # Devolver el foco al padre
        self.destroy()
