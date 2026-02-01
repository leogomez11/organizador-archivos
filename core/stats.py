# core/stats.py

from dataclasses import dataclass, field
from collections import Counter

# Contador total de sucesos
@dataclass
class Stats:
    procesados: int = 0
    saltados: int = 0
    excluidos: int = 0
    errores: int = 0
    
    def registrar_procesados(self):
        self.procesados += 1
        
    def registrar_saltados(self):
        self.saltados += 1
        
    def registrar_excluidos(self):
        self.excluidos += 1
        
    def registrar_error(self):
        self.errores += 1
