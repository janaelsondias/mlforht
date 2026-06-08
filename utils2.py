import os
import re
import unicodedata
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)

def normalize_columns(columns):
    def normalize(col):
        col = str(col).strip()
        col = unicodedata.normalize("NFKD", col)
        col = "".join(c for c in col if not unicodedata.combining(c))
        col = re.sub(r"[()\?\\/\-]", "_", col)
        col = re.sub(r"\s+", "_", col)
        col = re.sub(r"_+", "_", col)
        col = re.sub(r"[^a-zA-Z0-9]+$", "", col)
        return col.lower()

    return [normalize(c) for c in columns]

def rename_columns(columns):
    novas = []

    for col in columns:
        c = str(col).strip().lower()

        if c == "(nenhum nome de coluna)":
            novas.append("grupo_vulneravel")
        elif c == "sexo_do_suspeito":
            novas.append("genero_do_suspeito")
        elif c in ["sexo_da_vitima", "sexo_da_vítima"]:
            novas.append("genero_da_vitima")
        else:
            novas.append(col)

    return novas

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # df.columns = rename_columns(df.columns)
    df.columns = normalize_columns(rename_columns(df.columns))

    if "violacao" not in df.columns:
        raise ValueError("Coluna 'violacao' não encontrada no DataFrame.")

    df["violacao"] = df["violacao"].astype(str)

    violation_filter = df["violacao"].str.contains(
        r"trafico|tráfico",
        case=False,
        na=False,
        regex=True
    )

    df_filtered = df.loc[violation_filter].copy()

    logging.info(f"DataFrame processado: {len(df_filtered)} linhas filtradas.")
    return df_filtered

def load_csv_dataset(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path, sep=";", encoding="utf-8", dtype=str)
        return df
    except Exception as e:
        logging.error(f"Erro ao carregar o arquivo {file_path}: {e}")
        return pd.DataFrame()   

def process_csv_in_chunks(file_path: str, chunksize: int = 100000) -> pd.DataFrame:
    resultados = []

    for chunk in pd.read_csv(
        file_path,
        sep=";",
        encoding="utf-8",
        chunksize=chunksize,
        dtype=str
    ):
        df_filtered = process_dataframe(chunk)

        if not df_filtered.empty:
            resultados.append(df_filtered)

    if resultados:
        return pd.concat(resultados, ignore_index=True)

    return pd.DataFrame()

def get_csv_files(root_dir):
    csv_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if f.lower().endswith(".csv"):
                csv_files.append(os.path.join(dirpath, f))
    return csv_files

def init_process_files(root_dir, max_workers=2):
    files = get_csv_files(root_dir)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        resultados = list(
            # tqdm(executor.map(process_csv_in_chunks, files), total=len(files))
            tqdm(executor.map(process_dataframe, files), total=len(files))
        )

    resultados = [df for df in resultados if not df.empty]

    if resultados:
        return pd.concat(resultados, ignore_index=True)

    return pd.DataFrame()