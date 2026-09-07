"""Build, deploy to the fixed production address, and verify the served files."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
PROJECT = "investment-spring"
SCOPE = "skt-ir"
PRODUCTION = "https://investment-spring.vercel.app"
CLI = "vercel@59.11.7"
VERIFY_ATTEMPTS = 6
VERIFY_DELAY_SECONDS = 2


def read_remote(relative):
    request = Request(PRODUCTION + "/" + quote(relative) + "?verify=" + str(time.time_ns()),
                      headers={"Cache-Control": "no-cache"})
    with urlopen(request, timeout=45) as response:
        return response.read()


def verify_file(path):
    """Production alias의 엣지 전파가 끝날 때까지 같은 파일만 재검증한다."""
    relative = path.relative_to(ROOT / "dist").as_posix()
    expected = hashlib.sha256(path.read_bytes()).digest()
    last_error = None
    for attempt in range(1, VERIFY_ATTEMPTS + 1):
        try:
            remote = read_remote(relative)
            if hashlib.sha256(remote).digest() == expected:
                return
            last_error = "served bytes differ"
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < VERIFY_ATTEMPTS:
            delay = VERIFY_DELAY_SECONDS * attempt
            print(f"Waiting {delay}s for production alias: {relative} ({last_error})", flush=True)
            time.sleep(delay)
    raise RuntimeError(
        f"Production differs from local build after {VERIFY_ATTEMPTS} attempts: {relative} ({last_error})"
    )


def verify_root():
    expected = (ROOT / "dist" / "index.html").read_bytes()
    last_error = None
    for attempt in range(1, VERIFY_ATTEMPTS + 1):
        try:
            request = Request(PRODUCTION + "/?verify=" + str(time.time_ns()), headers={"Cache-Control": "no-cache"})
            with urlopen(request, timeout=45) as response:
                if response.read() == expected:
                    return
            last_error = "served bytes differ"
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < VERIFY_ATTEMPTS:
            delay = VERIFY_DELAY_SECONDS * attempt
            print(f"Waiting {delay}s for production root ({last_error})", flush=True)
            time.sleep(delay)
    raise RuntimeError(f"Production root does not serve the current portal after {VERIFY_ATTEMPTS} attempts: {last_error}")


def verify():
    portal_path = ROOT / "dist" / "portal-data.js"
    files = sorted((ROOT / "dist").glob("*.html")) + [portal_path]
    files.extend(sorted((ROOT / "dist" / "index-radar-data").rglob("*.json")))
    snapshot = json.loads(portal_path.read_text(encoding="utf-8").split("=", 1)[1].rstrip(";\n"))
    for case in snapshot["data"]["cases"]:
        if not (ROOT / "dist" / case["dashboard_href"]).is_file():
            raise RuntimeError(f"Missing case page: {case['dashboard_href']}")
    for path in files:
        verify_file(path)
    verify_root()
    print(f"Verified {len(files)} files + root; {len(snapshot['data']['cases'])} cases; "
          f"revision {snapshot['revision']}", flush=True)
    print(PRODUCTION, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify()
        return
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_all.py")], cwd=ROOT, check=True)
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if not npx:
        raise RuntimeError("Node.js/npx is required for Vercel deployment")
    link = ROOT / ".vercel" / "project.json"
    if not link.exists():
        subprocess.run([npx, "--yes", CLI, "link", "--yes", "--project", PROJECT,
                        "--scope", SCOPE], cwd=ROOT, check=True)
    linked = json.loads(link.read_text(encoding="utf-8"))
    if linked.get("projectName") != PROJECT:
        raise RuntimeError("Unexpected linked Vercel project; deployment stopped")
    subprocess.run([npx, "--yes", CLI, "deploy", "--prod", "--yes", "--scope", SCOPE],
                   cwd=ROOT, check=True)
    verify()


if __name__ == "__main__":
    main()
