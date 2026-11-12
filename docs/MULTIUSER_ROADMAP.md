# Hoja de ruta multiusuario

## Objetivo
Permitir que cualquier persona cree su cuenta y use WA-Bridge AI sin acceder a los datos de otras cuentas.

## Estado
El MVP actual es local y de un solo usuario. No habilitar registro público ni exponer el servidor a Internet.

## Requisitos antes del lanzamiento
- Registro e inicio de sesión; contraseñas con hash Argon2id o scrypt, nunca texto plano.
- Cookies HttpOnly, Secure y SameSite; rotación y expiración de sesión.
- Protección CSRF, límites de intentos y validación de entradas.
- Aislamiento por usuario de contactos, borradores, tareas, historial, preferencias y conexiones.
- Pruebas automatizadas de acceso cruzado entre dos cuentas para lectura, edición y borrado.
- Secretos fuera de Git; HTTPS, copias de seguridad, retención y eliminación de datos.
- Límites de uso y controles anti-spam.
- Revisión de condiciones y elegibilidad de las integraciones oficiales de WhatsApp.

## Arquitectura prevista
Cada petición debe tener una identidad autenticada. Todas las consultas deben filtrar por el identificador de esa identidad. Las credenciales de integraciones se separan por cuenta y se cifran cuando corresponda. Ollama local sirve para desarrollo; para múltiples usuarios concurrentes se necesitará infraestructura de IA dimensionada y cuotas por usuario.

## Presupuesto
Objetivo inicial menor a 10 GB. Límite de planificación ampliado a 20 GB si es necesario. No descargar modelos adicionales ni almacenar medios de WhatsApp por defecto.
