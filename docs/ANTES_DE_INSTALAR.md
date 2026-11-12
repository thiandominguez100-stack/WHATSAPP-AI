# Preparación e instalación en Windows

Esta guía corresponde al uso personal y local de WA-Bridge AI. No conectes el servidor a Internet ni lo publiques en una red.

## 1. Antes de instalar

- Windows 10 u 11.
- Python 3.10 o superior y el lanzador `py`.
- Git para clonar el repositorio.
- Ollama instalado.
- El modelo `qwen2.5:1.5b` ya descargado; el proyecto no lo descarga.
- Espacio libre para el entorno Python, dependencias y base de datos.

Comprueba Python y Git:

```powershell
py --version
git --version
```

Comprueba Ollama:

```powershell
ollama list
```

Debe aparecer `qwen2.5:1.5b`. Si Ollama no responde, abre la aplicación Ollama antes de continuar.

## 2. Clonar e instalar

```powershell
git clone https://github.com/thiandominguez100-stack/WHATSAPP-AI.git
cd WHATSAPP-AI
Set-ExecutionPolicy -Scope Process Bypass
.\setup_windows.ps1
```

El instalador crea `.venv`, instala las dependencias Python y copia `.env.example` a `.env` solo si todavía no existe. No descarga modelos y no reemplaza una configuración existente.

## 3. Diagnosticar el equipo

```powershell
.\doctor_windows.ps1
```

El diagnóstico comprueba Python, entorno virtual, configuración, Ollama, presencia del modelo y disponibilidad del puerto 5000. No cambia la configuración ni imprime secretos.

Si el puerto 5000 ya está ocupado, no cierres procesos al azar. Informa el mensaje de diagnóstico para identificar qué lo está usando.

## 4. Iniciar la aplicación

```powershell
.\run_windows.ps1
```

Mantén abierta esa ventana de PowerShell mientras uses la aplicación. Abre manualmente:

http://127.0.0.1:5000

Para detener el servidor, vuelve a PowerShell y pulsa `Ctrl+C`.

## 5. Comprobar funcionamiento

En otra ventana de PowerShell, dentro de la carpeta del proyecto:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

También puedes abrir `http://127.0.0.1:5000/api/health`; debe responder con `"ok": true`.

Prueba la interfaz con datos ficticios primero: agrega un contacto de prueba, crea una tarea y consulta el historial. No uses números de otras personas sin permiso.

## 6. Copia de seguridad

Cuando quieras respaldar la base local:

```powershell
.\backup_windows.ps1
```

El archivo se guarda en `backups`. Conserva las copias en un lugar privado: pueden contener nombres, números, tareas y borradores. No las subas a GitHub ni las compartas públicamente.

## Límites actuales

- La aplicación administra datos guardados localmente.
- Puede preparar un borrador y abrir un enlace oficial `wa.me` para revisión manual.
- No lee automáticamente chats ni contactos de WhatsApp.
- No envía mensajes en segundo plano.
- El historial registra acciones de la aplicación, no el historial completo de WhatsApp.
- La conexión real con WhatsApp no forma parte de las fases 1 a 5.
