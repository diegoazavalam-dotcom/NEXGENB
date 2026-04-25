/**
 * MÓDULO VISUAL 3: LOG DE INCIDENCIAS (IncidenciasUI)
 * Panel derecho con Búsqueda en Vivo, Autocompletado, Paginación y Cierres.
 */
const IncidenciasUI = {
    name: "IncidenciasUI",
    containerId: "log-incidencias-container",
    lastAlertCount: -1,
    isFetching: false,
    
    // Variables para Búsqueda y Paginación
    cacheIncidencias: [],
    paginaActual: 1,
    itemsPorPagina: 10,
    busqueda: "",

    init() {
        if (typeof ScadaEngine !== 'undefined') ScadaEngine.suscribir(this);
        this.sincronizarConBD();
    },

    update(sensores) {
        const alertasVivas = sensores.filter(s => parseFloat(s.val) > parseFloat(s.lh) || parseFloat(s.val) < parseFloat(s.ll));
        
        const badge = document.getElementById('count-alertas');
        if (badge) {
            badge.innerText = alertasVivas.length;
            if (alertasVivas.length > 0) badge.classList.add('animate-pulse', 'text-red-500');
            else badge.classList.remove('animate-pulse', 'text-red-500');
        }

        if (alertasVivas.length !== this.lastAlertCount) {
            this.lastAlertCount = alertasVivas.length;
            this.sincronizarConBD();
        }
    },

    async sincronizarConBD() {
        if (this.isFetching) return;
        this.isFetching = true;

        try {
            const res = await fetch('/api/incidencias/pendientes', { credentials: 'include' });
            if (res.ok) {
                this.cacheIncidencias = await res.json();
                this.actualizarAutocompletado();
                this.render(); // Dibujamos la vista con filtros
            }
        } catch (e) {
            console.warn("⚠️ Esperando BD para incidencias.");
        } finally {
            this.isFetching = false;
        }
    },

    // --- AUTOCOMPLETADO INTELIGENTE ---
    actualizarAutocompletado() {
        const terminos = new Set();
        // Extraemos sensores, fechas y valores únicos para sugerirlos
        this.cacheIncidencias.forEach(inc => {
            terminos.add(inc.sensor_id);
            if(inc.fecha) terminos.add(inc.fecha.split(' ')[0]); // Solo el día
            terminos.add(inc.valor_detectado.toString());
        });

        let datalist = document.getElementById('dl-incidencias');
        if (!datalist) {
            datalist = document.createElement('datalist');
            datalist.id = 'dl-incidencias';
            document.body.appendChild(datalist);
        }
        datalist.innerHTML = Array.from(terminos).map(t => `<option value="${t}">`).join('');
    },

    // --- FILTROS Y PAGINACIÓN ---
    setBusqueda(texto) {
        this.busqueda = texto.toLowerCase();
        this.paginaActual = 1; // Volver a la página 1 al buscar
        this.render();
    },

    cambiarPagina(delta) {
        this.paginaActual += delta;
        this.render();
    },

    // --- DIBUJADO UI (RENDER) ---
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // 1. Aplicar Búsqueda
        const filtradas = this.cacheIncidencias.filter(inc => {
            if (!this.busqueda) return true;
            // Unimos todos los datos de la alerta para buscar en cualquier campo
            const textoCompleto = `${inc.sensor_id} ${inc.valor_detectado} ${inc.umbral_limite} ${inc.tipo} ${inc.fecha}`.toLowerCase();
            return textoCompleto.includes(this.busqueda);
        });

        // 2. Calcular Paginación
        const totalPaginas = Math.ceil(filtradas.length / this.itemsPorPagina) || 1;
        if (this.paginaActual > totalPaginas) this.paginaActual = totalPaginas;
        if (this.paginaActual < 1) this.paginaActual = 1;

        const inicio = (this.paginaActual - 1) * this.itemsPorPagina;
        const fin = inicio + this.itemsPorPagina;
        const itemsPagina = filtradas.slice(inicio, fin);

        // 3. Construir el HTML
        let html = `
            <div class="sticky top-0 bg-[#0d1117] z-20 pb-3 mb-2 border-b border-white/5">
                <input type="text" list="dl-incidencias" placeholder="🔍 Buscar sensor, valor, fecha..." 
                    class="w-full bg-black/40 border border-white/10 text-white p-3 rounded-xl text-xs outline-none focus:border-red-500 transition-colors placeholder:text-gray-600 font-bold"
                    value="${this.busqueda}"
                    onkeyup="IncidenciasUI.setBusqueda(this.value)"
                    onchange="IncidenciasUI.setBusqueda(this.value)">
            </div>
        `;

        if (filtradas.length === 0) {
            html += `
                <div class="flex flex-col items-center justify-center p-8 opacity-40 border-2 border-dashed border-white/10 rounded-3xl mt-4">
                    <span class="text-3xl mb-3">🛡️</span>
                    <p class="text-[9px] font-black uppercase tracking-[0.2em] text-blue-400">Sin coincidencias</p>
                </div>`;
        } else {
            // Lista de Tarjetas
            html += `<div class="space-y-3">`;
            html += itemsPagina.map(inc => {
                const esAlto = inc.tipo === 'ALTO';
                const hora = inc.fecha && inc.fecha.includes(' ') ? inc.fecha.split(' ')[1] : '--:--:--';

                return `
                <div class="glass-panel p-4 rounded-2xl border-l-4 ${esAlto ? 'border-red-500' : 'border-blue-500'} bg-white/5 animate-in fade-in">
                    <div class="flex justify-between items-start mb-2">
                        <div class="flex flex-col">
                            <span class="text-[10px] font-black text-white uppercase tracking-tighter">${inc.sensor_id}</span>
                            <span class="text-[7px] font-bold text-red-500/80 uppercase tracking-widest">${inc.tipo} CRÍTICO</span>
                        </div>
                        <span class="text-[9px] font-mono text-gray-500 bg-black/40 px-2 py-1 rounded-md">${hora}</span>
                    </div>
                    
                    <div class="bg-black/20 p-2 rounded-xl mb-3 border border-white/5">
                        <p class="text-[10px] text-gray-400">Falla: <span class="text-white font-black">${inc.valor_detectado}</span></p>
                        <p class="text-[8px] text-gray-500 uppercase">Límite: ${inc.umbral_limite}</p>
                    </div>

                    <div class="flex gap-2">
                        <button onclick="IncidenciasUI.atender('${inc.id}')" 
                            class="flex-1 py-2 bg-red-600/10 hover:bg-red-600 text-red-500 hover:text-white border border-red-500/20 rounded-xl text-[8px] font-black uppercase transition-all">
                            Firmar 1
                        </button>
                        <button onclick="IncidenciasUI.atenderMasivo('${inc.sensor_id}')" 
                            class="flex-1 py-2 bg-yellow-500/10 hover:bg-yellow-500 text-yellow-500 hover:text-white border border-yellow-500/20 rounded-xl text-[8px] font-black uppercase transition-all">
                            Masivo
                        </button>
                    </div>
                </div>`;
            }).join('');
            html += `</div>`;
        }

        // 4. Controles de Paginación Fijos al fondo
        if (totalPaginas > 1) {
            html += `
                <div class="sticky bottom-0 bg-[#0d1117] z-20 pt-3 mt-4 border-t border-white/5 flex justify-between items-center">
                    <button onclick="IncidenciasUI.cambiarPagina(-1)" class="px-3 py-1 bg-white/5 hover:bg-white/10 rounded-lg text-white font-bold transition-all ${this.paginaActual === 1 ? 'opacity-30 pointer-events-none' : ''}">◄</button>
                    <span class="text-[9px] text-gray-400 font-mono tracking-widest">PÁG ${this.paginaActual} / ${totalPaginas}</span>
                    <button onclick="IncidenciasUI.cambiarPagina(1)" class="px-3 py-1 bg-white/5 hover:bg-white/10 rounded-lg text-white font-bold transition-all ${this.paginaActual === totalPaginas ? 'opacity-30 pointer-events-none' : ''}">►</button>
                </div>
            `;
        }

        container.innerHTML = html;
    },

    // --- ACCIONES CON LA BD ---
    async atender(id_incidencia) {
        const comentario = prompt("🚨 FIRMA INDIVIDUAL\nAcción tomada:");
        if (!comentario || comentario.trim().length < 3) return;
        try {
            const res = await fetch('/api/incidencias/atender', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id_incidencia, comentario: comentario.trim() })
            });
            if ((await res.json()).success) this.sincronizarConBD();
            else alert("⛔ Error en BD");
        } catch (e) { alert("❌ Fallo de red"); }
    },

    async atenderMasivo(sensor_id) {
        const comentario = prompt(`⚠️ CIERRE MASIVO ISO 9001\nSe cerrarán TODAS las alertas de: ${sensor_id}\n\nIndique la causa raíz general:`);
        if (!comentario || comentario.trim().length < 3) return;
        try {
            const res = await fetch('/api/incidencias/atender_masivo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sensor_id: sensor_id, comentario: comentario.trim() })
            });
            const data = await res.json();
            if (data.success) {
                alert(`✅ ${data.mensaje}`);
                this.sincronizarConBD();
            } else alert("⛔ Error en cierre masivo.");
        } catch (e) { alert("❌ Fallo de red"); }
    }
};

document.addEventListener('DOMContentLoaded', () => { IncidenciasUI.init(); });