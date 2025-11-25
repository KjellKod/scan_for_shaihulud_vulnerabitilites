import os
import json
from pathlib import Path

ROOT = Path(".")
BAD_FILE = "bad-packages.txt"

# ------------------------------------------------------------------------------
# Load compromised packages list
# ------------------------------------------------------------------------------
def load_bad_packages():
    bad = {}
    with open(BAD_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or "=" not in line:
                continue

            name, versions = line.split("=", 1)
            name = name.strip()

            version_list = []
            for part in versions.split("||"):
                v = part.strip().lstrip("=")
                if v:
                    version_list.append(v)

            bad[name] = version_list
    return bad

BAD = load_bad_packages()

def is_bad(name, version):
    version = version.strip().lstrip("^~")
    return name in BAD and version in BAD[name]

# ------------------------------------------------------------------------------
# Print repo directories as they are visited
# ------------------------------------------------------------------------------
def list_repos():
    seen = set()
    for pkg in ROOT.rglob("package.json"):
        repo = pkg.parent
        seen.add(repo)

    for lock in ROOT.rglob("package-lock.json"):
        repo = lock.parent
        seen.add(repo)

    # sort for stable output
    return sorted(seen, key=lambda p: str(p))

# ------------------------------------------------------------------------------
# Scan package.json
# ------------------------------------------------------------------------------
def scan_package_json(path, results):
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        return

    for sec in ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]:
        for name, version in data.get(sec, {}).items():
            clean = version.lstrip("^~")
            if is_bad(name, clean):
                results.append(("package.json", path, name, version))

# ------------------------------------------------------------------------------
# Scan package-lock.json (supports npm v1 + v2+)
# ------------------------------------------------------------------------------
def scan_package_lock(path, results):
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        return

    # npm v2+ lockfile
    if "packages" in data:
        for key, meta in data["packages"].items():
            version = meta.get("version")
            if not version:
                continue
            name = os.path.basename(key) if key else data.get("name")
            if name and is_bad(name, version):
                results.append(("package-lock.json (v2)", path, name, version))
        return

    # npm v1 lockfile
    if "dependencies" in data:
        stack = list(data["dependencies"].items())
        while stack:
            name, meta = stack.pop()
            version = meta.get("version")
            if version and is_bad(name, version):
                results.append(("package-lock.json (v1)", path, name, version))
            nested = meta.get("dependencies")
            if isinstance(nested, dict):
                stack.extend(nested.items())

# ------------------------------------------------------------------------------
# Inventory mode
# ------------------------------------------------------------------------------
def inventory_all_packages():
    found = set()

    for path in ROOT.rglob("package.json"):
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            continue

        for sec in ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]:
            found.update(data.get(sec, {}).keys())

    for path in ROOT.rglob("package-lock.json"):
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            continue

        # v2+
        if "packages" in data:
            for key in data["packages"].keys():
                name = os.path.basename(key) if key else data.get("name")
                if name:
                    found.add(name)

        # v1
        if "dependencies" in data:
            stack = list(data["dependencies"].items())
            while stack:
                name, meta = stack.pop()
                found.add(name)
                nested = meta.get("dependencies")
                if isinstance(nested, dict):
                    stack.extend(nested.items())

    return sorted(found)

# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
def main():
    import sys

    # inventory mode
    if "--inventory" in sys.argv:
        for pkg in inventory_all_packages():
            print(pkg)
        return

    # standard scan with repo printing
    repos = list_repos()
    results = []

    for repo in repos:
        print(f"🔍 Checking repo: {repo}")
        pkg_json = repo / "package.json"
        pkg_lock = repo / "package-lock.json"

        if pkg_json.exists():
            scan_package_json(pkg_json, results)

        if pkg_lock.exists():
            scan_package_lock(pkg_lock, results)

    # output results
    if not results:
        print("\n✔ No compromised packages found.")
        return

    print("\n⚠️ COMPROMISED PACKAGES FOUND:\n")
    for kind, path, name, version in results:
        print(f"{kind} | {path} | {name}@{version}")

if __name__ == "__main__":
    main()
