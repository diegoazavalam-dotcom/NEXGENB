/**
 * ZONA ROJA 3: LOG DE EVENTOS CRÍTICOS
 * Maneja la visualización de incidencias pendientes y el cierre de las mismas.
 */
const AlertsLog = {
    name: "AlertsLog",
    containerId: "log-incidencias-container",
    lastCount: 0,

    /**
     * update() es llamado por el ScadaEngine cada segundo
     * @param {Array} sensores - Datos de telemetría para detectar estados de alarma
     */
    update(sensores) {
        // Filtramos solo los sensores que están fuera de rango para la alerta visual rápida
        const sensoresEnAlerta = sensores.filter(s => s.v < s.ll || s.v > s.lh);
        
        // Actualizamos el contador en el header (el círculo rojo que viste en el index)
        const badge = document.getElementById('count-alertas');
        if (badge) {
            badge.innerText = sensoresEnAlerta.length;
            badge.classList.toggle('animate-pulse', sensoresEnAlerta.length > 0);
        }

        // Si el número de alertas cambió, refrescamos la lista detallada de la base de datos
        if (sensoresEnAlerta.length !== this.lastCount) {
            this.refrescarLista();
            this.lastCount = sensoresEnAlerta.length;
        }
    },

    /**
     * Obtiene las incidencias reales desde la base de datos
     */
    async refrescarLista() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        try {
            const res = await fetch('/api/incidencias/pendientes');
            const incidencias = await res.json();

            if (!incidencias || incidencias.length === 0) {
                container.innerHTML = `
                    <div class="text-center p-8 opacity-20">
                        <div class="text-4xl mb-2">✅</div>
                        <div class="text-[9px] font-black uppercase tracking-widest">Sistema Seguro</div>
                    </div>`;
                return;
            }

            container.innerHTML = incidencias.map(inc => `
                <div class="glass-panel p-4 rounded-2xl border-l-4 ${inc.tipo === 'ALTO' ? 'border-red-500' : 'border-blue-500'} bg-white/5 group hover:bg-white/10 transition-all">
                    <div class="flex justify-between items-start mb-2">
                        <span class="text-[10px] font-black text-white uppercase">${inc.sensor_id}</span>
                        <span class="text-[8px] font-mono text-gray-500">${inc.fecha.split(' ')[1]}</span>
                    </div>
                    <div class="text-[11px] text-gray-300 mb-3">
                        Detectado: <span class="text-white font-bold">${inc.valor_detectado}</span> 
                        <span class="opacity-50">(Umbral: ${inc.umbral_limite})</span>
                    </div>
                    <button onclick="AlertsLog.atender('${inc.id}')" 
                        class="w-full py-2 bg-white/5 hover:bg-white/20 border border-white/10 rounded-xl text-[9px] font-black uppercase tracking-widest text-gray-400 hover:text-white transition-all">
                        Atender Incidencia
                    </button>
                </div>
            `).join('');

        } catch (e) {
            console.error("❌ Error recuperando incidencias:", e);
        }
    },

    /**
     * Cierra una incidencia con el comentario del operador
     */
    async atender(id) {
        const comentario = prompt("📋 BITÁCORA DE MANTENIMIENTO\nDescriba la acción correctiva:");
        if (!comentario || comentario.length < 3) return;

        try {
            const res = await fetch('/api/incidencias/atender', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id, comentario: comentario })
            });

            const result = await res.json();
            
            // Aquí manejamos el posible Error 500 del servidor de forma silenciosa
            if (res.ok || result.success) {
                console.log("✅ Incidencia cerrada correctamente");
            } else {
                console.warn("⚠️ El servidor reportó un error, pero forzamos refresco visual.");
            }
            
            // En cualquier caso, refrescamos la lista para dar feedback al usuario
            this.refrescarLista();

        } catch (e) {
            console.error("🔥 Error crítico en atender():", e);
            // Si hay error de red, igual refrescamos para limpiar la UI
            this.refrescarLista();
        }
    }
};