import os
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import logging
logging.basicConfig(level=logging.INFO)

# Diretório com arquivos CSV e diretório de saída
root_dir = "/mnt/c/Users/deinf.janaelson/Documents/Datasets/"
output_dir = "./data"

Path(output_dir).mkdir(parents=True, exist_ok=True)

# Normalização de colunas
def normalize_columns(columns):
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

# Correção de nome de colunas específicas (para evitar problemas de normalização) e.g. "(Nenhum nome de coluna)" -> "grupo_vulneravel"
def rename_columns(columns):
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
    
# Processamento de arquivo em chunks
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
        chunk.columns = rename_columns(chunk.columns)

        # normalizar schema
        chunk.columns = normalize_columns(chunk.columns)

        if "violacao" not in chunk.columns:
            return f"ERRO: coluna violacao não encontrada em {file_name}"

        # filtro
        violation_filter = chunk["violacao"].str.contains(
            "trafico|tráfico",
            case=False,
            na=False,
            regex=True
        )

        df_filtered = chunk.loc[violation_filter]

        if not df_filtered.empty:
            df_filtered.to_csv(
                output_path,
                mode="w" if first_chunk else "a",
                index=False,
                header=first_chunk,
                sep=";"
            )
            first_chunk = False

        del chunk
        del df_filtered
    # logging.info(f"Processado: {file_name}")
    return f"OK: {file_name}"

def get_csv_files(root_dir):
    csv_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if f.lower().endswith('.csv'):
                csv_files.append(os.path.join(dirpath, f))
    return csv_files

def init_process_files():
    files = get_csv_files(root_dir)
    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(tqdm(executor.map(process_file, files), total=len(files)))

    return resultados

# init_process_files()

