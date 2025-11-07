import os
import sys
import subprocess
from pathlib import Path


def main():
    base_dir = Path(__file__).resolve().parent.parent
    src_path = base_dir / "src" / "voice_service.py"

    if not src_path.exists():
        print(f"[ERROR] voice_service.py not found: {src_path}", file=sys.stderr)
        sys.exit(1)

    # Optional config path via env var (for future extension)
    cfg_env = os.getenv("VOICE_SERVICE_CONFIG")
    cmd = [sys.executable, str(src_path)]
    if cfg_env:
        # If the service supports a --config parameter, append it.
        # This is safe even if the script ignores unknown args.
        cmd += ["--config", cfg_env]

    print(f"[INFO] Starting voice service: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Voice service exited with error code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()