"""Typography-only print adaptation of the established plotting program.

No formulas, observations, curves or axis ranges change. The original outputs
remain untouched. Wider source panels need larger labels when set in A4 text.
"""
from pathlib import Path
import sys
import matplotlib.pyplot as plt
from matplotlib.text import Text

PAPER=Path(__file__).resolve().parent
sys.path.insert(0,str(PAPER.parent))
from experiments import make_figures as plots
from build_assets import FIGURES


def main():
    plots.FIG=PAPER/'figures'
    source_save=plots.save
    def print_save(fig,name,caption,catalog):
        if name not in FIGURES:
            plt.close(fig)
            return
        minimum=15 if name=='01_accessibility' else 13
        for text in fig.findobj(match=Text):
            text.set_fontsize(max(minimum,1.4*text.get_fontsize()))
        width,height=fig.get_size_inches()
        fig.set_size_inches(width,height*1.03)
        source_save(fig,name,caption,catalog)
    plots.save=print_save
    plots.main()


if __name__=='__main__':
    main()
