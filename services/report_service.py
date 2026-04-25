import pandas as pd
from io import BytesIO
from datetime import datetime
import sqlite3

class ReportService:
    @staticmethod
    def generar_excel_sensores(db_path, lista_sensores, fecha_inicio=None, fecha_fin=None):
        """
        REPORTE 1 Y 2: Telemetría (Individual e Histórica)
        Maneja tanto los últimos 50 valores como el rango de fechas masivo.
        """
        output = BytesIO()
        try:
            with sqlite3.connect(db_path) as conn:
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    for sensor in lista_sensores:
                        if not fecha_inicio or not fecha_fin:
                            # Caso 1: Telemetría rápida (últimos 50 valores)
                            query = """
                                SELECT fecha as Timestamp, nombre_sensor as Sensor, valor as Valor 
                                FROM historial_sensores 
                                WHERE nombre_sensor = ? 
                                ORDER BY id DESC LIMIT 50
                            """
                            params = (sensor,)
                        else:
                            # Caso 2: Reporte Histórico por fechas
                            query = """
                                SELECT fecha as Timestamp, nombre_sensor as Sensor, valor as Valor 
                                FROM historial_sensores 
                                WHERE nombre_sensor = ? AND fecha BETWEEN ? AND ?
                                ORDER BY fecha ASC
                            """
                            params = (sensor, fecha_inicio, fecha_fin)
                        
                        df = pd.read_sql_query(query, conn, params=params)
                        if not df.empty:
                            sheet_name = str(sensor)[:30] # Límite de Excel para nombres de hoja
                            df.to_excel(writer, index=False, sheet_name=sheet_name)
            
            output.seek(0)
            return output
        except Exception as e:
            print(f"❌ Error en Reporte de Telemetría: {e}")
            return None

    @staticmethod
    def generar_excel_incidencias(db_path):
        """
        REPORTE 3: Auditoría de Incidencias (Audit Trail)
        Calcula duración y extrae comentarios para certificación industrial.
        """
        output = BytesIO()
        try:
            with sqlite3.connect(db_path) as conn:
                query = """
                    SELECT 
                        sensor_id as 'Sensor',
                        valor_detectado as 'Valor Detectado',
                        umbral_limite as 'Umbral',
                        fecha as 'Apertura',
                        fecha_cierre as 'Cierre',
                        usuario_cierre as 'Operador Responsable',
                        comentario_cierre as 'Acción Correctiva',
                        CASE 
                            WHEN fecha_cierre IS NOT NULL THEN 
                                ROUND((strftime('%s', fecha_cierre) - strftime('%s', fecha)) / 60.0, 2)
                            ELSE 0 
                        END as 'Duración (Minutos)'
                    FROM log_incidencias
                    WHERE atendido = 1
                    ORDER BY fecha DESC
                """
                df = pd.read_sql_query(query, conn)
                
                if df.empty:
                    df = pd.DataFrame(columns=['Sensor', 'Valor Detectado', 'Umbral', 'Apertura', 'Cierre', 'Operador Responsable', 'Acción Correctiva', 'Duración (Minutos)'])

                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Bitácora de Incidencias')
                    
                    # Auto-ajuste de columnas para un acabado profesional
                    worksheet = writer.sheets['Bitácora de Incidencias']
                    for i, col in enumerate(df.columns):
                        column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, column_len)
            
            output.seek(0)
            return output
        except Exception as e:
            print(f"❌ Error crítico en Reporte de Incidencias: {e}")
            return None