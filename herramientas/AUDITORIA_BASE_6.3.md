# REGISTRO DE AUDITORÍA TÉCNICA - NEXGEN V6.0
## ESTADO: BASE ESTABLE 6.3 (CERTIFICADA)

### 📂 ESTRUCTURA DE ARCHIVOS
- /static/js/config_widget.js -> Gestión de hardware y limpieza de formularios.
- /static/js/hmi_widget.js    -> Ciclo de telemetría (1.5s) y renderizado de nodos.
- /static/css/style.css       -> Animaciones de alerta (.sensor-alerta) y parpadeo.
- /templates/index.html       -> Estructura limpia, scripts cargados con defer.

### ⚙️ BACKEND (Python/Flask)
- Ruta /api/telemetry: Entrega JSON dinámico (n, e, u, l, val, x, y).
- Ruta /api/admin/borrar/<id>: Sincronizada con DELETE en frontend.
- Database: SQLite en MODO WAL con timeout de 30s (anti-bloqueo).

### 🚨 SISTEMA DE ALERTAS
- Lógica: Comparación (valor >= límite) en tiempo real.
- Efecto: Cambio de clase CSS a "sensor-alerta" con pulso rojo.
- UI: Modal dinámico con Sparklines (gráficas de historial) al hacer clic.

---
Firmado para Proyecto Spin-off Comercial. 2026.