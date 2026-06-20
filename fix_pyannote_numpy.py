"""
Batch fix: Replace np.NaN and np.NAN with np.nan in pyannote source files
for NumPy 2.0 compatibility
"""
import os
import re

base_dir = r"E:\Projects\whisperMe\venv\Lib\site-packages\pyannote"

fixed_files = []
total_replacements = 0

for root, dirs, files in os.walk(base_dir):
    for fname in files:
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue
        
        # Replace np.NaN and np.NAN with np.nan
        # But NOT np.nan_to_num, np.nanmin, np.nanmax, np.nanmean etc.
        new_content = content
        
        # Replace np.NaN (exactly, not followed by lowercase letter)
        # np.NaN -> np.nan  (but not np.NaN_something)
        count1 = len(re.findall(r'np\.NaN\b', new_content))
        new_content = re.sub(r'np\.NaN\b', 'np.nan', new_content)
        
        # Replace np.NAN (exactly, not followed by lowercase letter)
        # np.NAN -> np.nan  (but not np.NAN_something)
        count2 = len(re.findall(r'np\.NAN\b', new_content))
        new_content = re.sub(r'np\.NAN\b', 'np.nan', new_content)
        
        replacements = count1 + count2
        if replacements > 0:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(new_content)
            rel_path = os.path.relpath(fpath, base_dir)
            fixed_files.append((rel_path, count1, count2))
            total_replacements += replacements
            print(f"  Fixed: {rel_path} ({count1} NaN + {count2} NAN = {replacements} replacements)")

print(f"\n{'='*50}")
print(f"Total: {len(fixed_files)} files fixed, {total_replacements} replacements made")

# Verify by trying to import
print(f"\n{'='*50}")
print("Verifying import after fix...")
try:
    # Force reimport
    import importlib
    import pyannote.audio.core.inference
    importlib.reload(pyannote.audio.core.inference)
    print("SUCCESS: pyannote.audio.core.inference imported successfully!")
except Exception as e:
    print(f"STILL BROKEN: {e}")
