import os
import shutil

# Define the root directory
root_dir = "/usr/src/app/YaraTest/bestK"

# Iterate through each th* subfolder
for subfolder in os.listdir(root_dir):
    subfolder_path = os.path.join(root_dir, subfolder)

    # Check if it's a directory and starts with 'th'
    if os.path.isdir(subfolder_path) and subfolder.startswith("th"):
        print(f"Processing subfolder: {subfolder_path}")

        # Iterate through all nested folders (e.g., cluster_*) inside each th* folder
        for cluster_folder in os.listdir(subfolder_path):
            cluster_path = os.path.join(subfolder_path, cluster_folder)

            # Check if it's a directory
            if os.path.isdir(cluster_path):
                # Recursively walk through all subdirectories
                for root, dirs, files in os.walk(cluster_path):
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        # Check if the folder does NOT start with 'TrueBest_K_' (case-insensitive)
                        if not dir_name.lower().startswith("truebest_k_"):
                            #print(f"Deleting folder: {dir_path}")
                            shutil.rmtree(dir_path)
                        else:
                            print(f"Keeping folder: {dir_path}")
                            # Rename it to "1"
                            new_path = os.path.join(root, "1")
                            # Avoid overwriting if "1" already exists
                            if os.path.exists(new_path):
                                print(f"Warning: '{new_path}' already exists. Skipping rename.")
                            else:
                                os.rename(dir_path, new_path)
                                #print(f"Renamed '{dir_path}' to '{new_path}'")
