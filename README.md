# WA-Bridge AI

Asistente web modular para organizar contactos, interpretar instrucciones sencillas, preparar mensajes y administrar tareas.

> Estado: MVP inicial. La integración de WhatsApp prepara enlaces oficiales `wa.me`; el usuario revisa el destinatario y pulsa enviar en WhatsApp. No automatiza WhatsApp Web, no extrae sesiones y no lee conversaciones privadas.

## Funciones incluidas

- Chat con un intérprete local básico de instrucciones en español.
- Agenda local de contactos (nombre y número).
- Preparación de borradores de WhatsApp con vista previa.
- Apertura de conversaciones mediante enlaces oficiales `https://wa.me/`.
- Tareas y recordatorios almacenados en SQLite.
- Historial local de operaciones.
- Registro centralizado de herramientas y validaciones.
- Interfaz web sencilla servida por Flask.

## Requisitos

- Python 3.10 o superior.
- pip.

## Ejecutar en Windows

1. Descarga o clona el repositorio.
2. Abre PowerShell en la carpeta del proyecto.
3. Crea y activa un entorno virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

4. Instala dependencias:

```powershell
py -m pip install -r requirements.txt
```

5. Copia `.env.example` a `.env` (opcional para la primera versión).
6. Inicia el servidor:

```powershell
py run.py
```

7. Abre http://127.0.0.1:5000

## Ejecutar en Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

## Primeros pasos

1. Entra en **Contactos** y agrega un nombre con su número internacional (por ejemplo, código de país + número, solo dígitos).
2. En el chat escribe: `prepara un mensaje para Ana diciendo que mañana llego a las 10`.
3. Revisa el borrador y el destinatario.
4. Pulsa **Abrir WhatsApp** y confirma/envía el mensaje desde WhatsApp.

También puedes escribir `crear tarea estudiar matemática` o administrar tareas desde la pestaña correspondiente.

## Configurar un proveedor de IA (opcional)

La aplicación incluye un intérprete local básico. Para usar un modelo externo compatible con la API de Chat Completions:

1. Copia `.env.example` a `.env`.
2. Completa `AI_BASE_URL` con la URL base del proveedor (por ejemplo, el endpoint base que termina en `/v1`).
3. Completa `AI_MODEL` con el identificador exacto del modelo.
4. Completa `AI_API_KEY` con la clave obtenida directamente del proveedor, si la requiere.
5. Reinicia la aplicación.

El proveedor debe ser compatible con el formato OpenAI Chat Completions. La disponibilidad gratuita, los límites y las condiciones dependen del proveedor; este proyecto no incluye claves ni garantiza una cuota gratuita. Se aceptan URLs HTTPS y endpoints locales en `localhost`. Nunca publiques tu archivo `.env`.

## Privacidad y seguridad

- La base SQLite se guarda en `data/wa_bridge.db` en el equipo donde corre el servidor.
- No introduzcas códigos de verificación, cookies, tokens de sesión ni contraseñas de WhatsApp.
- No se incluye automatización no oficial de WhatsApp Web.
- Los mensajes se abren para revisión; no se envían en segundo plano.
- No expongas el servidor en Internet sin añadir autenticación, HTTPS y controles de acceso.
- No subas `.env`, bases de datos, contactos ni claves al repositorio.

## Estructura

```text
backend/
  app.py
  agent.py
  database.py
  security.py
  whatsapp.py
  static/
    app.js
    style.css
  templates/
    index.html
tests/
  test_core.py
data/
run.py
requirements.txt
.env.example
.gitignore
```

## Próximas etapas

1. Conectar un proveedor de IA compatible y configurable, sin atar el proyecto a una sola marca.
2. Añadir autenticación local y perfiles/permisos.
3. Añadir importación de contactos con consentimiento.
4. Evaluar integraciones oficiales de WhatsApp que sean elegibles para el uso y la región de la cuenta.
5. Incorporar pruebas y empaquetado para ejecución local.

## Licencia

Aún no se ha definido una licencia. No asumas que el código puede redistribuirse hasta que se elija una.
