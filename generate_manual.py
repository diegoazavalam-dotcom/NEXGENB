import os
from xhtml2pdf import pisa

html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    @page {{
        size: letter;
        margin: 2cm;
        @frame footer {{
            -pdf-frame-content: footerContent;
            bottom: 1cm;
            margin-left: 1cm;
            margin-right: 1cm;
            height: 1cm;
        }}
    }}
    body {{ font-family: Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #333; }}
    h1 {{ color: #1e3a8a; text-align: center; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; font-size: 24pt; }}
    h2 {{ color: #2563eb; margin-top: 30px; border-bottom: 1px solid #ccc; padding-bottom: 5px; font-size: 16pt; }}
    h3 {{ color: #3b82f6; font-size: 13pt; }}
    p {{ margin-bottom: 15px; text-align: justify; }}
    .badge {{ background-color: #f3f4f6; border: 1px solid #d1d5db; padding: 2px 5px; border-radius: 3px; font-family: monospace; font-size: 9pt; }}
    .note {{ background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 10px; font-style: italic; font-size: 10pt; }}
    .warning {{ background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 10px; font-style: italic; font-size: 10pt; }}
    .center {{ text-align: center; }}
    ul {{ margin-bottom: 15px; }}
    li {{ margin-bottom: 5px; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background-color: #f3f4f6; font-weight: bold; }}
    .icon {{ font-size: 14pt; }}
    .image-container {{ text-align: center; margin: 20px 0; }}
    img {{ max-width: 100%; border-radius: 8px; border: 1px solid #ccc; }}
</style>
</head>
<body>
    <div id="footerContent" style="text-align: right; font-size: 9pt; color: #888;">
        ZoLe Automatización - Página <pdf:pagenumber> de <pdf:pagecount>
    </div>

    <h1>Manual de Operación<br>NexGen SCADA v7.5</h1>
    
    <div class="note">
        <strong>Documento Oficial:</strong> Este manual detalla los procedimientos operativos, de administración y análisis del ecosistema SCADA ZoLe. Diseñado bajo estándares industriales de la norma ISA-18.2.
    </div>

    <h2>1. Arquitectura y Acceso al Sistema</h2>
    <p>El sistema opera en una red industrial cerrada. Para acceder al portal principal, abra su navegador e ingrese a la dirección IP del servidor central. El inicio de sesión está protegido por credenciales de acceso vinculadas al nivel de responsabilidad de cada operador en la planta.</p>
    <h3>Roles de Autenticación</h3>
    <ul>
        <li><strong>SUPER_ADMIN / ADMIN:</strong> Acceso total. Permite crear nodos, configurar extractores, visualizar auditorías y realizar respaldos.</li>
        <li><strong>OPERADOR:</strong> Acceso restringido a monitoreo y comandos de planta (START/STOP) sobre los equipos, sin privilegios de configuración de red.</li>
    </ul>

    <h2>2. Ecosistema HMI: Barra de Navegación Universal</h2>
    <p>El sistema cuenta con un modelo <em>"Single Page Application Feel"</em>. La barra superior contiene las herramientas críticas de navegación, estables en todo el ecosistema:</p>
    <table>
        <tr><th>Icono</th><th>Módulo</th><th>Funcionalidad y Permisos</th></tr>
        <tr><td class="center">🛡️</td><td>Usuarios</td><td>(Admin) Gestión de cuentas y contraseñas.</td></tr>
        <tr><td class="center">🔔</td><td>Telegram</td><td>Configuración del bot de notificaciones instantáneas de alarmas.</td></tr>
        <tr><td class="center">🏠</td><td>Dashboard</td><td>Vista principal del mapa de planta y estatus general del PLC.</td></tr>
        <tr><td class="center">📊</td><td>Analítica</td><td>Reportes históricos, gráficas multivariables y exportación a Excel.</td></tr>
        <tr><td class="center">💨</td><td>Extractores</td><td>Control operativo de la Celda de Preformado (HVAC).</td></tr>
        <tr><td class="center">⚙️ / +</td><td>Activo Nuevo</td><td>(Admin) Creación de Nodos o Extractores dinámicos.</td></tr>
        <tr><td class="center">💾</td><td>Backup</td><td>(Admin) Descarga instantánea de la base de datos completa.</td></tr>
        <tr><td class="center">🔍</td><td>Auditoría</td><td>(Admin) Bitácora de trazabilidad de comandos operativos.</td></tr>
        <tr><td class="center">❓</td><td>Ayuda</td><td>Descarga de este manual en formato PDF.</td></tr>
    </table>

    <pdf:nextpage />

    <h2>3. Dashboard y Mapa de Planta</h2>
    <p>La vista principal <span class="badge">🏠</span> muestra el layout interactivo de la fábrica. Sobre el plano físico se superponen los nodos de telemetría dinámica. Esta vista le permite conocer el estado situacional global de las operaciones en un solo vistazo.</p>
    
    <div class="image-container">
        <img src="C:\\Users\\betoo\\.gemini\\antigravity\\brain\\44a5cd25-ea41-49bb-96df-692dccd4a857\\scada_dashboard_1778542446590.png" width="500">
    </div>

    <ul>
        <li><strong>Monitoreo de Nodos:</strong> Cada nodo muestra variables en tiempo real. Colores de alerta indican si una variable excede los límites (verde = Normal, rojo = Alarma).</li>
        <li><strong>Creación de Nodos:</strong> Haga clic en <em>Nodo +</em> (solo Administradores). Podrá ubicar libremente el nodo en el plano, asignarle un TAG industrial y vincularlo a un Data Block (DB) de Siemens S7.</li>
        <li><strong>Heartbeat PLC:</strong> En la esquina superior izquierda se verifica la conexión al PLC S7 (ESTABLE / DESCONECTADO) en tiempo real (Polling de 2000ms). Si esta conexión se pierde, el sistema alertará inmediatamente.</li>
        <li><strong>Arrastre de Nodos:</strong> (Admin) Con "Alt + Click" se pueden reposicionar los nodos en el plano para reflejar cambios físicos de la planta.</li>
    </ul>

    <h2>4. Control de Extractores de Gas (HVAC)</h2>
    <p>Al hacer clic en el icono <span class="badge">💨</span>, se accede a la interfaz de la Celda de Preformado. Aquí se gestionan los extractores que previenen la acumulación de gases.</p>
    
    <div class="image-container">
        <img src="C:\\Users\\betoo\\.gemini\\antigravity\\brain\\44a5cd25-ea41-49bb-96df-692dccd4a857\\scada_extractor_1778542462683.png" width="500">
    </div>

    <p><strong>Procedimiento Operativo:</strong></p>
    <ol>
        <li>Seleccione el modo del equipo: <strong>AUTO</strong> (depende de lógica de PLC remota y procesos de la máquina de preformado) o <strong>MANUAL</strong> (control directo por HMI).</li>
        <li>En modo MANUAL, los botones <strong>START</strong> (Verde) y <strong>STOP</strong> (Gris) estarán habilitados. Haga clic en ellos para arrancar o detener físicamente los motores.</li>
        <li><strong>Feedback Visual:</strong> El ventilador animado en verde girando indica que el equipo está en operación física real (Running feedback). En gris estático indica detenido.</li>
    </ol>
    <div class="warning">
        <strong>Gestión de Alarmas Térmicas:</strong> Si el bloque del PLC dispara una falla térmica (sobrecarga del motor), el extractor parpadeará en ROJO con el mensaje "FALLA TÉRMICA". Aparecerá el botón <em>RESET FALLA (ACK)</em>. Primero se debe atender la falla física en el guardamotor y luego presionar Reset en el HMI.
    </div>

    <pdf:nextpage />

    <h2>5. Analítica de Datos y Reportes</h2>
    <p>En el módulo <span class="badge">📊</span> se centraliza la telemetría histórica. Permite a los ingenieros y gerentes diagnosticar problemas pasados y optimizar los recursos energéticos o de mantenimiento.</p>

    <div class="image-container">
        <img src="C:\\Users\\betoo\\.gemini\\antigravity\\brain\\44a5cd25-ea41-49bb-96df-692dccd4a857\\scada_analytics_1778542475659.png" width="500">
    </div>

    <ul>
        <li><strong>Selección Multivariable:</strong> Puede seleccionar múltiples sensores de la lista manteniendo presionada la tecla <code>Ctrl</code> (o <code>Cmd</code>) y elegir el rango de fechas a inspeccionar.</li>
        <li><strong>Gráfica Interactiva:</strong> El sistema superpondrá automáticamente las tendencias para análisis cruzado de presiones, temperaturas, y flujos. Puede hacer zoom en áreas específicas.</li>
        <li><strong>Exportación a Master Excel:</strong> Permite generar un archivo `.xlsx` estandarizado, con todos los registros brutos en el periodo de tiempo, útil para auditorías de calidad o validaciones ISO.</li>
    </ul>

    <h2>6. Trazabilidad y Seguridad</h2>
    <p>El sistema cuenta con un registro inmutable de acciones. Cada comando ejecutado por un operador o administrador queda estrictamente registrado.</p>
    <p><strong>Auditoría (<span class="badge">🔍</span>):</strong> Cada clic en <code>START</code>, <code>STOP</code>, o <code>RESET</code> queda guardado con:</p>
    <ul>
        <li><strong>Usuario:</strong> Quién ejecutó la acción.</li>
        <li><strong>Timestamp:</strong> Fecha y hora exacta (con milisegundos).</li>
        <li><strong>Variable:</strong> Qué TAG o equipo fue manipulado.</li>
        <li><strong>Valores:</strong> Valor Anterior y Valor Nuevo, permitiendo rastrear el antes y después de cada intervención humana.</li>
    </ul>

</body>
</html>
"""

def generate_pdf():
    pdf_dir = os.path.join("C:\\SCADA_FINAL_1", "static", "pdf")
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
        
    output_path = os.path.join(pdf_dir, "manual.pdf")
    
    with open(output_path, "w+b") as result_file:
        pisa_status = pisa.CreatePDF(
            html_content,                
            dest=result_file
        )

    if pisa_status.err:
        print("Error generando el PDF:", pisa_status.err)
    else:
        print("Manual PDF generado con éxito en:", output_path)

if __name__ == "__main__":
    generate_pdf()
