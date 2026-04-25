# services/alarm_service.py
def validar_umbral(sensor_config, valor_actual):
    if valor_actual > sensor_config['limite']:
        # Disparar evento de alerta
        return {"status": "ALERTA", "msg": f"Sensor {sensor_config['n']} excedido"}
    return {"status": "OK"}