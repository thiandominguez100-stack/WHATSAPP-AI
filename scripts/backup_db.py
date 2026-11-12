"""Create a consistent local SQLite backup using the SQLite backup API."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def configured_database() -> Path:
    configured = os.getenv("WA_BRIDGE_DB", "").strip()
    env_file = ROOT / ".env"
    if not configured and env_file.exists():
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line.startswith("WA_BRIDGE_DB="):
                configured = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    path = Path(configured or "data/wa_bridge.db")
    return path if path.is_absolute() else ROOT / path


def main() -> int:
    source = configured_database()
    if not source.is_file():
        print(f"No existe la base de datos todavía: {source}")
        print("Inicia la aplicación y vuelve a ejecutar el respaldo.")
        return 1

    backup_dir = ROOT / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = backup_dir / f"wa_bridge_{stamp}.db"

    try:
        with sqlite3.connect(source, timeout=10) as src:
            with sqlite3.connect(destination) as dst:
                src.backup(dst)
                check = dst.execute("PRAGMA integrity_check").fetchone()
                if not check or check[0] != "ok":
                    raise RuntimeError("La comprobación de integridad de la copia falló.")
        print(f"Copia de seguridad creada: {destination}")
        print(f"Tamaño: {destination.stat().st_size:,} bytes")
        return 0
    except (OSError, sqlite3.Error, RuntimeError) as exc:
        destination.unlink(missing_ok=True)
        print(f"Error al crear la copia: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
