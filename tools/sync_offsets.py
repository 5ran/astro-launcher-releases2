"""Publish Theo's complete snapshot with exact-build, validated corrections."""
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCES = ("https://offsets.imtheo.lol/offsets.json", "https://offsets.femboythighs.org/offsets.json")

def corrected(data, corrections, verified_versions=()):
    version = data.get("Roblox Version", "")
    if not isinstance(version, str) or not re.fullmatch(r"version-[0-9a-f]{16,64}", version):
        raise ValueError("Invalid Roblox version")
    offsets = data.get("Offsets")
    if not isinstance(offsets, dict) or any(not isinstance(v, dict) for v in offsets.values()):
        raise ValueError("Invalid offset groups")
    values = [v for group in offsets.values() for v in group.values()]
    if len(values) < 300 or any(type(v) is not int or v < 0 or v > 2**64-1 for v in values):
        raise ValueError("Incomplete or invalid offset snapshot")
    for key, value in corrections.get(version, {}).items():
        group, name = key.split(".", 1)
        if type(value) is not int or value <= 0 or value > 65536 or group not in offsets:
            raise ValueError("Invalid correction")
        offsets[group][name] = value
    data["Astro Verification"] = {"Version": version, "Verified": version in verified_versions}
    return data

def main():
    corrections = json.loads((ROOT / "offsets/corrections.json").read_text())
    verified_versions = json.loads((ROOT / "offsets/verified-builds.json").read_text())
    errors = []
    for url in SOURCES:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Astro-Offsets-Sync/1.0", "Cache-Control": "no-cache"})
            with urllib.request.urlopen(request, timeout=40) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ValueError("Oversized response")
            data = corrected(json.loads(raw), corrections, verified_versions)
            output = ROOT / "offsets/offsets.json"
            temporary = output.with_suffix(".tmp")
            temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            temporary.replace(output)
            print("Validated snapshot:", data["Roblox Version"])
            return
        except Exception as error:
            errors.append(f"{url}: {error}")
    raise RuntimeError("No valid upstream snapshot; previous file preserved. " + "; ".join(errors))

if __name__ == "__main__":
    main()
