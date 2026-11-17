"""Build the anonymous manuscript without relying on platform-specific BibTeX paths."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys

from verify_paper import verify

PAPER = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-assets', action='store_true')
    parser.add_argument('--update-pdf', action='store_true')
    args = parser.parse_args()
    if args.refresh_assets:
        subprocess.run([sys.executable, 'build_assets.py'], cwd=PAPER, check=True)
    output = PAPER / 'build'
    output.mkdir(exist_ok=True)
    # Run native BibTeX from the source directory. MSYS Perl can translate
    # latexmk's absolute BIBINPUTS into paths a native TeX binary cannot read.
    subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error',
                    '-output-directory=build', 'main.tex'], cwd=PAPER, check=True)
    environment = os.environ.copy()
    environment['BIBINPUTS'] = str(PAPER) + os.pathsep + environment.get('BIBINPUTS', '')
    subprocess.run(['bibtex', 'build/main'], cwd=PAPER, env=environment, check=True)
    subprocess.run(['latexmk', '-xelatex', '-bibtex-', '-interaction=nonstopmode',
                    '-halt-on-error', '-outdir=build', 'main.tex'], cwd=PAPER, check=True)
    result = verify(output / 'main.pdf', output / 'main.log')
    if args.update_pdf:
        shutil.copyfile(output / 'main.pdf', PAPER / 'manuscript.pdf')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
