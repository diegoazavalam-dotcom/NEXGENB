/**
 * MÓDULO DE NOTIFICACIONES: AlertsWidget
 * Se encarga de gestionar la conexión con el Bot de Telegram para alertas críticas.
 */
const AlertsWidget = {
    init() {
        console.log("🔔 Módulo de Telegram preparado.");
    },

    async abrirModal() {
        // Mostramos el modal que ya existe en tu index.html
        document.getElementById('modal-alertas').classList.remove('hidden');
        
        // Pedimos al servidor la configuración actual para llenar los inputs
        try {
            const res = await fetch('/api/admin/telegram', { credentials: 'include' });
            if (res.ok) {
                const config = await res.json();
                if (config) {
                    document.getElementById('alert-token').value = config.token || '';
                    document.getElementById('alert-chatid').value = config.chat_id || '';
                }
            }
        } catch (e) {
            console.warn("⚠️ No se pudo cargar la config previa de Telegram.");
        }
    },

    async guardar() {
        const token = document.getElementById('alert-token').value.trim();
        const chat_id = document.getElementById('alert-chatid').value.trim();
        
        // Si hay token y chat, se activa. Si los borras, se desactiva el bot.
        const activo = (token.length > 5 && chat_id.length > 3) ? 1 : 0;

        const payload = {
            token: token,
            chat_id: chat_id,
            activo: activo
        };

        const btn = document.querySelector('#modal-alertas button:last-child');
        const txtOriginal = btn.innerText;
        btn.innerText = "Sincronizando...";
        btn.disabled = true;

        try {
            const res = await fetch('/api/admin/telegram', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if (data.status === 'success') {
                alert(activo ? "✅ Bot de Telegram ACTIVADO y sincronizado con éxito." : "⏸️ Bot de Telegram DESACTIVADO.");
                document.getElementById('modal-alertas').classList.add('hidden');
            } else {
                alert("⛔ Error al guardar: " + data.error);
            }
        } catch (e) {
            console.error(e);
            alert("❌ Fallo de comunicación con el servidor.");
        } finally {
            btn.innerText = txtOriginal;
            btn.disabled = false;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => { AlertsWidget.init(); });