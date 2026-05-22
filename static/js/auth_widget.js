const AuthWidget = {
    init() {
        console.log("🔧 AuthWidget: Iniciando...");
        const btnLogin = document.getElementById('btn-login');
        if (btnLogin) btnLogin.onclick = (e) => { e.preventDefault(); this.login(); };
        this.verificarAcceso();
    },

    async login() {
        const u = document.getElementById('u').value;
        const p = document.getElementById('p').value;
        if (!u || !p) return UIUtils.showToast("Ingresa credenciales", 'error');

        if (typeof UIUtils !== 'undefined') UIUtils.setLoading('btn-login', true);

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: u, password: p })
            });
            const data = await res.json();
            
            if (data.logged_in) {
                if (typeof UIUtils !== 'undefined') UIUtils.showToast("Acceso Concedido", 'success');
                setTimeout(() => window.location.reload(), 800);
            } else {
                if (typeof UIUtils !== 'undefined') UIUtils.showToast(data.message || "Credenciales inválidas", 'error');
            }
        } catch (e) {
            console.error(e);
            if (typeof UIUtils !== 'undefined') UIUtils.showToast("Error de red", 'error');
        } finally {
            if (typeof UIUtils !== 'undefined') UIUtils.setLoading('btn-login', false);
        }
    },

    // --- NUEVA FUNCIÓN LOGOUT ---
    async logout() {
        try {
            console.log("🚀 Deteniendo sistemas y cerrando sesión...");
            
            // 1. DETENER INTERVALOS (Evita los errores 401 en consola)
            // Esto busca todos los intervalos activos y los mata
            for (let i = 1; i < 1000; i++) {
                window.clearInterval(i);
            }

            // 2. Avisar al servidor
            await fetch('/logout', { method: 'GET', cache: 'no-store' });
            
            // 3. Limpieza de memorias
            sessionStorage.clear();
            localStorage.clear();

            // 4. Redirección limpia
            window.location.href = "/?logged_out=" + Date.now();
            
        } catch (e) {
            window.location.href = "/";
        }
    },

async verificarAcceso() {
        try {
            const res = await fetch('/api/auth/check', { cache: 'no-store' });
            if (!res.ok) {
                // Si el check falla (401, 500, etc), bloqueamos
                return this.gestionarUI(false, null);
            }
            const data = await res.json();
            // Si el servidor dice que NO está logueado explícitamente
            if (!data.logged_in) {
                return this.gestionarUI(false, null);
            }
            this.gestionarUI(true, data);
        } catch (e) { 
            console.error("⚠️ Error crítico de auth:", e);
            this.gestionarUI(false, null); 
        }
    },

    gestionarUI(isLoggedIn, data) {
        const modal = document.getElementById('modal-login');
        const dashboard = document.getElementById('main-dashboard');
        const overlay = document.getElementById('login-overlay');
        const btnAdmin = document.getElementById('btn-admin-seguridad');

        if (isLoggedIn && data) {
            if(modal) modal.classList.add('hidden');
            if(dashboard) dashboard.classList.remove('hidden');
            if(overlay) overlay.classList.add('hidden');
            
            const userRole = data.role || data.rol;
            if (userRole === 'ADMIN_TOTAL') {
                if(btnAdmin) btnAdmin.classList.remove('hidden');
            } else {
                if(btnAdmin) btnAdmin.classList.add('hidden');
            }
            if(typeof HMI_Logic !== 'undefined' && !HMI_Logic.activo) HMI_Logic.reactivar();
        } else {
            if(dashboard) dashboard.classList.add('hidden');
            if(overlay) overlay.classList.remove('hidden');
            // Si no hay sesión, mostramos el modal de entrada
            if(modal) modal.classList.remove('hidden');
        }
    }
};

document.addEventListener('DOMContentLoaded', () => AuthWidget.init());