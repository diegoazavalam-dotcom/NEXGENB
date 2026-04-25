/**
 * MÓDULO DE ADMINISTRACIÓN: AdminWidget
 * Gestiona la creación, visualización y eliminación de usuarios del SCADA.
 */
const AdminWidget = {
    init() {
        console.log("🛡️ Módulo de Administración de Usuarios cargado.");
    },

    async mostrarUsuarios() {
        let modal = document.getElementById('modal-admin-usuarios');
        if (!modal) {
            this.crearModalUI();
            modal = document.getElementById('modal-admin-usuarios');
        }
        
        modal.classList.remove('hidden');
        await this.cargarUsuarios();
    },

    cerrar() {
        const modal = document.getElementById('modal-admin-usuarios');
        if (modal) modal.classList.add('hidden');
    },

    crearModalUI() {
        const html = `
        <div id="modal-admin-usuarios" class="fixed inset-0 z-[4000] hidden bg-black/95 flex items-center justify-center p-4 backdrop-blur-xl transition-all">
            <div class="glass-panel w-full max-w-5xl p-8 rounded-[2.5rem] border border-white/10 shadow-2xl relative flex flex-col h-[80vh]">
                
                <div class="flex justify-between items-center mb-6 border-b border-white/5 pb-4">
                    <div>
                        <h2 class="text-2xl font-black text-white tracking-tighter uppercase">Gestión de <span class="text-blue-500">Credenciales</span></h2>
                        <p class="text-[9px] text-gray-400 font-bold tracking-[0.4em] uppercase mt-1">Control de Acceso SCADA</p>
                    </div>
                    <button onclick="AdminWidget.cerrar()" class="text-gray-500 hover:text-white text-3xl leading-none transition-colors">&times;</button>
                </div>
                
                <div class="flex flex-col md:flex-row gap-6 h-full overflow-hidden">
                    <div class="w-full md:w-1/3 bg-white/5 p-6 rounded-2xl border border-white/5 flex flex-col gap-4">
                        <h3 class="text-[10px] font-black text-blue-400 uppercase tracking-widest mb-2">Nuevo Operador</h3>
                        
                        <input type="text" id="new-user" placeholder="Nombre de Usuario" class="w-full bg-black/40 border border-white/10 text-white p-3 rounded-xl text-xs outline-none focus:border-blue-500 font-bold">
                        <input type="password" id="new-pass" placeholder="Contraseña" class="w-full bg-black/40 border border-white/10 text-white p-3 rounded-xl text-xs outline-none focus:border-blue-500 font-bold">
                        
                        <select id="new-role" class="w-full bg-black/40 border border-white/10 text-gray-300 p-3 rounded-xl text-xs outline-none focus:border-blue-500 font-bold uppercase">
                            <option value="OPERADOR">Operador (Básico)</option>
                            <option value="ADMIN_SCADA">Administrador SCADA</option>
                            <option value="MANTENIMIENTO">Mantenimiento</option>
                        </select>
                        
                        <button onclick="AdminWidget.crearUsuario()" class="w-full mt-auto bg-blue-600 hover:bg-blue-500 text-white py-4 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-blue-600/20">Registrar Credencial</button>
                    </div>

                    <div class="w-full md:w-2/3 bg-black/40 rounded-2xl border border-white/5 overflow-y-auto custom-scrollbar">
                        <table class="w-full text-left">
                            <thead class="sticky top-0 bg-[#0d1117] z-10 shadow-md">
                                <tr class="text-[9px] uppercase tracking-[0.2em] text-gray-500 border-b border-white/5">
                                    <th class="p-4">Usuario</th>
                                    <th class="p-4">Rol de Sistema</th>
                                    <th class="p-4">Grupo</th>
                                    <th class="p-4 text-right">Acción</th>
                                </tr>
                            </thead>
                            <tbody id="admin-table-body" class="divide-y divide-white/5 font-mono text-[11px] text-gray-300">
                                </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', html);
    },

    async cargarUsuarios() {
        const tbody = document.getElementById('admin-table-body');
        tbody.innerHTML = `<tr><td colspan="4" class="text-center p-8 opacity-50 font-bold tracking-widest uppercase">Cargando usuarios...</td></tr>`;
        
        try {
            const res = await fetch('/api/admin/usuarios', { credentials: 'include' });
            if (!res.ok) throw new Error("Fallo en servidor");
            
            const usuarios = await res.json();
            
            tbody.innerHTML = usuarios.map(u => {
                const esAdmin = u.role.includes('ADMIN');
                const badgeColor = esAdmin ? 'text-red-400 border-red-500/30 bg-red-500/10' : 'text-blue-400 border-blue-500/30 bg-blue-500/10';
                
                return `
                <tr class="hover:bg-white/5 transition-colors">
                    <td class="p-4 font-black text-white">${u.username}</td>
                    <td class="p-4">
                        <span class="${badgeColor} px-2 py-1 rounded-md text-[8px] font-black tracking-[0.2em] uppercase border drop-shadow-md">
                            ${u.role}
                        </span>
                    </td>
                    <td class="p-4 text-gray-500">${u.grupo}</td>
                    <td class="p-4 text-right">
                        ${u.username.toLowerCase() !== 'admin' ? 
                            `<button onclick="AdminWidget.eliminarUsuario('${u.username}')" class="text-red-500 hover:text-white bg-red-500/10 hover:bg-red-600 px-3 py-1.5 rounded-lg transition-all font-bold tracking-widest text-[8px]">ELIMINAR</button>` : 
                            `<span class="text-[8px] text-gray-600 uppercase font-black tracking-widest">Protegido</span>`
                        }
                    </td>
                </tr>`;
            }).join('');
        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center p-8 text-red-500 font-bold uppercase tracking-widest">Error al cargar datos.</td></tr>`;
        }
    },

    async crearUsuario() {
        const u = document.getElementById('new-user').value.trim();
        const p = document.getElementById('new-pass').value.trim();
        const r = document.getElementById('new-role').value;

        if (!u || !p) return alert("⚠️ Ingrese un usuario y una contraseña.");

        try {
            const res = await fetch('/api/admin/usuarios', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: u, password: p, role: r, grupo: 'PLANTA' })
            });
            const data = await res.json();
            
            if (data.status === 'success') {
                document.getElementById('new-user').value = '';
                document.getElementById('new-pass').value = '';
                this.cargarUsuarios(); // Refrescar la tabla
            } else {
                alert("⛔ " + (data.error || "No se pudo crear. ¿El usuario ya existe?"));
            }
        } catch (e) { alert("❌ Error de red."); }
    },

    async eliminarUsuario(username) {
        if (!confirm(`⚠️ PELIGRO: ¿Está seguro de eliminar permanentemente al usuario '${username}'?`)) return;

        try {
            const res = await fetch(`/api/admin/usuarios?username=${encodeURIComponent(username)}`, { method: 'DELETE' });
            const data = await res.json();
            
            if (data.status === 'success') {
                this.cargarUsuarios();
            } else {
                alert("⛔ " + (data.error || "No se pudo eliminar."));
            }
        } catch (e) { alert("❌ Error de red."); }
    }
};

document.addEventListener('DOMContentLoaded', () => { AdminWidget.init(); });