import os
import gc
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import logging
logging.basicConfig(level=logging.INFO)

root_dir = "/mnt/c/Users/deinf.janaelson/Documents/Datasets/"
output_dir = "/mnt/c/Users/deinf.janaelson/Documents/Datasets/Extracted"

Path(output_dir).mkdir(parents=True, exist_ok=True)


# ✅ normalização de colunas
def normalizar_colunas(columns):
    import re, unicodedata

    def normalize(col):
        col = col.strip()
        col = unicodedata.normalize('NFKD', col)
        col = ''.join(c for c in col if not unicodedata.combining(c))
        col = re.sub(r'[()\?\\/\-]', '_', col)
        col = re.sub(r'\s+', '_', col)
        col = re.sub(r'_+', '_', col)
        col = re.sub(r'[^a-zA-Z0-9]+$', '', col)
        return col.lower()

    return [normalize(c) for c in columns]

def corrigir_colunas_antes_normalizar(columns):
    novas = []

    for col in columns:
        c = col.strip().lower()

        if c == "(nenhum nome de coluna)":
            novas.append("grupo_vulneravel")
        elif c == "sexo_do_suspeito":
            novas.append("genero_do_suspeito")
        elif c in ["sexo_da_vitima", "sexo_da_vítima"]:
            novas.append("genero_da_vitima")
        else:
            novas.append(col)

    return novas
    
# ✅ processamento
def process_file(file_path):
    file_name = os.path.basename(file_path)
    output_path = os.path.join(output_dir, file_name)

    first_chunk = True

    for chunk in pd.read_csv(
        file_path,
        sep=";",
        encoding="utf-8",
        chunksize=100000,
        dtype=str,
    ):
        chunk.columns = corrigir_colunas_antes_normalizar(chunk.columns)

        # normalizar schema
        chunk.columns = normalizar_colunas(chunk.columns)

        if "violacao" not in chunk.columns:
            return f"ERRO: coluna violacao não encontrada em {file_name}"

        # filtro
        filtro = chunk["violacao"].str.contains(
            "trafico|tráfico",
            case=False,
            na=False,
            regex=True
        )

        filtrado = chunk.loc[filtro]

        if not filtrado.empty:
            filtrado.to_csv(
                output_path,
                mode="w" if first_chunk else "a",
                index=False,
                header=first_chunk,
                sep=";"
            )
            first_chunk = False

        del chunk
        del filtrado
        # gc.collect()
    logging.info(f"Processado: {file_name}")
    return f"OK: {file_name}"


# ✅ execução paralela
files = [
    os.path.join(root_dir, f)
    for f in os.listdir(root_dir)
    if f.endswith(".csv")
]

with ThreadPoolExecutor(max_workers=2) as executor:
    list(tqdm(executor.map(process_file, files), total=len(files)))