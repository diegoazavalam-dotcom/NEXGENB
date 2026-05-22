/**
 * MÓDULO VISUAL 2: TABLA DE INVENTARIO Y CONFIGURACIÓN (ConfigWidget)
 * Ahora soporta Creación, Edición y Eliminación completa.
 */
const ConfigWidget = {
    name: "ConfigWidget",
    sensoresCache: [], // Guardamos una copia local para poder leerla al editar
    modoEdicion: false,
    nombreOriginalEditar: "",

    async init() {
        if (typeof ScadaEngine !== 'undefined') ScadaEngine.suscribir(this);

        // Lógica del Modal (Cambiar entre Siemens S7 y OPC UA)
        const selectProto = document.getElementById('sensor-protocolo');
        if (selectProto) {
            selectProto.addEventListener('change', (e) => {
                const s7 = document.getElementById('group-s7-params');
                const opc = document.getElementById('group-opc-params');
                if (e.target.value === 'S7') {
                    s7.classList.remove('hidden');
                    opc.classList.add('hidden');
                } else {
                    s7.classList.add('hidden');
                    opc.classList.remove('hidden');
                }
            });
        }
    },

    // --- MODAL: CREAR NUEVO ---
    abrirModal() {
        this.modoEdicion = false;
        this.nombreOriginalEditar = "";
        
        // Limpiamos los campos
        document.getElementById('sensor-protocolo').value = 'S7';
        document.getElementById('sensor-protocolo').dispatchEvent(new Event('change')); // Forzamos el cambio visual
        document.getElementById('sensor-nombre').value = '';
        document.getElementById('sensor-id-conn').value = '';
        document.getElementById('sensor-metrica').value = 'REAL';
        document.getElementById('sensor-unidad').value = '';
        document.getElementById('add-ll').value = '10';
        document.getElementById('add-lh').value = '90';
        document.getElementById('add-db').value = '1';
        document.getElementById('add-off').value = '0';
        document.getElementById('sensor-nodo-id').value = '';

        // Cambiamos textos
        document.querySelector('#modal-agregar-sensor h2').innerText = "Vincular Nodo PLC";
        document.querySelector('#modal-agregar-sensor button:last-child').innerText = "Guardar Nodo";
        
        document.getElementById('modal-agregar-sensor').classList.remove('hidden');
    },

    // --- MODAL: EDITAR EXISTENTE ---
    abrirEdicion(nombreSensor) {
        // Buscamos el sensor en nuestra caché local
        const sensor = this.sensoresCache.find(s => s.n === nombreSensor);
        if (!sensor) return alert("Error: No se encontró la data del sensor.");

        this.modoEdicion = true;
        this.nombreOriginalEditar = sensor.n;

        // Llenamos los inputs con los datos del sensor
        document.getElementById('sensor-protocolo').value = sensor.protocolo || 'S7';
        document.getElementById('sensor-protocolo').dispatchEvent(new Event('change'));
        
        document.getElementById('sensor-nombre').value = sensor.n;
        document.getElementById('sensor-id-conn').value = sensor.id;
        document.getElementById('sensor-metrica').value = sensor.m || 'REAL';
        document.getElementById('sensor-unidad').value = sensor.u || '';
        document.getElementById('add-ll').value = sensor.ll;
        document.getElementById('add-lh').value = sensor.lh;
        
        // Dependiendo del protocolo llenamos los datos específicos (usamos "0" o vacíos si no existen en el objeto aún)
        // Nota: El backend devuelve la configuración. Para tener DB y Offset exactos, lo ideal es que telemetría los envíe,
        // pero podemos dejarlos predeterminados al editar si el motor SCADA no los mandaba en la vista rápida.
        document.getElementById('add-db').value = sensor.db || '1'; 
        document.getElementById('add-off').value = sensor.off || '0';
        document.getElementById('sensor-nodo-id').value = sensor.nodo_id || '';

        // Cambiamos textos
        document.querySelector('#modal-agregar-sensor h2').innerText = "Editar Nodo PLC";
        document.querySelector('#modal-agregar-sensor button:last-child').innerText = "Actualizar Cambios";
        
        document.getElementById('modal-agregar-sensor').classList.remove('hidden');
    },

    // --- RECEPCIÓN DE DATOS EN VIVO ---
    update(sensores) {
        this.sensoresCache = sensores; 
        const tbody = document.getElementById('tabla-sensores-body');
        if (!tbody) return;

        if (!this.sensorHistory) this.sensorHistory = {};
        if (!this.lastUpdateTime) this.lastUpdateTime = {};
        const now = Date.now();

        const currentIds = sensores.map(s => `row-${s.n}`);
        Array.from(tbody.children).forEach(tr => {
            if (!currentIds.includes(tr.id)) tr.remove();
        });

        sensores.forEach(sensor => {
            let tr = document.getElementById(`row-${sensor.n}`);
            const isDisconnected = document.getElementById('plc-status-text')?.innerText.includes('DESCONECTADO');
            const valorNum = parseFloat(sensor.val);
            const valorActual = isNaN(valorNum) ? 0 : valorNum;
            let esAlerta = false;
            let colorTexto = 'text-green-400';
            let displayValue = valorActual.toFixed(1);

            if (isDisconnected) {
                displayValue = '--';
                colorTexto = 'text-gray-500 font-black';
            } else {
                esAlerta = valorActual > parseFloat(sensor.lh) || valorActual < parseFloat(sensor.ll);
                colorTexto = esAlerta ? 'text-red-500 font-black animate-pulse' : 'text-gray-300';
            }

            // --- 1. DATA QUALITY & SPARKLINE LOGIC ---
            if (!this.sensorHistory[sensor.n]) this.sensorHistory[sensor.n] = Array(20).fill(valorActual);
            const hist = this.sensorHistory[sensor.n];
            
            // Si cambió el valor, actualizamos el timestamp
            if (hist[hist.length - 1] !== valorActual) {
                this.lastUpdateTime[sensor.n] = now;
            }
            hist.push(valorActual);
            if (hist.length > 20) hist.shift();

            // Calidad del Dato
            const timeSinceChange = now - (this.lastUpdateTime[sensor.n] || now);
            let qualityClass = "bg-gray-500 shadow-none"; // Fresco (Normal)
            if (timeSinceChange > 60000) qualityClass = "bg-yellow-500 shadow-[0_0_5px_#eab308]"; // Stale (+60s congelado)
            if (isNaN(valorNum)) qualityClass = "bg-red-500 shadow-[0_0_5px_#ef4444]"; // Bad
            if (isDisconnected) qualityClass = "bg-gray-500 shadow-none";

            // Sparkline SVG
            const sMax = Math.max(...hist) * 1.1 || 1;
            const sMin = Math.min(...hist) * 0.9 || 0;
            const sRange = (sMax - sMin) || 1;
            const pts = hist.map((v, i) => `${i * 2.5},${20 - ((v - sMin) / sRange * 20)}`).join(' ');
            const sparkline = isDisconnected ? '' : `<svg width="50" height="20" class="inline-block ml-3 opacity-60"><polyline points="${pts}" fill="none" stroke="${esAlerta ? '#ef4444' : '#3b82f6'}" stroke-width="1.5"/></svg>`;


            if (!tr) {
                tr = document.createElement('tr');
                tr.id = `row-${sensor.n}`;
                tr.className = "text-[10px] uppercase tracking-widest text-gray-400 border-b border-white/5 hover:bg-white/5 transition-colors";
                
                tr.innerHTML = `
                    <td class="p-4 flex items-center gap-3">
                        <div class="relative flex items-center justify-center" title="Data Quality">
                            <span class="w-2.5 h-2.5 rounded-full ${qualityClass}"></span>
                            ${esAlerta ? `<span class="absolute w-4 h-4 rounded-full bg-red-500/50 animate-ping"></span>` : ''}
                        </div>
                        <span class="font-black text-white">${sensor.n}</span>
                    </td>
                    <td class="p-4 font-mono text-[9px]">${sensor.protocolo || 'S7'} | ${sensor.id}</td>
                    <td class="p-4 flex items-center">
                        <span class="valor-vivo text-lg ${colorTexto} min-w-[3rem]">${displayValue}</span>
                        <span class="text-[8px] text-gray-500 mr-2">${sensor.u || ''}</span>
                        ${sparkline}
                    </td>
                    <td class="p-4">
                        <input type="number" value="${sensor.ll}" onchange="ConfigWidget.updateLimit('${sensor.n}', this.value, 'bajo')" 
                            class="w-16 bg-black/40 border border-blue-500/30 text-blue-400 p-1.5 rounded-lg text-center outline-none focus:border-blue-500 font-bold">
                    </td>
                    <td class="p-4">
                        <input type="number" value="${sensor.lh}" onchange="ConfigWidget.updateLimit('${sensor.n}', this.value, 'alto')" 
                            class="w-16 bg-black/40 border border-red-500/30 text-red-500 p-1.5 rounded-lg text-center outline-none focus:border-red-500 font-bold">
                    </td>
                    <td class="p-4 text-right whitespace-nowrap">
                        <button onclick="TelecontrolWidget.abrir('${sensor.n}', '${sensor.m}')" class="text-purple-500 hover:text-white bg-purple-500/10 hover:bg-purple-600 px-3 py-1.5 rounded-lg transition-all font-bold tracking-widest text-[8px] mr-1">WRITE</button>
                        <button onclick="HistorialWidget.abrir('${sensor.n}')" class="text-green-500 hover:text-white bg-green-500/10 hover:bg-green-600 px-3 py-1.5 rounded-lg transition-all font-bold tracking-widest text-[8px] mr-1">CHART</button>
                        <button onclick="ConfigWidget.abrirEdicion('${sensor.n}')" class="text-blue-500 hover:text-white bg-blue-500/10 hover:bg-blue-600 px-3 py-1.5 rounded-lg transition-all font-bold tracking-widest text-[8px] mr-1">EDITAR</button>
                        <button onclick="ConfigWidget.eliminar('${sensor.n}')" class="text-red-500 hover:text-white bg-red-500/10 hover:bg-red-600 px-3 py-1.5 rounded-lg transition-all font-bold tracking-widest text-[8px]">BORRAR</button>
                    </td>
                `;
                tbody.appendChild(tr);
            } else {
                // Actualización rápida reconstruyendo las celdas principales
                tr.innerHTML = `
                    <td class="p-4 flex items-center gap-3">
                        <div class="relative flex items-center justify-center" title="Data Quality">
                            <span class="w-2.5 h-2.5 rounded-full ${qualityClass}"></span>
                            ${esAlerta ? `<span class="absolute w-4 h-4 rounded-full bg-red-500/50 animate-ping"></span>` : ''}
                        </div>
                        <span class="font-black text-white">${sensor.n}</span>
                    </td>
                    <td class="p-4 font-mono text-[9px]">${sensor.protocolo || 'S7'} | ${sensor.id}</td>
                    <td class="p-4 flex items-center">
                        <span class="valor-vivo text-lg ${colorTexto} min-w-[3rem]">${displayValue}</span>
                        <span class="text-[8px] text-gray-500 mr-2">${sensor.u || ''}</span>
                        ${sparkline}
                    </td>
                    <td class="p-4">
                        <input type="number" value="${sensor.ll}" onchange="ConfigWidget.updateLimit('${sensor.n}', this.value, 'bajo')" 
                            class="w-16 bg-black/40 border border-blue-500/30 text-blue-400 p-1.5 rounded-lg text-center outline-none focus:border-blue-500 font-bold">
                    </td>
                    <td class="p-4">
                        <input type="number" value="${sensor.lh}" onchange="ConfigWidget.updateLimit('${sensor.n}', this.value, 'alto')" 
                            class="w-16 bg-black/40 border border-red-500/30 text-red-500 p-1.5 rounded-lg text-center outline-none focus:border-red-500 font-bold">
                    </td>
                    <td class="p-4 text-right whitespace-nowrap">
                        <button onclick="TelecontrolWidget.abrir('${sensor.n}', '${sensor.m}')" class="text-purple-500 hover:text-white bg-purple-500/10 hover:bg-purple-600 px-3 py-1.5 rounded-lg transition-all font-bold tracking-widest text-[8px] mr-1">WRITE</button>
                        <button onclick="HistorialWidget.abrir('${sensor.n}')" class="text-green-500 hover:text-white bg-green-500/10 hover:bg-green-600 px-3 py-1.5 rounded-lg transition-all font-bold tracking-widest text-[8px] mr-1">CHART</button>
                        <button onclick="ConfigWidget.abrirEdicion('${sensor.n}')" class="text-blue-500 hover:text-white bg-blue-500/10 hover:bg-blue-600 px-3 py-1.5 rounded-lg transition-all font-bold tracking-widest text-[8px] mr-1">EDITAR</button>
                        <button onclick="ConfigWidget.eliminar('${sensor.n}')" class="text-red-500 hover:text-white bg-red-500/10 hover:bg-red-600 px-3 py-1.5 rounded-lg transition-all font-bold tracking-widest text-[8px]">BORRAR</button>
                    </td>
                `;
            }
        });
    },

    // --- ACCIONES A LA BASE DE DATOS ---
    async registrar() {
        const payload = {
            protocolo: document.getElementById('sensor-protocolo').value,
            n: document.getElementById('sensor-nombre').value,
            id: document.getElementById('sensor-id-conn').value,
            m: document.getElementById('sensor-metrica').value,
            u: document.getElementById('sensor-unidad').value,
            lb: document.getElementById('add-ll').value, // Renombramos internamente para BD
            la: document.getElementById('add-lh').value,
            db: document.getElementById('add-db').value,
            off: document.getElementById('add-off').value,
            nodo_id: document.getElementById('sensor-nodo-id').value
        };

        if (!payload.n || !payload.id) {
            if (typeof UIUtils !== 'undefined') UIUtils.showToast("Faltan datos clave (Nombre o ID)", 'error');
            else alert("⚠️ Faltan datos clave (Nombre o ID)");
            return;
        }

        // 1. Decidimos a qué ruta enviar (Crear vs Editar)
        const ruta = this.modoEdicion ? '/api/admin/editar_sensor' : '/api/admin/config_sensores';
        if (this.modoEdicion) payload.original_n = this.nombreOriginalEditar;

        if (typeof UIUtils !== 'undefined') UIUtils.setLoading('btn-save-node', true);

        try {
            const res = await fetch(ruta, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if (data.status === 'success') {
                document.getElementById('modal-agregar-sensor').classList.add('hidden');
                if (typeof UIUtils !== 'undefined') UIUtils.showToast("Nodo guardado con éxito", 'success');
                // Al editar, forzamos un borrado de la fila en el DOM para que se regenere limpia
                if (this.modoEdicion) {
                    const row = document.getElementById(`row-${this.nombreOriginalEditar}`);
                    if (row) row.remove();
                }
            } else {
                if (typeof UIUtils !== 'undefined') UIUtils.showToast(data.error || "Error al guardar", 'error');
                else alert("⛔ Error: " + data.error);
            }
        } catch (e) {
            console.error(e);
            if (typeof UIUtils !== 'undefined') UIUtils.showToast("Falla de red al registrar el nodo", 'error');
            else alert("❌ Falla de red al registrar el nodo.");
        } finally {
            if (typeof UIUtils !== 'undefined') UIUtils.setLoading('btn-save-node', false);
        }
    },

    async eliminar(nombre) {
        if (!confirm(`⚠️ ¿Estás seguro de eliminar el activo: ${nombre}?`)) return;
        try {
            const res = await fetch('/api/admin/eliminar_sensor', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ n: nombre })
            });
            const data = await res.json();
            if (data.status !== 'success') alert("Error al eliminar: " + data.error);
        } catch (e) { console.error(e); }
    },

    async updateLimit(nombre, valor, tipo) {
        const ruta = tipo === 'alto' ? '/api/admin/update_high_limit' : '/api/admin/update_low_limit';
        try {
            const res = await fetch(ruta, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ n: nombre, v: valor })
            });
            if (!res.ok) alert("⚠️ No se pudo actualizar el límite en la base de datos.");
        } catch (e) { console.error(e); }
    }
};

