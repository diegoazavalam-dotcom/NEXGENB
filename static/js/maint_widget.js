const MaintWidget = {
    // Función que ya usas para guardar
    abrirReporte(sensorName) {
        const nota = prompt(`Descripción de la intervención para ${sensorName}:`);
        if (nota) {
            const user = document.getElementById('user-display').innerText.split('|')[0].trim();
            fetch('/api/mantenimiento', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ sensor: sensorName, operador: user, nota: nota })
            }).then(() => alert("Intervención registrada en DB"));
        }
    },

    // Nueva función para ver la bitácora
    async mostrarBitacora() {
        const res = await fetch('/api/historial_mantenimiento');
        const logs = await res.json();
        
        let html = `<div id="maint-log" class="fixed inset-0 z-[300] bg-black/80 flex items-center justify-center p-4">
            <div class="glass w-full max-w-2xl p-8 rounded-[2rem] border border-white/10">
                <div class="flex justify-between mb-6">
                    <h2 class="text-white font-black italic">BITÁCORA DE <span class="text-blue-500">MANTENIMIENTO</span></h2>
                    <button onclick="document.getElementById('maint-log').remove()" class="text-white">CERRAR ✕</button>
                </div>
                <table class="w-full text-left text-[10px]">
                    <tr class="text-gray-500 border-b border-white/5">
                        <th class="pb-2">FECHA</th><th class="pb-2">SENSOR</th><th class="pb-2">OP</th><th class="pb-2">NOTA</th>
                    </tr>
                    ${logs.map(l => `
                        <tr class="border-b border-white/5">
                            <td class="py-2 text-gray-400">${l[3].split(' ')[1]}</td>
                            <td class="py-2 text-blue-400 font-bold">${l[0]}</td>
                            <td class="py-2 text-white">${l[1]}</td>
                            <td class="py-2 text-gray-300 italic">${l[2]}</td>
                        </tr>
                    `).join('')}
                </table>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', html);
    }
};

// Escuchar la tecla "H" para abrir la bitácora
document.addEventListener('keydown', (e) => {
    if(e.key.toLowerCase() === 'h') MaintWidget.mostrarBitacora();
});