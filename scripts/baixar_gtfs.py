"""Baixa um instantâneo GTFS da PBH para dados/brutos/ e registra a origem.

Uso: python3 scripts/baixar_gtfs.py [--destino dados/brutos/bhtrans.zip]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path

URL = (
    "https://ckan.pbh.gov.br/dataset/77764a7e-63fc-4111-ace3-fb7d3037953a/"
    "resource/f0fa78dc-74c3-49fa-8971-c310a76a07fa/download/gtfsfiles.zip"
)


def baixar(destino: Path, url: str = URL) -> dict[str, str | int]:
    """Salva ZIP e JSON com fonte, data, tamanho e SHA-256."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(".part")
    digest = hashlib.sha256()
    tamanho = 0
    try:
        subprocess.run(
            ["curl", "--fail", "--location", "--silent", "--show-error", "--retry", "2",
             "--max-time", "120", "--output", str(temporario), url],
            check=True,
        )
        with temporario.open("rb") as entrada:
            while bloco := entrada.read(1024 * 1024):
                digest.update(bloco)
                tamanho += len(bloco)
        if not zipfile.is_zipfile(temporario):
            raise ValueError("download não é um ZIP GTFS")
        temporario.replace(destino)
    finally:
        temporario.unlink(missing_ok=True)
    registro: dict[str, str | int] = {
        "url": url,
        "baixado_em_utc": datetime.now(UTC).isoformat(),
        "sha256": digest.hexdigest(),
        "bytes": tamanho,
    }
    destino.with_suffix(".json").write_text(
        json.dumps(registro, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return registro


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, default=Path("dados/brutos/bhtrans.zip"))
    args = parser.parse_args()
    print(json.dumps(baixar(args.destino), indent=2, ensure_ascii=False))
