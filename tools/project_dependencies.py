#!/usr/bin/env python3
"""Consolida as dependências game-specific em tools/vendor/<nome>.

Fontes externas (SOMENTE LEITURA — nunca modificadas, movidas ou apagadas):
  C:\\Projetos\\DKC2-disasm        -> tools/vendor/DKC2-disasm
  C:\\Projetos\\DKC2Recomp         -> tools/vendor/DKC2Recomp
  C:\\Projetos\\SNES-ROM-Framework -> tools/vendor/SNES-ROM-Framework

Regras da cópia segura:
  - copia assets, sources, tests e docs (árvore completa da fonte);
  - exclui .git/, build*/ (build, build-present, build-release), venv/ e caches;
  - idempotente: destino já presente com mesmo tamanho + mesmo hash é pulado;
  - nunca apaga nada em tools/vendor (somente cria/atualiza arquivos);
  - registra o resultado em tools/vendor/<nome>-manifest.json (path, hash, size).

Fora de escopo (não sincronizado por este script): tools/vendor/defold-mcp —
clone do servidor MCP do Defold, mantido à parte.

Uso:
  python tools/project_dependencies.py               # sincroniza as 3 fontes
  python tools/project_dependencies.py DKC2Recomp    # sincroniza só uma
"""

import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from safe_copy import get_file_hash  # noqa: E402  (reuso do utilitário do repo)

ROOT = Path(__file__).resolve().parent.parent
VENDOR_DIR = ROOT / "tools" / "vendor"

SOURCES = {
    "DKC2-disasm": Path(r"C:\Projetos\DKC2-disasm"),
    "DKC2Recomp": Path(r"C:\Projetos\DKC2Recomp"),
    "SNES-ROM-Framework": Path(r"C:\Projetos\SNES-ROM-Framework"),
}

# .git / venv / caches (excluídos por nome exato)
EXCLUDE_DIRS = {
    ".git", ".hg", ".svn",
    "venv", ".venv",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".cache",
    "node_modules", ".tox",
}
# artefatos de build (nome "build" ou prefixo "build-": build-present, build-release)
EXCLUDE_FILE_SUFFIXES = (".pyc", ".pyo")  # bytecode = cache


def dir_excluded(name: str) -> bool:
    return name in EXCLUDE_DIRS or name == "build" or name.startswith("build-")


def sync_source(name: str, src: Path) -> tuple[int, int, Path]:
    """Copia src -> tools/vendor/<name>. Retorna (copiados, pulados, manifest)."""
    if not src.is_dir():
        raise FileNotFoundError(f"fonte ausente: {src}")

    dst_root = VENDOR_DIR / name
    dst_root.mkdir(parents=True, exist_ok=True)

    copied = skipped = 0
    for cur, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs if not dir_excluded(d))
        for fname in sorted(files):
            if fname.endswith(EXCLUDE_FILE_SUFFIXES):
                continue
            src_file = Path(cur) / fname
            rel = src_file.relative_to(src)
            dst_file = dst_root / rel

            if dst_file.is_file() and dst_file.stat().st_size == src_file.stat().st_size:
                if get_file_hash(str(dst_file)) == get_file_hash(str(src_file)):
                    skipped += 1  # idempotente: arquivo igual não é regravado
                    continue

            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)  # só cria/atualiza; nunca deleta
            copied += 1

    # manifest = snapshot do destino (path, hash, size) — fonte do registro copy/hash
    entries = []
    for cur, dirs, files in os.walk(dst_root):
        dirs[:] = sorted(dirs)
        for fname in sorted(files):
            f = Path(cur) / fname
            entries.append({
                "path": str(f.relative_to(dst_root)).replace("/", "\\"),
                "hash": get_file_hash(str(f)),
                "size": f.stat().st_size,
            })

    manifest = VENDOR_DIR / f"{name}-manifest.json"
    manifest.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    return copied, skipped, manifest


def main(argv: list[str]) -> int:
    names = argv or list(SOURCES)
    unknown = [n for n in names if n not in SOURCES]
    if unknown:
        print(f"fonte desconhecida: {unknown}; opções: {list(SOURCES)}")
        return 2

    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    failed = 0
    for name in names:
        try:
            copied, skipped, manifest = sync_source(name, SOURCES[name])
        except FileNotFoundError as exc:
            print(f"[FALHA] {name}: {exc}")
            failed += 1
            continue
        print(f"[OK] {name}: copiados={copied} pulados={skipped} manifest={manifest.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
