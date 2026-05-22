import time
import threading
import psutil
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.smi import builder, instrum, exval
from pysnmp.proto.api import v2c

print("🕵️‍♂️ Iniciando Agente Encubierto SNMP de Hardware...")

snmpEngine = engine.SnmpEngine()

# Configurar puerto UDP 161 (Requiere sudo en Linux)
try:
    config.addTransport(
        snmpEngine,
        udp.domainName,
        udp.UdpTransport().openServerMode(('0.0.0.0', 161))
    )
except Exception as e:
    print(f"❌ Error al abrir puerto 161: {e}\n(Recuerda ejecutar el script con 'sudo' en Linux)")
    exit(1)

# Configurar seguridad (Comunidad: public)
config.addV1System(snmpEngine, 'my-area', 'public')
config.addVacmUser(snmpEngine, 2, 'my-area', 'noAuthNoPriv', (1,3,6,1,4,1,9999), (1,3,6,1,4,1,9999))

snmpContext = context.SnmpContext(snmpEngine)
mibBuilder = snmpContext.getMibInstrum().getMibBuilder()

MibScalar, MibScalarInstance = mibBuilder.importSymbols('SNMPv2-SMI', 'MibScalar', 'MibScalarInstance')

# Creación de MIBs personalizadas (OIDs)
cpu_obj = MibScalar((1,3,6,1,4,1,9999,1,1), v2c.OctetString())
ram_obj = MibScalar((1,3,6,1,4,1,9999,1,2), v2c.OctetString())
disk_obj = MibScalar((1,3,6,1,4,1,9999,1,3), v2c.OctetString())

cpu_inst = MibScalarInstance(cpu_obj.name, (0,), cpu_obj.syntax)
ram_inst = MibScalarInstance(ram_obj.name, (0,), ram_obj.syntax)
disk_inst = MibScalarInstance(disk_obj.name, (0,), disk_obj.syntax)

mibBuilder.exportSymbols('CUSTOM-HW-MIB', cpu_obj=cpu_obj, ram_obj=ram_obj, disk_obj=disk_obj, cpu_inst=cpu_inst, ram_inst=ram_inst, disk_inst=disk_inst)

# Hilo de monitoreo en tiempo real
def update_metrics():
    # Inicializar CPU
    psutil.cpu_percent(interval=None)
    while True:
        try:
            # Extraer métricas vitales
            cpu_val = psutil.cpu_percent(interval=None)
            ram_val = psutil.virtual_memory().percent
            disk_val = psutil.disk_usage('/').percent
            
            # Actualizar valores en el motor SNMP
            cpu_inst.syntax = cpu_inst.syntax.clone(str(cpu_val))
            ram_inst.syntax = ram_inst.syntax.clone(str(ram_val))
            disk_inst.syntax = disk_inst.syntax.clone(str(disk_val))
            
        except Exception as e:
            print(f"Error actualizando métricas: {e}")
        time.sleep(1)

threading.Thread(target=update_metrics, daemon=True).start()

# Activar el responder de lectura (GET)
cmdrsp.GetCommandResponder(snmpEngine, snmpContext)

print("✅ Agente Encubierto SNMP activo y escuchando en 0.0.0.0:161")
print("OIDs mapeados:")
print(" - CPU : 1.3.6.1.4.1.9999.1.1.0")
print(" - RAM : 1.3.6.1.4.1.9999.1.2.0")
print(" - DISK: 1.3.6.1.4.1.9999.1.3.0")

snmpEngine.transportDispatcher.jobStarted(1)
try:
    snmpEngine.transportDispatcher.runDispatcher()
except KeyboardInterrupt:
    snmpEngine.transportDispatcher.closeDispatcher()
