/**
 * MÓDULO VISUAL 1: HMI LOGIC
 * Se encarga de pintar y mover los círculos de telemetría sobre el plano de la planta.
 * Diseño actualizado a Glassmorphism (Cristal traslúcido)
 */
const HMI_Logic = {
    name: "HMI_Logic",
    containerId: "hmi-layout",
    activo: false,

    reactivar() {
        this.activo = true;
        if (typeof ScadaEngine !== 'undefined') {
            ScadaEngine.suscribir(this);
        }
    },

    update(datos_entrada) { // <-- 1. Cambiamos el nombre del parámetro recibido
        if (!this.activo) return;
        const container = document.getElementById(this.containerId);
        if (!container) return;

        // 🚑 2. EL PARCHE: Forzamos a que siempre sea un Array válido
        const sensores = Array.isArray(datos_entrada) ? datos_entrada : (datos_entrada.sensores || []);

        sensores.forEach(sensor => {
            let el = document.getElementById(`nodo-${sensor.n}`);
            
            if (!el) {
                el = document.createElement('div');
                el.id = `nodo-${sensor.n}`;
                el.className = 'absolute flex flex-col items-center justify-center transition-all duration-300 cursor-grab group';
                container.appendChild(el);
                this.hacerArrastrable(el, sensor.n);
                
                // --- NUEVO: DOBLE CLIC PARA ABRIR LA GRÁFICA ---
                el.addEventListener('dblclick', () => {
                    if (typeof HistorialWidget !== 'undefined') {
                        HistorialWidget.abrir(sensor.n);
                    }
                });
            }

            const valorActual = parseFloat(sensor.val).toFixed(1);
            const esAlerta = valorActual > parseFloat(sensor.lh) || valorActual < parseFloat(sensor.ll);
            
            // --- NUEVO ESTILO GLASS TRASLÚCIDO CON CIRCUNFERENCIA MARCADA ---
            // Si está bien: Cristal verde con borde verde remarcado
            // Si es alerta: Cristal rojo con borde rojo remarcado y animación
            const colorBg = esAlerta ? 'bg-red-500/30' : 'bg-green-500/20';
            const colorBorder = esAlerta ? 'border-red-500' : 'border-green-400';
            const shadow = esAlerta ? 'shadow-[0_0_20px_rgba(239,68,68,0.6)]' : 'shadow-[0_0_15px_rgba(74,222,128,0.3)]';
            const animacion = esAlerta ? 'sensor-alerta' : ''; 

            if (el.dataset.dragging !== "true") {
                el.style.left = `${sensor.x}%`;
                el.style.top = `${sensor.y}%`;
                el.style.transform = 'translate(-50%, -50%)';
            }

            // Inyectamos el diseño (Nota el border-[3px] y el backdrop-blur-md)
            el.innerHTML = `
                <div class="relative flex items-center justify-center w-12 h-12 rounded-full ${colorBg} ${colorBorder} border-[3px] ${shadow} ${animacion} backdrop-blur-md z-10 transition-colors duration-300">
                    <span class="text-white font-black text-[11px] tracking-tighter drop-shadow-[0_2px_2px_rgba(0,0,0,1)]">${valorActual}</span>
                </div>
                <div class="absolute top-full mt-2 bg-black/90 text-white text-[9px] font-black uppercase tracking-widest px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-20 pointer-events-none border border-white/10 backdrop-blur-md">
                    ${sensor.n} <br> <span class="text-gray-400 font-mono">${sensor.m || 'N/A'}</span>
                </div>
            `;
        });
    },

    hacerArrastrable(el, nombreSensor) {
        let isDragging = false;
        
        el.addEventListener('mousedown', (e) => {
            isDragging = true;
            el.dataset.dragging = "true";
            el.classList.replace('cursor-grab', 'cursor-grabbing');
        });

        window.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const container = document.getElementById(this.containerId);
            const rect = container.getBoundingClientRect();
            
            let x = ((e.clientX - rect.left) / rect.width) * 100;
            let y = ((e.clientY - rect.top) / rect.height) * 100;
            
            x = Math.max(0, Math.min(100, x));
            y = Math.max(0, Math.min(100, y));
            
            el.style.left = `${x}%`;
            el.style.top = `${y}%`;
        });

        window.addEventListener('mouseup', async () => {
            if (isDragging) {
                isDragging = false;
                el.dataset.dragging = "false";
                el.classList.replace('cursor-grabbing', 'cursor-grab');
                
                const posX = parseFloat(el.style.left);
                const posY = parseFloat(el.style.top);
                
                try {
                    await fetch('/api/admin/update_position', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ n: nombreSensor, x: posX, y: posY })
                    });
                } catch (error) {
                    console.error("Error al guardar la posición:", error);
                }
            }
        });
    },

    async subirPlano(input) {
        if (!input.files || input.files.length === 0) return;
        const formData = new FormData();
        formData.append('file', input.files[0]);

        try {
            const res = await fetch('/api/admin/upload_plano', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.status === 'success') {
                document.getElementById(this.containerId).style.backgroundImage = `url('${data.path}?t=${new Date().getTime()}')`;
            } else {
                alert("Error: " + data.error);
            }
        } catch (e) {
            alert("Error de red al subir el layout.");
        }
    }
};