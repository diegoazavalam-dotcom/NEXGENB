from abc import ABC, abstractmethod

class IDriver(ABC):
    """
    Interfaz abstracta que obliga a todos los drivers (Siemens, Modbus, etc.)
    a tener los mismos métodos. Esto es ORO para la escalabilidad.
    """
    
    @abstractmethod
    def conectar(self) -> bool:
        """Debe retornar True si hay conexión, False si falla"""
        pass

    @abstractmethod
    def leer_sensor(self, direccion, tipo, limite) -> float:
        """Debe retornar el valor ya procesado"""
        pass
    
    @abstractmethod
    def desconectar(self):
        pass