/**
 * WIDGET PARA TELECONTROL (ESCRITURA A PLC)
 */
const TelecontrolWidget = {
    sensorActual: null,
    
    abrir(nombreSensor, tipoMetrica) {
        this.sensorActual = nombreSensor;
        document.getElementById('telecontrol-sensor').value = nombreSensor + " (" + (tipoMetrica || 'REAL') + ")";
        document.getElementById('telecontrol-valor').value = '';
        
        const realInput = document.getElementById('telecontrol-real-input');
        const boolInput = document.getElementById('telecontrol-bool-input');
        const execBtn = document.getElementById('btn-telecontrol-exec');
        
        if (tipoMetrica === 'BOOL') {
            if (realInput) realInput.classList.add('hidden');
            if (boolInput) boolInput.classList.remove('hidden');
            if (execBtn) execBtn.classList.add('hidden');
        } else {
            if (realInput) realInput.classList.remove('hidden');
            if (boolInput) boolInput.classList.add('hidden');
            if (execBtn) execBtn.classList.remove('hidden');
        }

        document.getElementById('modal-telecontrol').classList.remove('hidden');
        if (tipoMetrica !== 'BOOL') {
            setTimeout(() => document.getElementById('telecontrol-valor').focus(), 100);
        }
    },

    async enviarComando() {
        const valorRaw = document.getElementById('telecontrol-valor').value;
        if (valorRaw === '') {
            if (typeof UIUtils !== 'undefined') UIUtils.showToast("Ingresa un valor para enviar", 'error');
            else alert("Ingresa un valor para enviar.");
            return;
        }

        // HEURÍSTICA: Prevención de Errores (Validación de entrada)
        if (isNaN(Number(valorRaw))) {
            if (typeof UIUtils !== 'undefined') UIUtils.showToast("El valor debe ser numérico", 'error');
            else alert("El valor debe ser numérico.");
            return;
        }

        // HEURÍSTICA: Prevención de errores (Doble confirmación para acciones críticas)
        if (!confirm(`⚠️ PRECAUCIÓN:\n¿Estás seguro de enviar el comando [ ${valorRaw} ] al activo ${this.sensorActual}?`)) {
            return;
        }
        
        const payload = {
            sensor: this.sensorActual,
            valor: valorRaw
        };

        if (typeof UIUtils !== 'undefined') UIUtils.setLoading('btn-telecontrol-exec', true);

        try {
            const res = await fetch('/api/telecontrol/escribir', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (res.ok && data.status === 'success') {
                document.getElementById('modal-telecontrol').classList.add('hidden');
                if (typeof UIUtils !== 'undefined') UIUtils.showToast(`Comando exitoso: ${valorRaw}`, 'success');
                else alert(`✅ Comando enviado exitosamente: [ ${valorRaw} ] a ${this.sensorActual}`);
            } else {
                if (typeof UIUtils !== 'undefined') UIUtils.showToast(data.error || "Error de Telecontrol", 'error');
                else alert("⛔ Acceso Denegado o Error: " + (data.error || "Fallo desconocido"));
            }
        } catch (e) {
            console.error(e);
            if (typeof UIUtils !== 'undefined') UIUtils.showToast("Falla de red", 'error');
            else alert("❌ Falla de red al intentar enviar el comando.");
        } finally {
            if (typeof UIUtils !== 'undefined') UIUtils.setLoading('btn-telecontrol-exec', false);
        }
    }
};