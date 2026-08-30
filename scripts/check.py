"""Run the complete local release gate."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile
from pathlib import Path

from shimstacker import __version__

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
EXAMPLES = ROOT / "src" / "shimstacker" / "examples"
ARTIFACTS = ("report.json", "pick-list.csv", "bench-sheet.md", "report.html")
EXPECTED_DEMO_JOBS = 3


def run(arguments: list[str], *, expected: int = 0, cwd: Path = ROOT) -> None:
    """Run one gate command and require its documented exit code."""
    completed = subprocess.run(arguments, cwd=cwd, check=False)  # noqa: S603
    if completed.returncode != expected:
        command = subprocess.list2cmdline(arguments)
        raise RuntimeError(
            f"command returned {completed.returncode}, expected {expected}: {command}"
        )


def python_module(*arguments: str) -> list[str]:
    """Build a command using the active interpreter."""
    return [sys.executable, "-m", *arguments]


def compare_bundles(first: Path, second: Path) -> None:
    """Require every documented report to be byte deterministic."""
    for name in ARTIFACTS:
        if (first / name).read_bytes() != (second / name).read_bytes():
            raise RuntimeError(f"nondeterministic report artifact: {name}")


def create_examples_archive(target: Path) -> None:
    """Create a deterministic archive of the authored example plans."""
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sorted(EXAMPLES.glob("*.json")):
            info = zipfile.ZipInfo(f"examples/{source.name}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())


def inspect_packages(wheel: Path, source_archive: Path) -> None:
    """Check package contents and reject local-state leakage."""
    with zipfile.ZipFile(wheel) as archive:
        wheel_names = set(archive.namelist())
    with tarfile.open(source_archive, "r:gz") as archive:
        source_names = {member.name for member in archive.getmembers()}

    required_wheel = {
        "shimstacker/examples/feasible-shop.json",
        "shimstacker/examples/shared-stock-conflict.json",
        "shimstacker/py.typed",
    }
    if not required_wheel <= wheel_names:
        raise RuntimeError(f"wheel is missing: {sorted(required_wheel - wheel_names)}")
    if not any(name.endswith("/docs/SPEC.md") for name in source_names):
        raise RuntimeError("source archive is missing docs/SPEC.md")

    forbidden = ("/.git/", "__pycache__", ".pyc", ".coverage", ".env", ".uv-cache")
    leaked = sorted(
        name for name in wheel_names | source_names if any(x in name for x in forbidden)
    )
    if leaked:
        raise RuntimeError(f"package contains local state: {leaked[:5]}")


def isolated_smoke(wheel: Path, workspace: Path) -> None:
    """Install the wheel without the source tree and run the packaged demo."""
    environment = workspace / "wheel-env"
    venv.EnvBuilder(with_pip=True).create(environment)
    executable = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    run([str(executable), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)])
    run([str(executable), "-m", "shimstacker", "--version"])
    output = workspace / "installed-demo"
    run([str(executable), "-m", "shimstacker", "demo", "--output", str(output)])
    payload = json.loads((output / "report.json").read_text(encoding="utf-8"))
    if payload["status"] != "feasible" or len(payload["allocations"]) != EXPECTED_DEMO_JOBS:
        raise RuntimeError("installed demo did not reproduce the expected feasible allocation")


def main() -> int:
    """Run quality, behavior, package, and clean-install checks."""
    run(python_module("ruff", "format", "--check", "src", "tests", "scripts"))
    run(python_module("ruff", "check", "src", "tests", "scripts"))
    run(python_module("mypy", "src"))
    run(python_module("coverage", "erase"))
    run(python_module("coverage", "run", "--branch", "-m", "pytest", "-q"))
    run(python_module("coverage", "report"))

    with tempfile.TemporaryDirectory(prefix=".gate-", dir=ROOT) as directory:
        workspace = Path(directory)
        feasible = EXAMPLES / "feasible-shop.json"
        conflict = EXAMPLES / "shared-stock-conflict.json"
        run(python_module("shimstacker", "validate", str(feasible)))
        run(
            python_module(
                "shimstacker", "plan", str(feasible), "--output", str(workspace / "first")
            )
        )
        run(
            python_module(
                "shimstacker", "plan", str(feasible), "--output", str(workspace / "second")
            )
        )
        compare_bundles(workspace / "first", workspace / "second")
        run(
            python_module(
                "shimstacker", "plan", str(conflict), "--output", str(workspace / "conflict")
            ),
            expected=1,
        )

        if DIST.exists():
            shutil.rmtree(DIST)
        run(python_module("build", "--no-isolation"))
        wheels = list(DIST.glob("*.whl"))
        source_archives = list(DIST.glob("*.tar.gz"))
        if len(wheels) != 1 or len(source_archives) != 1:
            raise RuntimeError("build must produce exactly one wheel and one source archive")
        inspect_packages(wheels[0], source_archives[0])
        create_examples_archive(DIST / f"shimstacker-examples-v{__version__}.zip")
        isolated_smoke(wheels[0], workspace)

    print("SHIMSTACKER_RELEASE_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
