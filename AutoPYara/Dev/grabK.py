import os
import pandas as pd
import numpy as np
from collections import defaultdict

# Define the base path
PathBase = '/usr/src/app/YaraResults/yaraRules/retrainedBloomFilters/ssdeep/Autoyara/Th50/'

# Initialize dictionary to store k_clusters values for each cluster index
cluster_k_values = defaultdict(list)
PADDING_SIZE = 5
# Get all subfolders in PathBase
try:
    subfolders = [f for f in os.listdir(PathBase) if os.path.isdir(os.path.join(PathBase, f))]
except (FileNotFoundError, PermissionError):
    exit(1)

# Process each subfolder
for subfolder in subfolders:
    if subfolder.startswith('cluster_'):
        try:
            # Extract cluster index (e.g., 0 from cluster_0)
            cluster_index = int(subfolder.replace('cluster_', ''))
            
            # Path to k_values.csv
            csv_path = os.path.join(PathBase, subfolder, 'k_values.csv')
            
            # Check if k_values.csv exists
            if os.path.exists(csv_path):
                try:
                    # Read the CSV file
                    df = pd.read_csv(csv_path)
                    
                    # Ensure k_clusters column exists
                    if 'k_clusters' in df.columns:
                        # Get k_clusters values (any number of rows)
                        k_values = df['k_clusters'].tolist()
                        if k_values:  # Check if list is not empty
                            # Pad to PADDING_SIZE values using the last value
                            last_value = k_values[-1]
                            k_values.extend([last_value] * (PADDING_SIZE - len(k_values)))
                            cluster_k_values[cluster_index].extend(k_values)
                        else:
                            # Pad with PADDING_SIZE NaN values
                            cluster_k_values[cluster_index].extend([np.nan] * PADDING_SIZE)
                    else:
                        # Pad with PADDING_SIZE NaN values
                        cluster_k_values[cluster_index].extend([np.nan] * PADDING_SIZE)
                except (pd.errors.EmptyDataError, Exception):
                    # Pad with PADDING_SIZE NaN values
                    cluster_k_values[cluster_index].extend([np.nan] * PADDING_SIZE)
            else:
                # Pad with PADDING_SIZE NaN values
                cluster_k_values[cluster_index].extend([np.nan] * PADDING_SIZE)
        except (ValueError, Exception):
            pass

# Convert defaultdict to regular dict for output
cluster_k_values = dict(cluster_k_values)

# Save results to a file for future evaluation
output_file = os.path.join('th50k_ssdeep.csv')
try:
    with open(output_file, 'w') as f:
        f.write('cluster_index,k_clusters\n')
        for cluster_index, k_values in sorted(cluster_k_values.items()):
            for k in k_values:
                # Handle NaN for CSV output
                k_str = 'NaN' if pd.isna(k) else k
                f.write(f"{cluster_index},{k_str}\n")
except Exception:
    pass