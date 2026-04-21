import argparse
from pathlib import Path

from 1nextgen2026_coding_bootcamp.config import compose_config
from nextgen2026_coding_bootcamp.steps.analyze import run_analyze


def main() -> int:
    parser = argparse.ArgumentParser(description="Run analyze stage")
    parser.add_argument("--config", type=Path, default=Path("configs/stages/analyze.yaml"))
    parser.add_argument("--set", nargs="*", default=[], metavar="KEY=VALUE")
    args = parser.parse_args()

    config_root = Path("configs")
    stage_part = str(args.config.relative_to(config_root))
    parts = ["run.yaml", "paths.yaml", stage_part, "profiles/base.yaml"]

    cfg = compose_config(config_root=config_root, parts=parts, overrides=args.set)
    run_analyze(cfg=cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())