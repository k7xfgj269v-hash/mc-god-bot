#!/usr/bin/env python3
"""Compute the full client library classpath (relative paths) for Forge 1.20.1-47.3.22
on macOS arm64, exactly like the official launcher does (version json + inherited json + rules)."""
import json, os, sys

GAME = os.path.expanduser("~/Library/Application Support/minecraft")
CUR_OS = {"name": "osx", "arch": "aarch64", "version": "26.6.1"}
FEATURES = {"is_demo_user": False, "has_custom_resolution": False}

def rules_allow(rules):
    if not rules:
        return True
    allowed = False
    for r in rules:
        if "os" in r:
            osr = r["os"]
            if "name" in osr and osr["name"] != CUR_OS["name"]:
                continue
            if "arch" in osr and osr["arch"] != CUR_OS["arch"]:
                continue
            if "version" in osr and not CUR_OS["version"].startswith(osr["version"]):
                continue
        if "features" in r:
            ok = all(FEATURES.get(k) == v for k, v in r["features"].items())
            if not ok:
                continue
        return r["action"] == "allow"
    return allowed

def maven_path(name):
    parts = name.split(":")
    group, art, ver = parts[0].replace(".", "/"), parts[1], parts[2]
    cls = parts[3] if len(parts) > 3 else ""
    fn = f"{art}-{ver}" + (f"-{cls}" if cls else "") + ".jar"
    return os.path.join("libraries", group, art, ver, fn)

libs = []
for vj in ("1.20.1-forge-47.3.22/1.20.1-forge-47.3.22.json", "1.20.1/1.20.1.json"):
    p = os.path.join(GAME, "versions", vj)
    d = json.load(open(p))
    for l in d.get("libraries", []):
        if rules_allow(l.get("rules")):
            libs.append(maven_path(l["name"]))

seen, out = set(), []
for x in libs:
    if x not in seen:
        seen.add(x)
        out.append(x)
for x in out:
    if not os.path.exists(os.path.join(GAME, x)):
        print("MISSING: " + x, file=sys.stderr)
print(":".join(out))
