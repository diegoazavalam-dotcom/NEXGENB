/**
 * SCADA ENGINE V7.5 - El Motor Central (WEBSOCKETS EDITION)
 * Recibe datos del servidor instantáneamente sin hacer polling continuo.
 */
const ScadaEngine = {
    subscriptores: [],
    isActive: true,
    socket: null,

    // 1. Método para conectar un módulo al motor
    suscribir(modulo) {
        if (modulo && typeof modulo.update === 'function') {
            this.subscriptores.push(modulo);
            console.log(`🔌 Módulo conectado al motor: ${modulo.name || 'Desconocido'}`);
        } else {
            console.warn("⚠️ Intento de suscribir un módulo inválido o sin función update().");
        }
    },

    // 2. Repartidor de datos
    distribuir(data) {
        if (!this.isActive) return;

        const sensores = data.sensores || [];
        const totalIncidencias = data.total_incidencias || 0;

        // Actualizamos contador global de sensores
        const badgeSensores = document.getElementById('count-sensores');
        if (badgeSensores) badgeSensores.innerText = sensores.length;

        // Actualizamos alertas
        const badgeIncidencias = document.getElementById('count-alertas'); 
        if (badgeIncidencias) {
            badgeIncidencias.innerText = totalIncidencias;
            
            // Efecto visual dinámico
            if (totalIncidencias > 0) {
                badgeIncidencias.classList.add('animate-pulse');
            } else {
                badgeIncidencias.classList.remove('animate-pulse');
            }
        }

        // Repartimos a los sub-módulos
        this.subscriptores.forEach(modulo => {
            try {
                modulo.update(sensores);
            } catch (e) {
                console.error(`Error en el módulo ${modulo.name}:`, e);
            }
        });
    },

    // 3. Inteligencia de visibilidad (Ahorro de energía)
    iniciarControlEnergia() {
        document.addEventListener("visibilitychange", () => {
            if (document.hidden) {
                this.isActive = false;
                console.log("⏸️ SCADA en pausa visual (Pestaña oculta)");
            } else {
                this.isActive = true;
                console.log("▶️ SCADA visualmente reactivado");
            }
        });
    },

    // 4. Encendido del motor
    iniciar() {
        if (this.socket) return;
        
        console.log("🚀 Motor SCADA Iniciado en modo WebSocket.");
        this.iniciarControlEnergia();
        
        // Asume que la librería socket.io fue inyectada en el HTML
        if (typeof io !== 'undefined') {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('🟢 Conectado al Gateway SCADA en tiempo real');
            });

            this.socket.on('telemetria_update', (data) => {
                this.distribuir(data);
            });

            this.socket.on('disconnect', () => {
                console.warn('🔴 Desconectado del Gateway SCADA');
            });
        } else {
            console.error("❌ Librería Socket.IO no encontrada. Revisa tu HTML.");
        }
    },

    // 5. Apagado del motor (Útil para cuando cierras sesión)
    detener() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            console.log("🛑 Motor SCADA Desconectado.");
        }
    }
};