/**
 * MÓDULO VISUAL 4: HISTORIAL WIDGET (Gráfico en Tiempo Real)
 * Muestra el Data Stream con los umbrales de alerta dinámicos (Piso y Techo).
 */
const HistorialWidget = {
    chartInstance: null,
    timer: null,
    sensorActual: null,
    limiteAlto: null,
    limiteBajo: null,

    init() {
        console.log("📈 Módulo de Gráfico en Tiempo Real con Umbrales iniciado.");
        const btnCerrar = document.querySelector('#modal-historial button');
        if (btnCerrar) {
            btnCerrar.onclick = () => this.cerrar();
        }
    },

    async abrir(nombreSensor) {
        this.sensorActual = nombreSensor;
        
        // 1. Extraer los límites dinámicos desde la caché o directamente de la tabla HTML
        this.limiteAlto = 100; // Por defecto por si falla
        this.limiteBajo = 0;

        if (typeof ConfigWidget !== 'undefined' && ConfigWidget.sensoresCache) {
            const sensorData = ConfigWidget.sensoresCache.find(s => s.n === nombreSensor);
            if (sensorData) {
                this.limiteAlto = parseFloat(sensorData.lh);
                this.limiteBajo = parseFloat(sensorData.ll);
            }
        } else {
            // Respaldo: Leer directamente de las cajitas de texto de la tabla
            const tr = document.getElementById(`row-${nombreSensor}`);
            if (tr) {
                const inputs = tr.querySelectorAll('input[type="number"]');
                if (inputs.length >= 2) {
                    this.limiteBajo = parseFloat(inputs[0].value);
                    this.limiteAlto = parseFloat(inputs[1].value);
                }
            }
        }

        // 2. Actualizar el título para mostrar el contexto numérico
        document.getElementById('modal-titulo').innerHTML = `DATA_STREAM: <span class="text-blue-500">${nombreSensor}</span> <span class="text-[9px] text-gray-400 ml-4 tracking-widest">RANGO: [${this.limiteBajo} - ${this.limiteAlto}]</span>`;
        document.getElementById('modal-historial').classList.remove('hidden');
        
        // 3. Arrancar el motor del gráfico
        await this.cargarDatos();
        this.timer = setInterval(() => this.cargarDatos(), 1000);
    },

    cerrar() {
        document.getElementById('modal-historial').classList.add('hidden');
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        this.sensorActual = null;
    },

    async cargarDatos() {
        if (!this.sensorActual) return;
        try {
            const res = await fetch(`/api/historial/${encodeURIComponent(this.sensorActual)}`, { credentials: 'include' });
            if (!res.ok) return;
            const datos = await res.json();
            this.dibujar(datos);
        } catch (e) {
            console.error("Error al cargar historial:", e);
        }
    },

    dibujar(datos) {
        const ctx = document.getElementById('chart-historial').getContext('2d');
        
        // Compatibilidad con formato antiguo (Array) y nuevo ({labels: [], values: []})
        const labels = datos.labels || datos.map(d => d.fecha);
        const values = datos.values || datos.map(d => d.valor);
        
        // Creamos arreglos planos para las líneas rectas de los umbrales
        const dataAlto = values.map(() => this.limiteAlto);
        const dataBajo = values.map(() => this.limiteBajo);

        // Añadimos un pequeño margen (10%) arriba y abajo para que las líneas no se peguen a los bordes
        const paddingMax = this.limiteAlto + (Math.abs(this.limiteAlto) * 0.1 || 10);
        const paddingMin = this.limiteBajo - (Math.abs(this.limiteBajo) * 0.1 || 10);

        if (this.chartInstance) {
            // Actualización a 60fps
            this.chartInstance.data.labels = labels;
            this.chartInstance.data.datasets[0].data = values;
            this.chartInstance.data.datasets[1].data = dataAlto;
            this.chartInstance.data.datasets[2].data = dataBajo;
            
            // Actualizar límites del zoom
            if (this.chartInstance.options.scales.y) {
                this.chartInstance.options.scales.y.suggestedMax = paddingMax;
                this.chartInstance.options.scales.y.suggestedMin = paddingMin;
            }
            
            this.chartInstance.update('none'); 
        } else {
            // Creación del Gráfico Multicapa
            this.chartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Lectura en Vivo',
                            data: values,
                            borderColor: '#3b82f6', // Azul brillante
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            borderWidth: 3,
                            pointRadius: 0, // Quitamos puntos para que se vea como onda de osciloscopio
                            pointHoverRadius: 6,
                            fill: true,
                            tension: 0.3,
                            order: 1 // Asegura que la línea azul se dibuje por encima de las otras
                        },
                        {
                            label: 'Límite Crítico (Alto)',
                            data: dataAlto,
                            borderColor: '#ef4444', // Rojo
                            borderDash: [5, 5], // Línea Punteada
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: false,
                            tension: 0,
                            order: 2
                        },
                        {
                            label: 'Límite Crítico (Bajo)',
                            data: dataBajo,
                            borderColor: '#f59e0b', // Naranja
                            borderDash: [5, 5], // Línea Punteada
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: false,
                            tension: 0,
                            order: 3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: false, // Apagado para evitar parpadeos en realtime
                    plugins: { 
                        legend: { 
                            display: true,
                            labels: { color: '#a1a1aa', font: { family: 'Inter', size: 10, weight: 'bold' } }
                        } 
                    },
                    scales: {
                        x: { 
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }, 
                            ticks: { color: '#71717a' } 
                        },
                        y: { 
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }, 
                            ticks: { color: '#71717a' },
                            // Forzamos al gráfico a mostrar el rango de los umbrales
                            suggestedMax: paddingMax,
                            suggestedMin: paddingMin
                        }
                    }
                }
            });
        }
    }
};

document.addEventListener('DOMContentLoaded', () => HistorialWidget.init());