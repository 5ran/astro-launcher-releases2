"""Publish Theo's complete snapshot with exact-build, validated corrections."""
import json
import pathlib
import re
import urllib.request

def select_snapshot(data, corrections, verified_versions, approved_dir):
    """Pinned approved full snapshots beat live upstream for the exact build."""
    version = data.get("Roblox Version", "")
    if not isinstance(version, str) or not re.fullmatch(r"version-[0-9a-f]{16,64}", version):
        raise ValueError("Invalid Roblox version")
    path = approved_dir / (version + ".json")
    if path.exists():
        approved = json.loads(path.read_text(encoding="utf-8"))
        if approved.get("Roblox Version") != version or version not in verified_versions:
            raise ValueError("Approved snapshot/build mismatch")
        if approved.get("Astro Verification") != {"Version": version, "Verified": True}:
            raise ValueError("Invalid approved snapshot status")
        # Validate shape without applying mutable corrections to approved bytes.
        corrected(approved, {}, verified_versions)
        return approved
    # Legacy approvals retain their established corrections. New unapproved
    # builds remain Theo-only and receive no ad-hoc merged fields.
    return corrected(data, corrections if version in verified_versions else {}, verified_versions)

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
            data = select_snapshot(json.loads(raw), corrections, verified_versions, ROOT / "offsets/approved")
            output = ROOT / "offsets/offsets.json"
            temporary = output.with_suffix(".tmp")
            temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            # Preserve the previous build before moving the latest pointer.
            # Already archived revisions must not be replaced by stale latest data.
            if output.exists():
                previous = json.loads(output.read_text(encoding="utf-8"))
                previous_version = previous.get("Roblox Version", "")
                if isinstance(previous_version, str) and re.fullmatch(r"version-[0-9a-f]{16,64}", previous_version):
                    archive = ROOT / "offsets/versions" / previous_version / "offsets.json"
                    archive.parent.mkdir(parents=True, exist_ok=True)
                    if not archive.exists():
                        archive.write_text(json.dumps(previous, indent=2) + "\n", encoding="utf-8")
            archive = ROOT / "offsets/versions" / data["Roblox Version"] / "offsets.json"
            archive.parent.mkdir(parents=True, exist_ok=True)
            archive_temp = archive.with_suffix(".tmp")
            archive_temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            archive_temp.replace(archive)
            temporary.replace(output)
            print("Validated snapshot:", data["Roblox Version"])
            return
        except Exception as error:
            errors.append(f"{url}: {error}")
    raise RuntimeError("No valid upstream snapshot; previous file preserved. " + "; ".join(errors))

if __name__ == "__main__":
    main()
