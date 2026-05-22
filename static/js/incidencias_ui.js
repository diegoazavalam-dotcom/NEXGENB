/**
 * MÓDULO VISUAL 3: LOG DE INCIDENCIAS (IncidenciasUI)
 * Panel derecho con Búsqueda en Vivo, Autocompletado, Paginación y Cierres.
 */
const AudioAlarm = {
    ctx: null, interval: null,
    init() { if(!this.ctx) this.ctx = new (window.AudioContext || window.webkitAudioContext)(); },
    start() {
        if(this.interval) return;
        this.init();
        if(this.ctx.state === 'suspended') this.ctx.resume();
        this.interval = setInterval(() => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'square';
            osc.frequency.setValueAtTime(800, this.ctx.currentTime); // Tono agudo de alarma
            osc.frequency.exponentialRampToValueAtTime(600, this.ctx.currentTime + 0.1);
            gain.gain.setValueAtTime(0.1, this.ctx.currentTime); // Volumen bajo para no asustar
            gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.2);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start();
            osc.stop(this.ctx.currentTime + 0.2);
        }, 1000);
    },
    stop() {
        if(this.interval) clearInterval(this.interval);
        this.interval = null;
    }
};

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

        // HOOK MODEL: Recompensa Variable (Salud del Sistema)
        const healthBadge = document.getElementById('system-health');
        if (healthBadge) {
            let healthScore = 100 - (alertasVivas.length * 5);
            if (healthScore < 0) healthScore = 0;
            healthBadge.innerText = healthScore + "%";
            
            if (healthScore === 100) {
                healthBadge.className = "text-2xl font-black text-green-500 drop-shadow-[0_0_8px_rgba(34,197,94,0.8)] transition-all duration-500";
            } else if (healthScore > 50) {
                healthBadge.className = "text-2xl font-black text-yellow-500 animate-pulse transition-all duration-500";
            } else {
                healthBadge.className = "text-2xl font-black text-red-500 animate-pulse transition-all duration-500";
            }
        }

        if (alertasVivas.length !== this.lastAlertCount) {
            // HOOK MODEL: Recompensa Variable (Refuerzo Positivo al limpiar la planta)
            if (this.lastAlertCount > 0 && alertasVivas.length === 0) {
                if (typeof UIUtils !== 'undefined') {
                    UIUtils.showToast("¡Excelente trabajo! Sistema 100% Optimizado y Estable.", "success");
                }
            }
            this.lastAlertCount = alertasVivas.length;
            this.sincronizarConBD();
        }
    },

    async sincronizarConBD() {
        if (this.isFetching) return;
        this.isFetching = true;

        try {
            const res = await fetch('/api/alarmas/isa182', { credentials: 'include' });
            if (res.ok) {
                this.cacheIncidencias = await res.json();
                this.actualizarAutocompletado();
                this.render(); // Dibujamos la vista con filtros
                
                // Evaluar si debemos sonar la alarma auditiva
                const hayCriticasUnack = this.cacheIncidencias.some(inc => inc.estado_ack === 'UNACK' && inc.prioridad === 'CRITICA');
                if (hayCriticasUnack) AudioAlarm.start();
                else AudioAlarm.stop();
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
            html += `<div class="space-y-3">`;
            html += itemsPagina.map(inc => {
                const esAlto = inc.tipo === 'ALTO';
                const hora = inc.fecha && inc.fecha.includes(' ') ? inc.fecha.split(' ')[1] : '--:--:--';
                const esUnack = inc.estado_ack === 'UNACK';
                const parpadeo = esUnack ? 'animate-pulse' : '';
                const opacidad = esUnack ? '' : 'opacity-70';
                
                // Colores por prioridad
                let colorPrioridad = 'text-blue-500 border-blue-500 bg-blue-500/10';
                if (inc.prioridad === 'CRITICA') colorPrioridad = 'text-red-600 border-red-600 bg-red-600/10 font-black';
                else if (inc.prioridad === 'ALTA') colorPrioridad = 'text-orange-500 border-orange-500 bg-orange-500/10';
                else if (inc.prioridad === 'MEDIA') colorPrioridad = 'text-yellow-500 border-yellow-500 bg-yellow-500/10';

                return `
                <div class="glass-panel p-4 rounded-2xl border-l-4 ${colorPrioridad} ${parpadeo} ${opacidad} transition-all">
                    <div class="flex justify-between items-start mb-2">
                        <div class="flex flex-col">
                            <span class="text-[12px] font-black text-white uppercase tracking-tighter">${inc.sensor_id}</span>
                            <span class="text-[8px] font-bold ${colorPrioridad.split(' ')[0]} uppercase tracking-widest">${inc.prioridad} - ${inc.tipo}</span>
                        </div>
                        <div class="flex flex-col items-end">
                            <span class="text-[9px] font-mono text-gray-500 bg-black/40 px-2 py-1 rounded-md">${hora}</span>
                            ${!esUnack ? `<span class="text-[7px] text-green-400 mt-1">ACK por ${inc.usuario_ack}</span>` : ''}
                        </div>
                    </div>
                    
                    <div class="bg-black/20 p-2 rounded-xl mb-3 border border-white/5">
                        <p class="text-[11px] text-gray-400">Falla: <span class="text-white font-black">${inc.valor_detectado}</span></p>
                        <p class="text-[8px] text-gray-500 uppercase">Límite: ${inc.umbral_limite}</p>
                    </div>

                    <div class="flex gap-2">
                        ${esUnack ? `
                        <button onclick="IncidenciasUI.reconocer('${inc.id}')" 
                            class="flex-[2] py-2 bg-green-500 hover:bg-green-400 text-black border border-green-400 rounded-xl text-[9px] font-black uppercase transition-all shadow-lg shadow-green-500/20">
                            ACK (Reconocer)
                        </button>` : `
                        <button onclick="IncidenciasUI.atender('${inc.id}')" 
                            class="flex-1 py-2 bg-blue-500/10 hover:bg-blue-500 text-blue-400 hover:text-white border border-blue-500/30 rounded-xl text-[8px] font-black uppercase transition-all">
                            Cerrar
                        </button>`}
                        
                        <button onclick="IncidenciasUI.aparcar('${inc.id}')" 
                            class="flex-1 py-2 bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white border border-white/10 rounded-xl text-[8px] font-black uppercase transition-all">
                            Shelve
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
    async reconocer(id_alarma) {
        // Optimistic UI Update: Reflejar instantáneamente en la interfaz para máxima velocidad (UX)
        const alarmaLocal = this.cacheIncidencias.find(i => i.id === id_alarma);
        if (alarmaLocal) {
            alarmaLocal.estado_ack = 'ACK';
            alarmaLocal.usuario_ack = 'admin (local)';
            this.render(); // Redibujar al instante para detener el parpadeo
            AudioAlarm.stop(); // Detener sirena inmediatamente
        }

        try {
            const res = await fetch('/api/alarmas/ack', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id_alarma })
            });
            if ((await res.json()).success) {
                if (typeof UIUtils !== 'undefined') UIUtils.showToast("Alarma Reconocida (ACK)", 'success');
                // Al terminar, sincronizamos silenciosamente con la fuente de la verdad
                this.sincronizarConBD();
            }
        } catch (e) { 
            if (typeof UIUtils !== 'undefined') UIUtils.showToast("Error de red en ACK", 'error'); 
            this.sincronizarConBD(); // Revertir en caso de fallo
        }
    },

    async aparcar(id_alarma) {
        const horasStr = prompt("⏲️ SHELVING (ISA-18.2)\n¿Por cuántas horas deseas silenciar esta alarma?");
        if (!horasStr) return;
        const horas = parseFloat(horasStr);
        if (isNaN(horas) || horas <= 0) return alert("Cantidad inválida");

        try {
            const res = await fetch('/api/alarmas/shelve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id_alarma, horas: horas })
            });
            if ((await res.json()).success) {
                if (typeof UIUtils !== 'undefined') UIUtils.showToast(`Alarma aparcada por ${horas}h`, 'success');
                this.sincronizarConBD();
            }
        } catch (e) { if (typeof UIUtils !== 'undefined') UIUtils.showToast("Error de red", 'error'); }
    },

    async atender(id_incidencia) {
        const comentario = prompt("🚨 CIERRE DE ALARMA\nResolución / Acción tomada:");
        if (!comentario || comentario.trim().length < 3) return;
        try {
            const res = await fetch('/api/incidencias/atender', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: id_incidencia, comentario: comentario.trim() })
            });
            if ((await res.json()).success) {
                if (typeof UIUtils !== 'undefined') UIUtils.showToast("Alarma cerrada", 'success');
                this.sincronizarConBD();
            }
        } catch (e) { if (typeof UIUtils !== 'undefined') UIUtils.showToast("Fallo de red", 'error'); }
    }
};

document.addEventListener('DOMContentLoaded', () => { IncidenciasUI.init(); });