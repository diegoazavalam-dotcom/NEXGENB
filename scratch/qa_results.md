# NexGen SCADA v7 - Reporte de Pruebas de QA de Consistencia y Ciclo de Alarmas
**Fecha y Hora:** 2026-05-22 13:59:29
**Entorno:** Local Host (Windows venv)

### 1. Vista 1: HMI Dashboard (`/api/telemetria`)
- **Estado:** ✅ PASÓ
- **Consistencia de Estructura:** Correcta (Todos los campos requeridos presentes).
- **Sensores Detectados:** 12

### 2. Vista 2: Analytics & SPC (`/api/reportes/spc_cards`)
- **Estado:** ✅ PASÓ
- **Métricas estadísticas devueltas:** Sí (media, desviación, límites de control de procesos).
- **Sensores analizados:** 12

### 3. Vista 3: Extractores de Gas (`/api/extractores/estado`)
- **Estado:** ✅ PASÓ
- **Consistencia de Variables de Control:** Correcta (Id, zona, running, auto, falla).
- **Extractores leídos:** 8

### 4. Ciclo de Vida de Alertas (ISA-18.2)
#### 4.1 Trigger e Inserción en BD
- **Estado:** ✅ PASÓ
- **Detalle:** Alerta crítica insertada en `log_incidencias` para el sensor `QA_Sensor_Presion`.

#### 4.2 Registro y Visibilidad en el HMI
- **Estado:** ✅ PASÓ
- **Alerta Detectada ID:** 93
- **Estado Inicial:** `UNACK` (Sin Reconocer)

#### 4.3 Reconocimiento (ACK) de Alarma
- **Estado:** ✅ PASÓ
- **Detalle:** Solicitud HTTP POST exitosa. Estado transicionado de `UNACK` a `ACK` correctamente.

#### 4.4 Atención y Cierre de Alarma
- **Estado:** ✅ PASÓ
- **Detalle:** El operador atendió la alarma. Transicionó a `atendido = 1` y desapareció del panel en vivo del HMI.

### 5. Histéresis e Inmunidad al Parpadeo del Gateway (ISA-18.2)
#### 5.1 Activación del Candado
- **Estado:** ✅ PASÓ
- **Detalle:** Al superar 80.0°C, el motor del Gateway activó inmediatamente el estado `ALTO` en memoria.

#### 5.2 Lógica de Banda Muerta (Histéresis)
- **Estado:** ✅ PASÓ
- **Detalle:** El valor bajó a 79.0°C (dentro de los 2.0°C de deadband), el Gateway retuvo la alarma previniendo parpadeo (*chattering*).

#### 5.3 Normalización y Liberación de Candado
- **Estado:** ✅ PASÓ
- **Detalle:** Al bajar de 78.0°C (77.0°C), el candado se liberó automáticamente, permitiendo futuros disparos si se vuelve a calentar.
