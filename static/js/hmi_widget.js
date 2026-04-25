// 1. Variable global fuera del objeto para evitar errores de sintaxis
let myChart = null;

const HMIApp = {
    selectedSensor: null,

    init() {
        console.log("🚀 HMI Activo - Base 6 Estable");
        setInterval(() => this.getTelemetry(), 1500);
    },

    async getTelemetry() {
        try {
            const res = await fetch('/api/telemetria');
            
            // 🛡️ TRAMPA DE SEGURIDAD 1: Licencia Expirada
            if (res.status === 402) {
                console.warn("🚫 Licencia Expirada o Archivo Inválido. Redirigiendo a bloqueo...");
                window.location.href = '/licencia_expirada';
                return; // Cortamos la ejecución aquí
            }

            // 🛡️ TRAMPA DE SEGURIDAD 2: Sesión Caducada
            if (res.status === 401) {
                console.warn("⚠️ Sesión expirada. Redirigiendo a Login...");
                window.location.href = '/'; 
                return;
            }

            const data = await res.json();
            if (data && data.sensores) { // Nota: en app.py mandas "sensores", no "sensors"
                this.render(data.sensores);
                if (this.selectedSensor) this.updateDetail(data.sensores);
                if (data.status_plc) this.updatePLCStatus(data.status_plc);
            }
        } catch (e) {
            console.error("❌ Error de red con el motor SCADA:", e);
        }
    },

    showDetail(nombre) {
        this.selectedSensor = nombre;
        document.getElementById('det-nombre').innerText = nombre;
        document.getElementById('sensor-detail-widget').classList.remove('hidden');
        // Al abrir, cargamos el historial por defecto
        this.loadHistory();
    },

    updateDetail(sensors) {
        const s = sensors.find(sensor => sensor.n === this.selectedSensor);
        if (s) {
            document.getElementById('det-val').innerText = s.val.toFixed(2);
            document.getElementById('det-unit').innerText = s.u || '';
            const limite = s.l || 100;
            const porcentaje = Math.min((s.val / limite) * 100, 100);
            document.getElementById('det-bar').style.width = porcentaje + '%';
            document.getElementById('det-perc').innerText = Math.round(porcentaje) + '%';
        }
    },

    // --- MÓDULO DE CONFIGURACIÓN (Punto 2) ---
    abrirConfig(n, x, y) {
        document.getElementById('edit-n').value = n;
        document.getElementById('edit-x').value = x;
        document.getElementById('edit-y').value = y;
        document.getElementById('modal-sensor').classList.remove('hidden');
        console.log("Editando posición de:", n);
    },

    async guardarPosicion() {
        const data = {
            n: document.getElementById('edit-n').value,
            x: parseFloat(document.getElementById('edit-x').value),
            y: parseFloat(document.getElementById('edit-y').value)
        };

        try {
            const res = await fetch('/api/admin/update_position', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await res.json();
            if (result.status === 'ok') {
                alert("✅ Posición guardada con éxito");
                document.getElementById('modal-sensor').classList.add('hidden');
                location.reload(); 
            } else {
                alert("❌ Error: " + result.message);
            }
        } catch (e) {
            console.error("Error:", e);
        }
    },

    // --- MÓDULO DE HISTORIAL Y GRÁFICAS ---
    async loadHistory() {
        const sensor = this.selectedSensor;
        if (!sensor) return;

        // Capturamos los valores del calendario
        const inicio = document.getElementById('hist-inicio').value;
        const fin = document.getElementById('hist-fin').value;

        try {
            // Construimos la URL inyectando el nombre en la ruta y las fechas como parámetros
            let url = `/api/historial/${encodeURIComponent(sensor)}`;
            
            // Si el usuario seleccionó fechas, se las pegamos a la URL
            if (inicio && fin) {
                url += `?inicio=${inicio}&fin=${fin}`;
            }

            const res = await fetch(url);
            const data = await res.json();

            // Como app.py ahora devuelve {labels: [], values: []}, lo inyectamos directo
            if (data.labels && data.labels.length > 0) {
                this.renderChart(data.labels, data.values);
            } else {
                // Opcional: Limpiar la gráfica si no hay datos en ese rango
                this.renderChart([], []);
            }
        } catch (e) {
            console.error("❌ Error en historial:", e);
        }
    },

    renderChart(labels, values) {
        const ctx = document.getElementById('sparklineChart').getContext('2d');
        if (myChart) { myChart.destroy(); }

        myChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Tendencia',
                    data: values,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    fill: true,
                    tension: 0, // 🚀 OPTIMIZACIÓN 1: 0 = Líneas rectas (0 estrés de CPU)
                    pointRadius: 0,
                    hitRadius: 10, // Mantiene el área de detección del mouse grande
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false, // 🚀 OPTIMIZACIÓN 2: Sin animaciones de entrada
                normalized: true, // 🚀 OPTIMIZACIÓN 3: Salta validaciones internas de Chart.js
                spanGaps: true,   // Conecta la línea aunque falte un dato intermedio
                interaction: {    // 🚀 OPTIMIZACIÓN 4: Tooltip ultra-rápido en el eje X
                    mode: 'nearest',
                    intersect: false,
                    axis: 'x'
                },
                plugins: { legend: { display: false } },
                scales: {
                    x: { display: false },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: 'rgba(255,255,255,0.5)', font: { size: 8 } }
                    }
                }
            }
        });
    },

    render(sensors) {
    const layer = document.getElementById('nodes-layer');
    if (!layer) return;

    layer.innerHTML = sensors.map(s => {
        // --- LÓGICA DE ESTADO ISO ---
        // Definimos si está en falla analizando ambos umbrales
        const limiteAlto = s.lh || s.l || 100;
        const limiteBajo = s.ll || 0;
        
        const esFallaAlta = s.val >= limiteAlto;
        const esFallaBaja = s.val <= limiteBajo;
        const estaEnFalla = esFallaAlta || esFallaBaja;

        // Determinamos el color: Rojo para fallas, Azul para normal
        // (Podrías usar Naranja para falla baja si prefieres diferenciar)
        const colorClass = estaEnFalla ? 'bg-red-600 animate-pulse' : 'bg-blue-500';

        return `
            <div class="absolute group" style="left: ${s.x}%; top: ${s.y}%; transform: translate(-50%, -50%); z-index: 50;">
                <div onclick="HMIApp.showDetail('${s.n}')" 
                     oncontextmenu="event.preventDefault(); HMIApp.abrirConfig('${s.n}', ${s.x}, ${s.y})"
                     class="h-6 w-6 rounded-full border-2 border-white/40 cursor-pointer hover:scale-125 transition-all shadow-lg ${colorClass}">
                </div>
                <div class="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-black/80 text-[8px] text-white px-2 py-1 rounded pointer-events-none transition-opacity whitespace-nowrap font-bold">
                    ${s.n}: ${s.val.toFixed(2)} ${s.u || ''}
                </div>
            </div>
        `;
    }).join('');
    },

    updatePLCStatus(status) {
        const led = document.getElementById('led-circle');
        const ledText = document.getElementById('led-text');
        if (led && ledText) {
            led.className = `w-2 h-2 rounded-full ${status === 'ONLINE' ? 'bg-green-500' : 'bg-yellow-500'}`;
            ledText.innerText = status;
        }
    }
};

// Inicialización
HMIApp.init();