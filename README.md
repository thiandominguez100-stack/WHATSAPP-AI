# WA-Bridge AI

Asistente web modular para organizar contactos, interpretar instrucciones sencillas, preparar mensajes y administrar tareas.

> Estado: MVP local. WhatsApp se abre mediante enlaces oficiales `wa.me`; el usuario revisa y confirma el envío. No automatiza WhatsApp Web ni lee conversaciones privadas.

## Funciones actuales

- Chat con intérprete local y proveedor compatible con OpenAI Chat Completions.
- Configuración preparada para Ollama local con `qwen2.5:1.5b`.
- Contactos, borradores, tareas e historial en SQLite.
- Herramientas permitidas explícitamente; el modelo no ejecuta código arbitrario.

## Requisitos

- Windows 10/11, Python 3.10+ y Ollama (para Qwen local).
- Modelo `qwen2.5:1.5b` ya descargado. El instalador no lo vuelve a descargar.

## Instalación rápida en Windows

Abre PowerShell en la carpeta del repositorio:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_windows.ps1
```

Luego:

```powershell
.\run_windows.ps1
```

Abre http://127.0.0.1:5000. El script crea .venv, instala dependencias, comprueba Ollama y crea .env sin sobrescribir configuraciones existentes. Si el modelo ya está instalado, no se descarga de nuevo.

Comprueba el modelo con `ollama list`. La URL local configurada es `http://127.0.0.1:11434/v1`; Ollama debe estar ejecutándose.

## Uso

Agrega un contacto y prueba: `prepara un mensaje para Ana diciendo que mañana llego a las 10`. Revisa el borrador y abre WhatsApp para confirmar el envío. También puedes crear tareas o consultar tus listas.

## Seguridad

No introduzcas códigos de verificación, cookies, tokens de sesión ni contraseñas de WhatsApp. No se incluye automatización no oficial. No envíes mensajes masivos no solicitados. No expongas esta versión en Internet: todavía no tiene autenticación ni aislamiento multiusuario.

## Almacenamiento

No se descargan modelos automáticamente. El objetivo inicial es mantener el uso total del proyecto por debajo de 10 GB, con ampliación a 20 GB solo si hace falta. El modelo local Qwen ya instalado ocupa aproximadamente 1 GB.

## Estado multiusuario

El repositorio sigue siendo un MVP local de un solo usuario. Registro público, inicio de sesión, aislamiento de datos por cuenta, controles antiabuso y despliegue seguro son etapas pendientes. No basta con añadir una pantalla de registro: cada consulta y modificación debe quedar vinculada a la identidad autenticada y probarse contra accesos cruzados.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

GitHub Actions ejecuta pruebas al actualizar main o abrir un pull request.

## Licencia

Todavía no se ha definido una licencia.
