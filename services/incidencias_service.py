# services/incidencias_service.py
import database

class IncidenciasService:
    @staticmethod
    def obtener_recientes(limit=20):
        """Consulta las últimas incidencias registradas"""
        try:
            conn = database.get_db_connection()
            rows = conn.execute("""
                SELECT * FROM log_incidencias 
                ORDER BY fecha DESC LIMIT ?
            """, (limit,)).fetchall()
            conn.close()
            return [dict(ix) for ix in rows]
        except Exception as e:
            print(f"⚠️ Nota: Tabla de incidencias no lista o vacía")
            return []

    @staticmethod
    def marcar_como_atendida(incidencia_id, comentario, usuario):
        """Versión Evolucionada: Registra el CIERRE con trazabilidad técnica"""
        try:
            conn = database.get_db_connection()
            conn.execute("""
                UPDATE log_incidencias 
                SET atendido = 1, 
                    comentario_cierre = ?, 
                    usuario_cierre = ?, 
                    fecha_cierre = DATETIME('now', 'localtime')
                WHERE id = ?
            """, (comentario, usuario, incidencia_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error en Service: {e}")
            return False
