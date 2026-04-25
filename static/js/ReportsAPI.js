// ReportsAPI.js CORREGIDO
export const ReportsAPI = {
    async getSensores() {
        // El error estaba en que las credenciales iban fuera del fetch
        const res = await fetch('/api/admin/config_sensores', {
            credentials: 'include' // <--- Ahora sí está dentro de la configuración del fetch
        });
        return await res.json();
    },

    async getDatosMasivos(sensores, inicio, fin) {
        const res = await fetch('/api/reportes/data_masiva', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ sensores, inicio, fin }),
            credentials: 'include' // Agregamos esto para evitar el 403 en reportes
        });
        return await res.json();
    }
};