# import os
# import numpy as np
# from tqdm import tqdm

# from AutoPYara import AutoPYara
# import yaramod
# import pandas as pd
# import tempfile
# import shutil
# PROJECT_ROOT='/usr/src/app'
# def get_project_path(*paths):
#     """
#     Join paths relative to the project root.
#     Args:
#         *paths: Variable number of path components to join
#     Returns:
#         str: Absolute path joined with project root
#     """
#     return os.path.join(PROJECT_ROOT, *paths)

# def demo_train():
#     myYara = AutoPYara(ngram_top_k=100)

#     # Read CSV with file paths
#     df = pd.read_csv('/usr/src/app/YaraResults/masterCSV/datasetGoodwarePE.csv')

#     givenWkdir = '/usr/src/app/HDDdata/'
#     df = df[0:1]

#     # Replace the initial part of the path
#     if 'File_Path' in df.columns:
#         df['File_Path'] = df['File_Path'].str.replace('/mnt/data_disk1/mabon/', givenWkdir, regex=False)

#     # Create a temporary directory to collect all files
#     with tempfile.TemporaryDirectory() as temp_input_dir:
#         for idx, row in tqdm(df.iterrows(), total=len(df), desc="Copying files"):
#             file_list = [f.strip() for f in row['File_Path'].split(',')]
#             for fpath in file_list:
#                 if os.path.exists(fpath):
#                     shutil.copy(fpath, temp_input_dir)
#                 else:
#                     print(f"Warning: {fpath} does not exist.")


#         # Now that all files are in temp_input_dir, run train for each n-gram size
#         for ngram_size in [8, 16]:
#             myYara.train(
#                 temp_input_dir,
#                 get_project_path("intermediate", "bloom_filters", "benign_New"),
#                 ngram_size=ngram_size
#             )

# if __name__ == '__main__':
#     demo_train()


import os
import shutil
import pandas as pd
from tqdm import tqdm

# Read CSV with file paths
df = pd.read_csv('/usr/src/app/YaraResults/masterCSV/datasetGoodwarePE.csv')
givenWkdir = '/usr/src/app/HDDdata/'

# Replace the initial part of the path
if 'File_Path' in df.columns:
    df['File_Path'] = df['File_Path'].str.replace('/mnt/data_disk1/mabon/', givenWkdir, regex=False)

# Create the destination directory
diffdir = '/usr/src/app/BloomFilterTrain/data/'
os.makedirs(diffdir, exist_ok=True)

# Iterate through each file and copy it into the DIFDIR
for idx, row in tqdm(df.iterrows(), total=len(df), desc="Copying files"):
    file_list = [f.strip() for f in row['File_Path'].split(',')]
    for fpath in file_list:
        if os.path.exists(fpath):
            dest_path = os.path.join(diffdir, os.path.basename(fpath))
            shutil.copy(fpath, dest_path)
        else:
            print(f"Warning: {fpath} does not exist.")
