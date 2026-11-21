"""Export source + built UI, excluding secrets, imported data and environments."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
target = root / ".runtime" / "DevDiagnose-v0.1.0.zip"
target.parent.mkdir(exist_ok=True)
files = [root / name for name in (
    "README.md", ".gitignore", ".gitattributes", ".env.example",
    "environment.yml", "pyproject.toml", "requirements.lock.txt",
    ".vscode/settings.json", "frontend/package.json", "frontend/package-lock.json",
    "frontend/index.html", "frontend/tsconfig.json", "frontend/vite.config.ts",
    "frontend/playwright.config.ts",
)]
for directory in ("backend/devdiagnose", "frontend/src", "frontend/tests", "frontend/dist", "tests", "scripts", "docs"):
    files.extend(p for p in (root / directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo"})
with ZipFile(target, "w", ZIP_DEFLATED) as archive:
    for path in sorted(set(files)):
        archive.write(path, "DevDiagnose/" + path.relative_to(root).as_posix())
print(f"{target} ({target.stat().st_size} bytes)")
