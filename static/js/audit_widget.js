/**
 * MÓDULO DE SEGURIDAD: AuditWidget
 * Gestiona el visor de Trazabilidad ISO 9001 (Log de eventos del sistema)
 */
const AuditWidget = {
    init() {
        console.log("🔍 Módulo de Auditoría ISO preparado.");
    },

    async abrir() {
        // 1. Si el modal no existe en el HTML, lo inyectamos dinámicamente
        let modal = document.getElementById('modal-auditoria-iso');
        if (!modal) {
            this.crearModalUI();
            modal = document.getElementById('modal-auditoria-iso');
        }
        
        // 2. Mostramos la ventana
        modal.classList.remove('hidden');
        
        // 3. Cargamos los datos limpios desde PostgreSQL
        await this.cargarDatos();
    },

    cerrar() {
        const modal = document.getElementById('modal-auditoria-iso');
        if (modal) modal.classList.add('hidden');
    },

    crearModalUI() {
        const html = `
        <div id="modal-auditoria-iso" class="fixed inset-0 z-[4000] hidden bg-black/95 flex items-center justify-center p-4 backdrop-blur-xl transition-all">
            <div class="glass-panel w-full max-w-6xl p-8 rounded-[2.5rem] border border-white/10 shadow-2xl relative flex flex-col h-[85vh]">
                
                <div class="flex justify-between items-center mb-6">
                    <div>
                        <h2 class="text-2xl font-black text-white tracking-tighter uppercase">Traceability <span class="text-blue-500">Log</span></h2>
                        <p class="text-[9px] text-gray-400 font-bold tracking-[0.4em] uppercase mt-1">Auditoría ISO 9001 / CFR 21 Part 11</p>
                    </div>
                    <div class="flex gap-3">
                        <button onclick="window.location.href='/api/exportar/incidentes'" class="px-4 py-2 bg-green-600/20 hover:bg-green-600 text-green-500 hover:text-white rounded-xl text-[9px] font-black uppercase transition-all border border-green-500/20">Descargar Excel ISO</button>
                        <button onclick="AuditWidget.cerrar()" class="text-gray-500 hover:text-white text-3xl leading-none transition-colors">&times;</button>
                    </div>
                </div>
                
                <div class="flex flex-col md:flex-row gap-4 mb-4 bg-white/5 p-4 rounded-2xl border border-white/5">
                    <input type="text" id="audit-filter-user" placeholder="Filtrar por Usuario..." class="flex-1 bg-black/40 border border-white/10 text-white p-3 rounded-xl text-xs outline-none focus:border-blue-500 font-bold">
                    
                    <select id="audit-filter-action" class="flex-1 bg-black/40 border border-white/10 text-white p-3 rounded-xl text-xs outline-none focus:border-blue-500 font-bold uppercase">
                        <option value="">Todas las acciones</option>
                        <option value="LOGIN">Accesos (Login)</option>
                        <option value="INCIDENCIA_CERRADA">Cierre Alertas</option>
                        <option value="CIERRE_MASIVO">Cierre Masivo</option>
                        <option value="CONFIG_CHANGE">Cambios Configuración</option>
                        <option value="USER_MGMT">Gestión Usuarios</option>
                    </select>
                    
                    <input type="date" id="audit-filter-date" class="flex-1 bg-black/40 border border-white/10 text-white p-3 rounded-xl text-xs outline-none focus:border-blue-500">
                    
                    <button onclick="AuditWidget.cargarDatos()" class="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-blue-600/20">Filtrar</button>
                </div>

                <div class="flex-1 overflow-y-auto custom-scrollbar bg-black/40 rounded-2xl border border-white/5">
                    <table class="w-full text-left">
                        <thead class="sticky top-0 bg-[#0d1117] z-10 shadow-md">
                            <tr class="text-[9px] uppercase tracking-[0.2em] text-gray-500 border-b border-white/5">
                                <th class="p-4">Fecha / Hora Timestamp</th>
                                <th class="p-4">Usuario Operador</th>
                                <th class="p-4">Tipo de Acción</th>
                                <th class="p-4">Detalle de Trazabilidad</th>
                            </tr>
                        </thead>
                        <tbody id="audit-table-body" class="divide-y divide-white/5 font-mono text-[11px] text-gray-300">
                            </tbody>
                    </table>
                </div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', html);
    },

    async cargarDatos() {
        const tbody = document.getElementById('audit-table-body');
        tbody.innerHTML = `<tr><td colspan="4" class="text-center p-8 opacity-50 font-bold tracking-widest uppercase">Cargando registros criptográficos...</td></tr>`;
        
        const u = document.getElementById('audit-filter-user')?.value || '';
        const a = document.getElementById('audit-filter-action')?.value || '';
        const f = document.getElementById('audit-filter-date')?.value || '';

        try {
            // Llamamos a la API de Python pasando los filtros por URL
            const res = await fetch(`/api/admin/auditoria?u=${encodeURIComponent(u)}&a=${encodeURIComponent(a)}&f=${encodeURIComponent(f)}`, { credentials: 'include' });
            
            if (!res.ok) throw new Error("Fallo en servidor");
            const data = await res.json();
            const logs = data.logs || [];
            
            if (!logs || logs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" class="text-center p-8 opacity-50 text-red-400 font-bold uppercase tracking-widest">No se encontraron registros.</td></tr>`;
                return;
            }

            // Mapeamos los datos pintando "Badges" de colores según la acción
            tbody.innerHTML = logs.map(log => {
                let colorBadge = 'border-gray-500/30 text-gray-400 bg-gray-500/10';
                
                if (log.accion.includes('LOGIN')) colorBadge = 'border-blue-500/50 text-blue-400 bg-blue-500/10';
                if (log.accion.includes('CIERRE')) colorBadge = 'border-yellow-500/50 text-yellow-500 bg-yellow-500/10';
                if (log.accion.includes('CONFIG')) colorBadge = 'border-red-500/50 text-red-400 bg-red-500/10';
                if (log.accion.includes('USER')) colorBadge = 'border-purple-500/50 text-purple-400 bg-purple-500/10';

                return `
                <tr class="hover:bg-white/5 transition-colors group">
                    <td class="p-4 whitespace-nowrap text-[10px] text-gray-500 group-hover:text-gray-300 transition-colors">${log.fecha}</td>
                    <td class="p-4 font-black text-white uppercase">${log.usuario}</td>
                    <td class="p-4">
                        <span class="${colorBadge} px-2 py-1.5 rounded-md text-[8px] font-black tracking-[0.2em] uppercase border drop-shadow-md">
                            ${log.accion}
                        </span>
                    </td>
                    <td class="p-4 text-gray-400 italic font-sans text-xs">${log.detalle}</td>
                </tr>`;
            }).join('');

        } catch (e) {
            console.error("Error cargando auditoría:", e);
            tbody.innerHTML = `<tr><td colspan="4" class="text-center p-8 text-red-500 font-bold uppercase tracking-widest">Error de conexión con la base de datos de auditoría.</td></tr>`;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => { AuditWidget.init(); });