/**
 * ZONA ROJA 2: INVENTARIO DE ACTIVOS
 * Maneja la tabla inferior y las acciones de edición de límites.
 */
const InventoryTable = {
    name: "InventoryTable",
    containerId: "tabla-sensores-body",

    // Se ejecuta cuando el ScadaEngine recibe nuevos datos
    update(sensores) {
        const tbody = document.getElementById(this.containerId);
        if (!tbody) return;

        // Mapeamos los sensores a filas de tabla
        tbody.innerHTML = sensores.map(s => `
            <tr class="hover:bg-white/5 transition-colors border-b border-white/5">
                <td class="p-4 font-bold text-white">${s.n}</td>
                <td class="p-4 text-gray-500 font-mono text-[10px]">${s.id_conn || 'N/A'}</td>
                <td class="p-4">
                    <span class="px-2 py-1 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        ${s.v} ${s.u || ''}
                    </span>
                </td>
                <td class="p-4">
                    <input type="number" 
                        onchange="InventoryTable.cambiarLimite('${s.n}', this.value, 'low')"
                        class="w-16 bg-transparent border-b border-blue-500/30 text-blue-300 outline-none focus:border-blue-500" 
                        value="${s.ll}">
                </td>
                <td class="p-4">
                    <input type="number" 
                        onchange="InventoryTable.cambiarLimite('${s.n}', this.value, 'high')"
                        class="w-16 bg-transparent border-b border-red-500/30 text-red-300 outline-none focus:border-red-500" 
                        value="${s.lh}">
                </td>
                <td class="p-4 text-right">
                    <button onclick="InventoryTable.verHistorial('${s.n}')" class="text-gray-400 hover:text-white mx-2">📈</button>
                    <button onclick="InventoryTable.eliminar('${s.n}')" class="text-gray-600 hover:text-red-500">🗑️</button>
                </td>
            </tr>
        `).join('');
    },

    async cambiarLimite(nombre, valor, tipo) {
        const url = tipo === 'low' ? '/api/admin/update_low_limit' : '/api/admin/update_high_limit';
        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ n: nombre, v: valor })
            });
            if (res.ok) console.log(`✅ Límite ${tipo} actualizado para ${nombre}`);
        } catch (e) {
            console.error("Error actualizando límite:", e);
        }
    },

    verHistorial(nombre) {
        if (typeof HMI_Logic !== 'undefined') {
            HMI_Logic.mostrarHistorial(nombre);
        }
    },

    async eliminar(nombre) {
        if (!confirm(`¿Eliminar sensor ${nombre}?`)) return;
        try {
            const res = await fetch('/api/admin/eliminar_sensor', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ n: nombre })
            });
            if (res.ok) alert("Sensor eliminado");
        } catch (e) {
            alert("Error al eliminar");
        }
    }
};