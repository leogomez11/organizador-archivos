import ctypes
from gui.gui_simple import App

if __name__ == "__main__":
    #Instrucción clave para corregir el DPI
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    
    app_id = "leonel_gomez.organizador_archivos.1.0.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    
    #Iniciar la aplicación
    app = App()
    app.mainloop()