# whisperMe Project-Scoped Rules

This rules file enforces critical architecture, layout, and packaging constraints for whisperMe. All development agents must adhere to these policies.

## 1. Release Packaging & Dependency Downsizing (Volume Limit)
- **CPU-Only PyTorch Constraint**: When packaging releases (via `scripts/build_release.py` or similar workflow builds), always force CPU-only PyTorch installation by appending `--extra-index-url https://download.pytorch.org/whl/cpu` to the `pip install` command.
  - **Reason**: Standard PyPI PyTorch wheels on Windows include CUDA support and exceed 2.6 GB, which chokes CI/CD runners (like GitHub Actions), causes OOM (Out Of Memory) aborts, and results in bloated, unusable release ZIP files. CPU-only PyTorch is only ~150 MB and fits release packaging standards.
- **Pruning Logic**: Retain post-install folder cleanups for `torch/include`, `torch/test`, and `.lib` symbols inside the temporary dependencies folder before archiving.

## 2. Startup Launcher Shell Scripts (start.sh & start.bat)
- **File Integrity**: The repository root must always retain the native CLI startup executors:
  - `start.bat` (Windows launcher)
  - `start.sh` (Unix/Linux/macOS launcher)
- **App Launcher Fallbacks**: The GUI-based shortcut generators (`whisperMe.lnk` and `whisperMe.app`) are dynamic wrapper overlays and must NEVER result in the deletion of `start.sh` or `start.bat` from the source repository.
- **Relocation Safety**: Launcher scripts must dynamically compute their working directory relative to their parent file paths (`%~dp0` in bat, `dirname` in bash) to handle path changes gracefully.

## 3. Configuration & Databases Preservation
- **Upgrade Exclusions**: When implementing self-upgraders or copy-overwriters, always preserve configuration data (`config.json`), summaries templates (`prompt.json`), local recordings database (`data/`), podcast downloads (`downloads/`), and runs output (`logs/`).