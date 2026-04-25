/**
 * MÓDULO DE ANALÍTICA: ReportsWidget
 * Gestiona la selección múltiple, petición de datos históricos, gráficos (Chart.js) y exportación.
 */
const ReportsWidget = {
    chartInstance: null, // Guardamos el gráfico para poder destruirlo y redibujarlo

    async init() {
        console.log("📊 Módulo de Reportes y Analítica Iniciado.");
        
        // 1. Configurar fechas por defecto (Últimas 24 horas)
        const ahora = new Date();
        const ayer = new Date(ahora.getTime() - (24 * 60 * 60 * 1000));
        
        // Formatear para el input type="datetime-local" (YYYY-MM-DDThh:mm)
        const formatFecha = (d) => {
            const tzOffset = d.getTimezoneOffset() * 60000; // offset en milisegundos
            return (new Date(d - tzOffset)).toISOString().slice(0, 16);
        };

        document.getElementById('rep-inicio').value = formatFecha(ayer);
        document.getElementById('rep-fin').value = formatFecha(ahora);

        // 2. Cargar la lista de sensores en el selector múltiple
        await this.cargarListaSensores();
    },

    async cargarListaSensores() {
        try {
            const res = await fetch('/api/admin/config_sensores');
            const data = await res.json();
            const select = document.getElementById('lista-sensores-multiselect');
            
            if (!select || !data.sensores) return;

            // Llenamos el <select multiple>
            select.innerHTML = data.sensores.map(s => 
                `<option value="${s.nombre_sensor}">${s.nombre_sensor} (${s.protocolo || 'NODO'})</option>`
            ).join('');
        } catch (e) {
            console.error("Error cargando sensores para reportes:", e);
            alert("⚠️ No se pudo cargar el inventario de sensores.");
        }
    },

    // --- FUNCIÓN PRINCIPAL: DIBUJAR EL GRÁFICO ---
    async generarReporte() {
        // 1. Obtener opciones seleccionadas
        const select = document.getElementById('lista-sensores-multiselect');
        const seleccionados = Array.from(select.selectedOptions).map(opt => opt.value);
        
        const inicio = document.getElementById('rep-inicio').value;
        const fin = document.getElementById('rep-fin').value;
        const btn = document.getElementById('rep-btn-generar');

        if (seleccionados.length === 0) {
            return alert("⚠️ Por favor, selecciona al menos un activo (sensor) de la lista.");
        }
        if (!inicio || !fin) {
            return alert("⚠️ Revisa las fechas de inicio y fin.");
        }

        // 2. UI de Carga
        const textoOriginal = btn.innerText;
        btn.innerText = "⏳ PROCESANDO MILLONES DE DATOS...";
        btn.classList.add('opacity-50', 'cursor-not-allowed');
        btn.disabled = true;

        try {
            // 3. Petición a la Base de Datos (PostgreSQL)
            const res = await fetch('/api/reportes/data_masiva', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sensores: seleccionados, inicio: inicio, fin: fin })
            });
            
            const data = await res.json();

            if (!data.success) {
                throw new Error(data.error || "Falla en base de datos");
            }

            if (!data.labels || data.labels.length === 0) {
                alert("📭 No hay registros en ese rango de tiempo para los sensores seleccionados.");
                this.limpiarGrafico();
            } else {
                // 4. Dibujar el Gráfico y los KPIs
                this.dibujarGrafico(data.labels, data.datasets);
                this.generarInsights(data.datasets);
                
                // 5. NUEVO: Llamamos a las tarjetas SPC (Estadísticas)
                this.cargarTarjetasSPC();
            }

        } catch (e) {
            console.error("Error al generar reporte:", e);
            alert("❌ Error al procesar el reporte: " + e.message);
        } finally {
            // Restaurar botón
            btn.innerText = textoOriginal;
            btn.classList.remove('opacity-50', 'cursor-not-allowed');
            btn.disabled = false;
        }
    },

    dibujarGrafico(etiquetas, datasets_db) {
        const ctx = document.getElementById('chart-reporte-canvas').getContext('2d');
        
        // Destruir el gráfico anterior si existe para evitar superposiciones
        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        // Ocultar placeholder y mostrar canvas
        const canvas = document.getElementById('chart-reporte-canvas');
        const placeholder = document.getElementById('chart-placeholder');
        if (canvas) canvas.classList.remove('hidden');
        if (placeholder) placeholder.classList.add('hidden');

        // Paleta de colores estilo "Cyberpunk/Industrial" para líneas múltiples
        const paleta = [
            { border: '#3b82f6', bg: 'rgba(59, 130, 246, 0.1)' }, // Azul
            { border: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)' },  // Rojo
            { border: '#10b981', bg: 'rgba(16, 185, 129, 0.1)' }, // Verde
            { border: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)' }, // Naranja
            { border: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.1)' }  // Morado
        ];

        // Mapeamos los datos de la DB al formato de Chart.js
        const datasets_chart = datasets_db.map((ds, index) => {
            const color = paleta[index % paleta.length];
            return {
                label: ds.sensor,
                data: ds.values,
                borderColor: color.border,
                backgroundColor: color.bg,
                borderWidth: 2,
                pointRadius: 0,           // Ocultar puntos para que fluya más rápido
                pointHoverRadius: 6,      // Mostrar punto solo al pasar el mouse
                fill: true,
                tension: 0.3              // Suavizado de la línea
            };
        });

        // Crear la nueva instancia de Chart.js
        this.chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: etiquetas,
                datasets: datasets_chart
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        labels: { color: '#a1a1aa', font: { family: 'Inter', size: 10, weight: 'bold' } }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#a1a1aa',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#71717a', maxTicksLimit: 10 } // Limitar etiquetas para no saturar
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#71717a' }
                    }
                }
            }
        });
    },

    limpiarGrafico() {
        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
        document.getElementById('contenedor-analiticas-reporte').innerHTML = '';
        document.getElementById('contenedor-insights').innerHTML = '';
    },

    // --- ANALÍTICA EXTRA (MÁXIMOS, MÍNIMOS, PROMEDIOS) ---
    generarInsights(datasets_db) {
        const contenedor = document.getElementById('contenedor-analiticas-reporte');
        if (!contenedor) return;

        // Limpiamos el mensaje de "Esperando correlación..."
        contenedor.innerHTML = ''; 

        let html = '<div class="grid grid-cols-1 md:grid-cols-3 gap-4 col-span-full mb-6">';
        
        datasets_db.forEach(ds => {
            if (ds.values.length === 0) return;
            
            // Cálculos matemáticos
            const max = Math.max(...ds.values).toFixed(2);
            const min = Math.min(...ds.values).toFixed(2);
            const avg = (ds.values.reduce((a, b) => a + b, 0) / ds.values.length).toFixed(2);

            html += `
            <div class="bg-white/5 border border-white/10 p-4 rounded-2xl">
                <h4 class="text-[10px] font-black text-blue-400 uppercase tracking-widest mb-3">${ds.sensor}</h4>
                <div class="flex justify-between items-center text-xs">
                    <div class="flex flex-col"><span class="text-gray-500 uppercase text-[8px] font-bold">Máximo</span> <span class="text-red-400 font-mono">${max}</span></div>
                    <div class="flex flex-col"><span class="text-gray-500 uppercase text-[8px] font-bold">Promedio</span> <span class="text-blue-400 font-mono">${avg}</span></div>
                    <div class="flex flex-col text-right"><span class="text-gray-500 uppercase text-[8px] font-bold">Mínimo</span> <span class="text-green-400 font-mono">${min}</span></div>
                </div>
            </div>`;
        });
        
        html += '</div>';
        contenedor.innerHTML = html;
    },

    // --- EXPORTACIÓN A EXCEL MASIVA ---
    exportarExcelMasivo() {
        const select = document.getElementById('lista-sensores-multiselect');
        const seleccionados = Array.from(select.selectedOptions).map(opt => opt.value);
        const inicio = document.getElementById('rep-inicio').value;
        const fin = document.getElementById('rep-fin').value;

        if (seleccionados.length === 0) {
            return alert("⚠️ Selecciona los sensores que deseas exportar a Excel.");
        }

        // Construir la URL con parámetros GET
        let url = `/api/reportes/excel_masivo?inicio=${inicio}&fin=${fin}`;
        seleccionados.forEach(s => {
            url += `&sensores=${encodeURIComponent(s)}`;
        });

        // Redirigir al navegador para iniciar la descarga del archivo generado por Python
        window.location.href = url;
    },

    // --- NUEVA FUNCIÓN: TARJETAS DE CONTROL ESTADÍSTICO (SPC) ---
    async cargarTarjetasSPC() {
        try {
            const res = await fetch('/api/reportes/spc_cards');
            const json = await res.json();
            
            if (json.status !== 'success') {
                console.error("Error del servidor:", json.message);
                return;
            }

            const contenedor = document.getElementById('contenedor-insights');
            if (!contenedor) return;
            
            // Si no hay datos (la BD está vacía o ningún sensor está activo)
            if (json.data.length === 0) {
                contenedor.innerHTML = `
                    <div class="col-span-full text-center p-8 opacity-30 border-2 border-dashed border-white/10 rounded-2xl">
                        <p class="text-[10px] font-black uppercase tracking-[0.3em] text-gray-400">No hay datos históricos suficientes para el análisis SPC.</p>
                    </div>
                `;
                return;
            }

            // Preparamos el HTML para las tarjetas SPC
            let htmlCards = '<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">';

            json.data.forEach(sensor => {
                htmlCards += `
                    <div class="glass-panel rounded-3xl p-6 flex flex-col gap-4 border-t-4 border-t-white/10 hover:border-t-blue-500 transition-all shadow-xl">
                        
                        <div class="flex justify-between items-center border-b border-white/10 pb-2">
                            <h3 class="text-lg font-black text-white tracking-tighter uppercase truncate w-32" title="${sensor.nombre}">${sensor.nombre}</h3>
                            <span class="text-[9px] font-black tracking-widest uppercase px-2 py-1 rounded-md bg-white/5 ${sensor.color_nota}">
                                ${sensor.nota}
                            </span>
                        </div>

                        <div class="grid grid-cols-2 gap-4">
                            <div class="flex flex-col">
                                <span class="text-[8px] text-gray-500 uppercase font-black tracking-widest mb-1">Media (M)</span>
                                <span class="text-xl font-mono text-blue-400 font-bold leading-none">${sensor.media}</span>
                            </div>
                            <div class="flex flex-col text-right">
                                <span class="text-[8px] text-gray-500 uppercase font-black tracking-widest mb-1">Desviación (E)</span>
                                <span class="text-xl font-mono text-blue-400 font-bold leading-none">${sensor.desviacion}</span>
                            </div>
                        </div>

                        <div class="flex flex-col bg-black/40 p-3 rounded-xl border border-white/5">
                            <div class="flex justify-between items-center mb-1">
                                <span class="text-[9px] text-white uppercase font-bold tracking-widest">Estabilidad del Proceso</span>
                                <span class="text-[10px] font-black ${sensor.color_nota}">${sensor.estabilidad}%</span>
                            </div>
                            <div class="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                                <div class="h-full ${sensor.color_barra} transition-all duration-1000" style="width: ${sensor.estabilidad}%"></div>
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-4 bg-white/5 p-3 rounded-xl border border-white/5">
                            <div class="flex flex-col">
                                <span class="text-[8px] text-gray-500 uppercase font-black tracking-widest mb-1">Límite Inf.</span>
                                <span class="text-sm font-bold text-gray-300 leading-none">${sensor.limite_bajo}</span>
                            </div>
                            <div class="flex flex-col text-right">
                                <span class="text-[8px] text-gray-500 uppercase font-black tracking-widest mb-1">Límite Sup.</span>
                                <span class="text-sm font-bold text-gray-300 leading-none">${sensor.limite_alto}</span>
                            </div>
                        </div>

                        <div class="grid grid-cols-2 gap-4 pt-2 border-t border-white/10">
                            <div class="flex flex-col">
                                <span class="text-[8px] text-gray-500 uppercase font-black tracking-widest mb-1">Muestreo (N)</span>
                                <span class="text-sm font-mono text-gray-400 leading-none">${sensor.muestreo_total.toLocaleString()}</span>
                            </div>
                            <div class="flex flex-col text-right">
                                <span class="text-[8px] text-gray-500 uppercase font-black tracking-widest mb-1">Rango (A)</span>
                                <span class="text-sm font-mono text-gray-400 leading-none">${sensor.rango}</span>
                            </div>
                        </div>

                    </div>
                `;
            });

            htmlCards += '</div>';
            contenedor.innerHTML = htmlCards;

        } catch (e) {
            console.error("Error cargando tarjetas SPC:", e);
        }
    }
};