"""Create a deterministic SHA-256 inventory for the project hub."""

from hashlib import sha256
from json import dumps
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "inventory" / "files.json"
EXCLUDED_PARTS = {".git", ".venv", "venv", "__pycache__"}


def hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


records = []
for path in sorted(ROOT.rglob("*")):
    relative = path.relative_to(ROOT)
    if not path.is_file() or any(part in EXCLUDED_PARTS for part in relative.parts):
        continue
    if relative == OUTPUT.relative_to(ROOT):
        continue
    records.append(
        {
            "path": relative.as_posix(),
            "bytes": path.stat().st_size,
            "sha256": hash_file(path),
        }
    )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(dumps({"files": records}, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {len(records)} records to {OUTPUT}")
