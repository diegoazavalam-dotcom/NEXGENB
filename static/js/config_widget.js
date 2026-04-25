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
        this.sensoresCache = sensores; // Guardamos para la edición
        const tbody = document.getElementById('tabla-sensores-body');
        if (!tbody) return;

        const currentIds = sensores.map(s => `row-${s.n}`);
        Array.from(tbody.children).forEach(tr => {
            if (!currentIds.includes(tr.id)) tr.remove();
        });

        sensores.forEach(sensor => {
            let tr = document.getElementById(`row-${sensor.n}`);
            const valorActual = parseFloat(sensor.val).toFixed(1);
            const esAlerta = valorActual > parseFloat(sensor.lh) || valorActual < parseFloat(sensor.ll);
            const colorTexto = esAlerta ? 'text-red-500 font-black animate-pulse' : 'text-green-400';

            if (!tr) {
                tr = document.createElement('tr');
                tr.id = `row-${sensor.n}`;
                tr.className = "text-[10px] uppercase tracking-widest text-gray-400 border-b border-white/5 hover:bg-white/5 transition-colors";
                
                tr.innerHTML = `
                    <td class="p-4 flex items-center gap-2">
                        <span class="w-2 h-2 rounded-full ${esAlerta ? 'bg-red-500 animate-pulse' : 'bg-green-500'} indicator-dot"></span>
                        <span class="font-black text-white">${sensor.n}</span>
                    </td>
                    <td class="p-4 font-mono text-[9px]">${sensor.protocolo || 'S7'} | ${sensor.id}</td>
                    <td class="p-4">
                        <span class="valor-vivo text-lg ${colorTexto}">${valorActual}</span> <span class="text-[8px]">${sensor.u || ''}</span>
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
                        <button onclick="HistorialWidget.abrir('${sensor.n}')" class="text-green-500 hover:text-white bg-green-500/10 hover:bg-green-600 px-3 py-1.5 rounded-lg transition-all font-bold tracking-widest text-[8px] mr-1">CHART</button>
                        <button onclick="ConfigWidget.abrirEdicion('${sensor.n}')" class="text-blue-500 hover:text-white bg-blue-500/10 hover:bg-blue-600 px-3 py-1.5 rounded-lg transition-all font-bold tracking-widest text-[8px] mr-1">EDITAR</button>
                        <button onclick="ConfigWidget.eliminar('${sensor.n}')" class="text-red-500 hover:text-white bg-red-500/10 hover:bg-red-600 px-3 py-1.5 rounded-lg transition-all font-bold tracking-widest text-[8px]">BORRAR</button>
                    </td>
                `;
                tbody.appendChild(tr);
            } else {
                const indicator = tr.querySelector('.indicator-dot');
                const valSpan = tr.querySelector('.valor-vivo');
                if (indicator) indicator.className = `w-2 h-2 rounded-full ${esAlerta ? 'bg-red-500 animate-pulse shadow-[0_0_10px_red]' : 'bg-green-500'} indicator-dot`;
                if (valSpan) {
                    valSpan.className = `valor-vivo text-lg transition-colors ${colorTexto}`;
                    valSpan.innerText = valorActual;
                }
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

        if (!payload.n || !payload.id) return alert("⚠️ Faltan datos clave (Nombre o ID)");

        // 1. Decidimos a qué ruta enviar (Crear vs Editar)
        const ruta = this.modoEdicion ? '/api/admin/editar_sensor' : '/api/admin/config_sensores';
        if (this.modoEdicion) payload.original_n = this.nombreOriginalEditar;

        try {
            const res = await fetch(ruta, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if (data.status === 'success') {
                document.getElementById('modal-agregar-sensor').classList.add('hidden');
                // Al editar, forzamos un borrado de la fila en el DOM para que se regenere limpia
                if (this.modoEdicion) {
                    const row = document.getElementById(`row-${this.nombreOriginalEditar}`);
                    if (row) row.remove();
                }
            } else {
                alert("⛔ Error: " + data.error);
            }
        } catch (e) {
            console.error(e);
            alert("❌ Falla de red al registrar el nodo.");
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