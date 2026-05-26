import os
import gc
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

root_dir = "/mnt/c/Users/deinf.janaelson/Documents/Datasets/"
dir_extracted = "/mnt/c/Users/deinf.janaelson/Documents/Datasets/Extracted"

Path(dir_extracted).mkdir(parents=True, exist_ok=True)

def get_csv_files(root_dir):
    return [
        os.path.join(root_dir, f)
        for f in os.listdir(root_dir)
        if f.lower().endswith(".csv")
    ]

import re
import unicodedata

def normalize_columns(columns):
    def normalize(col):

        col = re.sub(r'[^a-zA-Z0-9]+$', '', col).strip()

        # 2. remover acentos
        col = unicodedata.normalize('NFKD', col)
        col = ''.join(c for c in col if not unicodedata.combining(c))

        # 3. substituir especiais por "_"
        col = re.sub(r'[()\?\\\/\-]', '_', col)

        # 4. substituir espaços por "_"
        col = re.sub(r'\s+', '_', col)

        # 5. remover múltiplos "_"
        col = re.sub(r'_+', '_', col)

        # ✅ 6. remover QUALQUER coisa no final que não seja letra ou número
        

        # 7. minúsculo
        col = col.lower()

        return col

    return [normalize(c) for c in columns]

def process_file(file_path):
    file_name = os.path.basename(file_path)
    output_path = os.path.join(dir_extracted, file_name)

    try:
        first_chunk = True

        for chunk in pd.read_csv(
            file_path,
            sep=";",
            encoding="utf-8",
            chunksize=100_000,
            low_memory=True
        ):
            # ✅ normaliza nomes das colunas
            # chunk.columns = normalize_columns(chunk.columns)

            if "violacao" not in chunk.columns:
                continue

            # ✅ filtro correto (somente na coluna)
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

            # ✅ liberar memória do chunk
            del chunk
            del filtrado
            gc.collect()

        return f"OK: {file_name}"

    except Exception as e:
        return f"ERRO: {file_name} → {e}"


files = get_csv_files(root_dir)

# ⚠️ ESSENCIAL EM WSL + ARQUIVOS GRANDES
max_workers = 2

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    results = list(tqdm(executor.map(process_file, files), total=len(files)))

# print final
for r in results:
    print(r)
