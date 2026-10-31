"""Safe replacement entry point; see scripts/collect_performance.py and README.

The former script disabled TLS, accepted fuzzy matches and zero-filled failures.
This wrapper requires an explicit season and output and preserves missing values.
"""
from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    script = Path(__file__).resolve().parents[1] / 'scripts/collect_performance.py'
    raise SystemExit(subprocess.call([sys.executable, str(script), '--sport', 'football', *sys.argv[1:]]))
