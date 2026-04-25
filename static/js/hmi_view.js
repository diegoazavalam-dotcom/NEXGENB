/**
 * ZONA ROJA 1: HMI VIEW (Layout Interactivo)
 * Renderiza los nodos sobre el plano y maneja el posicionamiento.
 */
const HMIView = {
    name: "HMIView",
    containerId: "hmi-layout",
    isEditMode: true, // Permitir mover sensores por defecto

    /**
     * update() es llamado por el ScadaEngine cada segundo
     */
    update(sensores) {
        const layout = document.getElementById(this.containerId);
        if (!layout) return;

        sensores.forEach(s => {
            let el = document.getElementById(`node-${s.n}`);
            
            // Si el sensor no existe en el DOM, lo creamos
            if (!el) {
                el = this.crearNodo(s);
                layout.appendChild(el);
            }

            // Actualizamos valor y estado de alerta
            const valorEl = el.querySelector('.node-value');
            const estaEnAlerta = s.v < s.ll || s.v > s.lh;

            if (valorEl) valorEl.innerText = `${s.v}${s.u || ''}`;
            
            // Animación de pulso si hay alarma
            el.classList.toggle('sensor-alerta', estaEnAlerta);
            el.style.borderColor = estaEnAlerta ? '#ef4444' : '#30363d';
        });
    },

    crearNodo(s) {
        const div = document.createElement('div');
        div.id = `node-${s.n}`;
        div.className = `absolute glass-panel p-2 rounded-lg border flex flex-col items-center min-w-[80px] cursor-move transition-shadow`;
        
        // Posición inicial (proporcional al contenedor)
        div.style.left = `${s.x}%`;
        div.style.top = `${s.y}%`;

        div.innerHTML = `
            <span class="text-[7px] font-black text-gray-500 uppercase tracking-tighter">${s.n}</span>
            <span class="node-value text-xs font-bold text-white tracking-tight">--</span>
            <div class="flex gap-1 mt-1">
                <div class="w-1 h-1 rounded-full bg-blue-500 animate-pulse"></div>
                <div class="w-1 h-1 rounded-full bg-gray-700"></div>
            </div>
        `;

        this.hacerDraggable(div, s.n);
        return div;
    },

    hacerDraggable(el, nombre) {
        let isDragging = false;
        
        el.addEventListener('mousedown', (e) => {
            isDragging = true;
            el.style.zIndex = 1000;
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            const layout = document.getElementById(this.containerId);
            const rect = layout.getBoundingClientRect();
            
            // Calculamos posición porcentual para que sea responsivo
            let x = ((e.clientX - rect.left) / rect.width) * 100;
            let y = ((e.clientY - rect.top) / rect.height) * 100;

            // Limitar dentro del cuadro
            x = Math.max(0, Math.min(95, x));
            y = Math.max(0, Math.min(95, y));

            el.style.left = `${x}%`;
            el.style.top = `${y}%`;
        });

        document.addEventListener('mouseup', async () => {
            if (!isDragging) return;
            isDragging = false;
            el.style.zIndex = 10;

            // Guardar nueva posición en DB
            const x = parseFloat(el.style.left);
            const y = parseFloat(el.style.top);
            
            try {
                await fetch('/api/admin/update_position', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ n: nombre, x: x, y: y })
                });
            } catch (e) {
                console.error("Error guardando posición:", e);
            }
        });
    },

    async subirPlano(input) {
        if (!input.files || !input.files[0]) return;
        const formData = new FormData();
        formData.append('file', input.files[0]);

        try {
            const res = await fetch('/api/admin/upload_plano', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.status === 'success') {
                document.getElementById(this.containerId).style.backgroundImage = `url('${data.path}?t=${Date.now()}')`;
            }
        } catch (e) {
            alert("Error al subir plano");
        }
    }
};