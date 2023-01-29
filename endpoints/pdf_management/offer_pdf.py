import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


data = [
    [1, 'denumire1', 'cant1', 'pret1', 'valoare1'],
    [2, 'denumire2', 'cant2', 'pret2', 'valoare2'],
    [3, 'denumire3', 'cant3', 'pret3', 'valoare3'],
    [4, 'denumire4', 'cant4', 'pret4', 'valoare4'],
]
df = pd.DataFrame(np.random.random((10, 3)), columns=("νικος", "col 2", "col 3"))

fig, ax = plt.subplots(figsize=(12, 14))
ax.axis('tight')
ax.axis('off')
the_table = ax.table(cellText=df.values, colLabels=df.columns, loc='center')

pp = PdfPages("./foo.pdf")
pp.savefig(fig, bbox_inches='tight')
pp.close()

# borb.pdf
