# Decisión de alcance: aplicación personal

WA-Bridge AI se mantiene como una herramienta **local, personal y de un solo usuario**.

No se implementarán:
- Registro público ni inicio de sesión para terceros.
- Cuentas múltiples o aislamiento multiusuario.
- Administración de cuentas de WhatsApp de otras personas.
- Despliegue público o servicio alojado para terceros.

La aplicación debe escuchar únicamente en una interfaz de loopback y rechazar conexiones remotas. Esta decisión prevalece sobre cualquier propuesta multiusuario anterior.

El foco de desarrollo es completar las fases 1 a 5 para el uso personal del propietario: base técnica, motor de comandos, proveedor de IA local/compatible, controles de seguridad y simulador con datos ficticios.

La conexión con una cuenta real de WhatsApp se evaluará después, mediante mecanismos autorizados y con revisión humana de los mensajes. No se extraerán cookies, códigos de verificación, tokens ni sesiones privadas.
