"""Find _bergamot*.pyd and inject it into the wheel."""
import zipfile
import os
import sys
import glob

# Search broadly for .pyd in all common locations
pyd_files = []
for root, dirs, files in os.walk("."):
    # Skip .git
    if ".git" in root:
        continue
    for f in files:
        if "_bergamot" in f and f.endswith((".pyd", ".dll")):
            pyd_files.append(os.path.join(root, f))

# Debug: print all candidates
for p in pyd_files:
    print(f"  Candidate: {p} ({os.path.getsize(p)} bytes)")

# Prefer the real .pyd (larger = more likely the actual compiled extension)
pyd_path = None
if pyd_files:
    pyd_path = max(pyd_files, key=os.path.getsize)

if not pyd_path:
    print("NO_PYD_FOUND")
    sys.exit(0)

print(f"Using .pyd: {pyd_path} ({os.path.getsize(pyd_path)} bytes)")

# Find wheel
wheels = glob.glob("wheelhouse/*.whl")
if not wheels:
    print("NO_WHEEL_FOUND")
    sys.exit(1)

wheel_path = wheels[0]
tmp_path = wheel_path + ".tmp"
original_size = os.path.getsize(wheel_path)

# Check if .pyd is already in wheel
with zipfile.ZipFile(wheel_path, "r") as z:
    names = z.namelist()
    if any("_bergamot" in n for n in names):
        print(f"Wheel already contains _bergamot extension ({original_size} bytes)")
        for n in names:
            info = z.getinfo(n)
            print(f"  {n} ({info.file_size} bytes)")
        print("SUCCESS")
        sys.exit(0)

# Inject .pyd into wheel
with zipfile.ZipFile(wheel_path, "r") as zin:
    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            zout.writestr(item, zin.read(item))
        zout.write(pyd_path, "bergamot/_bergamot.pyd")

os.replace(tmp_path, wheel_path)
new_size = os.path.getsize(wheel_path)

# Verify
with zipfile.ZipFile(wheel_path, "r") as z:
    for n in z.namelist():
        info = z.getinfo(n)
        print(f"  {n} ({info.file_size} bytes)")
    if any("_bergamot" in n for n in z.namelist()):
        print(f"SUCCESS: .pyd injected! Wheel: {original_size} -> {new_size} bytes")
    else:
        print(f"FAIL: .pyd not injected. Size unchanged: {original_size} -> {new_size}")
