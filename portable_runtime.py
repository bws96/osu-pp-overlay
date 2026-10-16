"""Per-process portable runtimes, independent of the host PATH."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
NODE=str(ROOT/'runtime'/'node'/'node.exe')
