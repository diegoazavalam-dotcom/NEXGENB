/**
 * SCADA ENGINE V7.5 - El Motor Central
 * Se encarga única y exclusivamente de traer los datos y repartirlos.
 * No toca el HTML, no dibuja nada (excepto contadores globales). Solo es el "corazón" del sistema.
 */
const ScadaEngine = {
    intervalo: 1000, // 1 segundo (1000 milisegundos)
    timer: null,
    subscriptores: [], // Aquí guardaremos qué módulos quieren recibir datos
    isActive: true, // Control para saber si la pestaña está visible

    // 1. Método para conectar un módulo al motor
    suscribir(modulo) {
        if (modulo && typeof modulo.update === 'function') {
            this.subscriptores.push(modulo);
            console.log(`🔌 Módulo conectado al motor: ${modulo.name || 'Desconocido'}`);
        } else {
            console.warn("⚠️ Intento de suscribir un módulo inválido o sin función update().");
        }
    },

    // 2. El latido del corazón: Trae los datos
    async tick() {
        // Si la pestaña no está visible, no hacemos peticiones (Ahorro de RAM/Red)
        if (!this.isActive) return;

        try {
            // Hacemos la petición a la API que ya tienes en app.py
            const response = await fetch('/api/telemetria', {
                credentials: 'include' // Asegura que la cookie de sesión (login) viaje
            });

            // Si el servidor responde 401 (Sesión expirada), forzamos recarga
            if (response.status === 401) {
                console.warn("⚠️ Sesión bloqueada. Deteniendo motor para evitar bucle.");
                this.detener(); // <--- IMPORTANTE: Esto apaga el timer
                
                // Solo mostramos el login, NO recargamos
                if (window.AuthWidget) {
                    window.AuthWidget.gestionarUI(false, null);
                }
                return;
            }

            const data = await response.json();

            if (data.status === 'ok' && data.sensores) {
                // MODIFICACIÓN: Pasamos TODO el objeto de datos, no solo los sensores
                this.distribuir(data);
            }
        } catch (error) {
            console.error("⚠️ Error de red en el latido del SCADA:", error);
        }
    },

    // 3. Repartidor de datos
distribuir(data) {
        const sensores = data.sensores || [];
        const totalIncidencias = data.total_incidencias || 0;

        // 2. Actualizamos contador global de sensores
        const badgeSensores = document.getElementById('count-sensores');
        if (badgeSensores) badgeSensores.innerText = sensores.length;

        // 3. --- AQUÍ ESTÁ EL CAMBIO: Usamos 'count-alertas' en lugar de 'badge-incidencias' ---
        const badgeIncidencias = document.getElementById('count-alertas'); 
        if (badgeIncidencias) {
            badgeIncidencias.innerText = totalIncidencias;
            
            // Efecto visual dinámico
            if (totalIncidencias > 0) {
                badgeIncidencias.classList.add('animate-pulse'); // Mantenemos el rojo que ya tiene tu HTML
            } else {
                badgeIncidencias.classList.remove('animate-pulse');
            }
        }

        // 4. Repartimos a HMI_Logic
        this.subscriptores.forEach(modulo => {
            try {
                modulo.update(sensores);
            } catch (e) {
                console.error(`Error en el módulo ${modulo.name}:`, e);
            }
        });
    },

    // 4. Inteligencia de visibilidad (Ahorro de energía)
    iniciarControlEnergia() {
        document.addEventListener("visibilitychange", () => {
            if (document.hidden) {
                this.isActive = false;
                console.log("⏸️ SCADA en pausa (Pestaña oculta)");
            } else {
                this.isActive = true;
                console.log("▶️ SCADA reactivado");
                this.tick(); // Forzamos un latido inmediato al volver
            }
        });
    },

    // 5. Encendido del motor
    iniciar() {
        if (this.timer) return; // Evita que se inicie dos veces
        
        console.log("🚀 Motor SCADA Iniciado.");
        this.iniciarControlEnergia();
        
        // Arrancamos el ciclo infinito
        this.timer = setInterval(() => this.tick(), this.intervalo);
        
        // Hacemos un primer latido inmediato para no esperar 1 segundo
        this.tick();
    },

    // 6. Apagado del motor (Útil para cuando cierras sesión)
    detener() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
            console.log("🛑 Motor SCADA Detenido.");
        }
    }
};