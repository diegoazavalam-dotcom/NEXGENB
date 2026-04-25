/**
 * SEGURIDAD Y CONTROL DE INTERFAZ
 * Maneja el acceso, login, logout y la apertura de modales de configuración.
 */
const AuthManager = {
    name: "AuthManager",

    // --- Gestión de Acceso ---
    async login() {
        const u = document.getElementById('u').value;
        const p = document.getElementById('p').value;

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ usuario: u, password: p })
            });
            const data = await res.json();

            if (data.status === 'success') {
                window.location.reload(); // Recargamos para que Flask valide la sesión
            } else {
                alert("❌ Credenciales inválidas");
            }
        } catch (e) {
            console.error("Error en login:", e);
        }
    },

    async logout() {
        await fetch('/api/auth/logout');
        window.location.reload();
    },

    // --- Control de Modales (UI) ---
    abrirConfiguracion() {
        const modal = document.getElementById('modal-agregar-sensor');
        if (modal) modal.classList.remove('hidden');
    },

    cerrarModales() {
        document.querySelectorAll('[id^="modal-"]').forEach(m => {
            m.classList.add('hidden');
        });
    },

    // --- Utilidades de Auditoría ---
    async descargarBackup() {
        try {
            window.location.href = '/api/admin/backup_db';
        } catch (e) {
            console.error("Error al descargar backup:", e);
        }
    }
};

// Listener para cerrar modales con la tecla ESC
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') AuthManager.cerrarModales();
});