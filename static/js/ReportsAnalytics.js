export const ReportsAnalytics = {
    procesarEstadisticas(values) {
        if (!values || values.length === 0) return { min: 0, max: 0, avg: 0, std: 0, puntos: 0 };
        
        const numericos = values.map(Number).filter(v => !isNaN(v));
        if (numericos.length === 0) return { min: 0, max: 0, avg: 0, std: 0, puntos: 0 };

        const suma = numericos.reduce((a, b) => a + b, 0);
        const promedio = suma / numericos.length;
        
        const varianza = numericos.reduce((a, b) => a + Math.pow(b - promedio, 2), 0) / numericos.length;
        const desviacion = Math.sqrt(varianza);

        return {
            min: Math.min(...numericos).toFixed(2),
            max: Math.max(...numericos).toFixed(2),
            avg: promedio.toFixed(2),
            std: desviacion.toFixed(2),
            puntos: numericos.length
        };
    },

    obtenerResumenCompleto(datasets) {
        // Ahora pasamos también el incidencias_count que viene del backend
        return datasets.map(d => ({
            sensor: d.sensor,
            incidencias: d.incidencias_count || 0, // <--- Nueva variable
            ...this.procesarEstadisticas(d.values)
        }));
    },

    interpretarDatos(stats) {
        const interpretaciones = [];
        const avg = parseFloat(stats.avg);
        const std = parseFloat(stats.std);
        const variabilidad = (std / avg) * 100;
        const numIncidencias = stats.incidencias || 0; // <--- Capturamos incidencias

        // 1. Análisis de Estabilidad
        if (variabilidad > 15) {
            interpretaciones.push(`⚠️ El sensor **${stats.sensor}** muestra alta inestabilidad (${variabilidad.toFixed(1)}% de variabilidad).`);
        } else if (variabilidad < 5 && stats.puntos > 10) {
            interpretaciones.push(`✅ Proceso estable en **${stats.sensor}**.`);
        }

        // 2. NUEVO: Correlación con Incidencias (Tracking)
        if (numIncidencias > 0) {
            interpretaciones.push(`🚩 El sistema registró **${numIncidencias} eventos** fuera de umbral para **${stats.sensor}**.`);
            
            // Si hay inestabilidad Y hay incidencias, sugerimos causa-raíz
            if (variabilidad > 12) {
                interpretaciones.push(`⚠️ Existe correlación crítica entre la fluctuación eléctrica/térmica y los disparos del log.`);
            }
        }

        return interpretaciones;
    },
};