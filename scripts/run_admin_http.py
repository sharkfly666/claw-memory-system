from pathlib import Path
import argparse

from claw_memory_system.admin_http import serve


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    serve(Path(args.workspace).expanduser(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
