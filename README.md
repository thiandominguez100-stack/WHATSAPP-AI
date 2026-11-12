# WA-Bridge AI

Asistente web **personal y local** para trabajar únicamente con el WhatsApp del propietario del equipo. No tendrá registro público ni cuentas para terceros.

> Estado: MVP local. La aplicación prepara borradores y abre conversaciones mediante enlaces oficiales `wa.me`; el usuario revisa y confirma el envío. Esta versión no automatiza WhatsApp Web ni lee conversaciones privadas.

## Alcance: fases 1 a 5

1. **Fundación:** repositorio, estructura, documentación y entorno Python.
2. **Motor de comandos:** interpretar instrucciones en español y convertirlas en operaciones estructuradas.
3. **Sistema multi-IA:** adaptadores para proveedores compatibles y modelos locales como Ollama.
4. **Seguridad:** herramientas permitidas, validación de entradas, confirmación humana y registro de actividad.
5. **Simulador de WhatsApp:** probar flujos de búsqueda, clasificación y preparación de mensajes con datos de prueba.

La integración con una cuenta real de WhatsApp queda fuera de estas cinco fases. Se evaluará después mediante mecanismos autorizados. No se extraen cookies, códigos, tokens ni sesiones de WhatsApp Web.

## Funciones actuales

- Chat en español con intérprete local y adaptador compatible con OpenAI Chat Completions.
- Configuración para Ollama local con `qwen2.5:1.5b`.
- Contactos, borradores, tareas e historial en SQLite.
- Catálogo de herramientas permitidas; el modelo no ejecuta código arbitrario.
- Enlaces oficiales para abrir WhatsApp y revisar manualmente el borrador.

## Requisitos

- Windows 10/11 y Python 3.10 o superior.
- Ollama instalado y el modelo `qwen2.5:1.5b` descargado (ya está instalado en el equipo del propietario).
- No se necesita volver a descargar el modelo.

## Instalación en Windows

Abre PowerShell dentro de la carpeta del repositorio:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_windows.ps1
```

Después inicia la aplicación:

```powershell
.\run_windows.ps1
```

Abre http://127.0.0.1:5000. El instalador crea el entorno virtual, instala dependencias y crea `.env` solo si todavía no existe. No sobrescribe tu configuración ni descarga modelos de Ollama.

Comprueba el modelo con `ollama list`. Ollama debe estar ejecutándose en `http://127.0.0.1:11434`.

## Seguridad y privacidad

- Esta versión es para un único usuario en el equipo local. No la publiques en Internet ni la expongas a la red.
- No introduzcas códigos de verificación, cookies, tokens de sesión ni contraseñas de WhatsApp.
- No se incluye automatización no oficial, lectura de sesiones ni envío automático.
- Antes de enviar, revisa el destinatario y el contenido dentro de WhatsApp.

## Almacenamiento

Objetivo inicial: mantener el proyecto y sus datos por debajo de 10 GB; ampliar hasta 20 GB solo si fuera necesario. Los modelos locales no se descargan desde los scripts de instalación. Qwen 2.5 1.5B ya está instalado y ocupa aproximadamente 1 GB.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

GitHub Actions ejecuta las pruebas al actualizar la rama principal o abrir un pull request.

## Estado

El trabajo se limita deliberadamente a las fases 1–5 y a una sola cuenta personal. No se desarrollará registro multiusuario ni gestión de WhatsApp de terceros en este proyecto.
