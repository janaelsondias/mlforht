import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

root_dir = "/mnt/c/Users/deinf.janaelson/Documents/Datasets/"
dir_extracted = "/mnt/c/Users/deinf.janaelson/Documents/Datasets/Extracted"

Path(dir_extracted).mkdir(parents=True, exist_ok=True)

def get_csv_files(root_dir):
    return [f for f in os.listdir(root_dir) if f.lower().endswith(".csv")]

def contains_trafficking(line):
    l = line.lower()
    return "trafico" in l or "tráfico" in l

# def process_file(file_name):
#     input_path = os.path.join(root_dir, file_name)
#     output_path = os.path.join(dir_extracted, file_name)

#     with open(input_path, "r", encoding="utf-8", errors="ignore") as f_in, \
#          open(output_path, "w", encoding="utf-8") as f_out:

#         # cabeçalho
#         header = f_in.readline()
#         f_out.write(header)

#         # processamento em streaming
#         for line in f_in:
#             if contains_trafficking(line):
#                 f_out.write(line)

#     print(f"OK: {file_name}")
def process_file(file_name):
    input_path = os.path.join(root_dir, file_name)
    output_path = os.path.join(dir_extracted, file_name)

    with open(input_path, "r", encoding="utf-8", errors="ignore") as f_in, \
         open(output_path, "w", encoding="utf-8") as f_out:

        header = f_in.readline()
        f_out.write(header)

        while True:
            lines = f_in.readlines(1024 * 1024)  # 1MB por bloco
            if not lines:
                break

            for line in lines:
                if contains_trafficking(line):
                    f_out.write(line)

files = get_csv_files(root_dir)

# ⚠️ MUITO IMPORTANTE (ajuste fino)
max_workers = 2  # ideal para arquivos grandes (evita travar o disco)

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # executor.map(process_file, files)
    executor.map(process_file, files[8:10])