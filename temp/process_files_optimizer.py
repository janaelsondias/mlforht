import os
import pandas as pd
from collections import Counter

root_dir = "/mnt/c/Users/deinf.janaelson/Documents/Datasets/Extracted"

def get_csv_files(root_dir):
    return [os.path.join(root_dir, f)
            for f in os.listdir(root_dir)
            if f.lower().endswith(".csv")]

files = get_csv_files(root_dir)

contador = Counter()

for file in files:
    print(f"Processando: {file}")

    for chunk in pd.read_csv(file, sep=";", encoding="utf-8", chunksize=100000):
        # garante que a coluna existe
        if 'violacao' in chunk.columns:
            valores = chunk['violacao'].dropna()
            contador.update(valores)

# transformar em DataFrame
resultado = (
    pd.DataFrame(contador.items(), columns=["violacao", "quantidade"])
    .sort_values(by="quantidade", ascending=False)
)

print(resultado.head(20))