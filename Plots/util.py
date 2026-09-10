import re
import os
import glob
from collections import Counter
from fractions import Fraction

import numpy as np
import pandas as pd


def sanity_h(tprateAutoyaraBase_Train_df, tprateAutoyaraBase_Test, tprateAutoPYara_Train, tprateAutoPYara_Test, df_root, thv):
    """
    Compute the smallest cluster size with valid TP rate data from the input DataFrame lists.

    Parameters:
    - tprateAutoyaraBase_Train_df: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - tprateAutoyaraBase_Test: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - tprateAutoPYara_Train: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - tprateAutoPYara_Test: List of DataFrames with 'Cluster' and 'TP_Rate' columns
    - df_root: DataFrame with 'File_Path', 'SHA256', 'SSDeep', 'Cluster_Label', 'Threshold' columns

    Returns:
    - Smallest cluster size with valid data (integer)
    """
    # Validate input
    dfs_lists = [
        tprateAutoyaraBase_Train_df,
        tprateAutoyaraBase_Test,
        tprateAutoPYara_Train,
        tprateAutoPYara_Test
    ]
    if not all(isinstance(df_list, list) and all(isinstance(df, pd.DataFrame) for df in df_list) for df_list in dfs_lists):
        raise ValueError("All inputs must be lists of pandas DataFrames")
    if not isinstance(df_root, pd.DataFrame):
        raise ValueError("df_root must be a pandas DataFrame")

    # Compute cluster sizes from df_root for Threshold=50
    cluster_sizes = df_root[df_root['Threshold'] == thv].groupby('Cluster_Label').size().reset_index(name='Cluster_Size')
    cluster_size_map = dict(zip(cluster_sizes['Cluster_Label'], cluster_sizes['Cluster_Size']))

    # Collect all clusters with valid TP rate data
    valid_clusters = set()
    for df_list in dfs_lists:
        for df in df_list:
            df = df.replace('None', np.nan).apply(pd.to_numeric, errors='coerce')
            clusters = df['Cluster'].dropna().astype(int).tolist()
            valid_clusters.update(clusters)

    # Map valid clusters to their sizes
    valid_sizes = [cluster_size_map.get(cluster, float('inf')) for cluster in valid_clusters if cluster in cluster_size_map]

    if not valid_sizes:
        raise ValueError("No valid cluster sizes found with TP rate data")

    # Return the smallest cluster size
    smallest_size = int(min(valid_sizes))
    print(smallest_size)


def collect_tprate_data(base_path, name):
    # Initialize lists to store data
    cluster_numbers = []
    tp_rates = []

    # Pattern to match cluster folders (cluster_*)
    folder_pattern = os.path.join(base_path, 'cluster_*')

    # Find all matching folders
    for folder in glob.glob(folder_pattern):
        # Extract cluster number from folder name
        cluster_num = os.path.basename(folder).replace('cluster_', '')

        # Path to tprateAutoPYara_Train.txt
        file_path = os.path.join(folder, name)

        # Check if file exists
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    # Extract TP rate using regex
                    match = re.search(r'TP Rate: (\d+\.\d+)', content)
                    if match:
                        tp_rate = float(match.group(1))
                        cluster_numbers.append(cluster_num)
                        tp_rates.append(tp_rate)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    # Create DataFrame
    df = pd.DataFrame({
        'Cluster': cluster_numbers,
        'TP_Rate': tp_rates
    })

    # Sort by cluster number if needed
    df['Cluster'] = df['Cluster'].astype(int)
    df = df.sort_values('Cluster').reset_index(drop=True)

    return df


def extract_rule_tp_rates(file_path):
    """
    Extracts rule names and their TP rates from a YARA rule file.
    Returns a dictionary mapping rule names to TP rates (as floats).
    """
    rule_tp_map = {}
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            # Split content into rules, capturing rule name and content
            rules = re.split(r'\n\s*rule\s+([^\s{]+)', content.strip())
            # Pair rule names with their content (name, content, name, content, ...)
            rules = [(rules[i], rules[i + 1]) for i in range(1, len(rules), 2)]

            for rule_name, rule_content in rules:
                # Validate rule name
                if not rule_name or not re.match(r'^\w+$', rule_name):
                    print(f"Skipping invalid rule name: {rule_name}")
                    continue

                # Extract TP rate from comments
                # Match either "//Input TP Rate: X/Y" or standalone "//X/Y"
                tp_match = re.search(
                    r'//\s*(?:Input\s+TP\s+Rate\s*:\s*)?(\d+)\s*/\s*(\d+)',
                    rule_content,
                    re.MULTILINE | re.IGNORECASE
                )
                if tp_match:
                    numerator, denominator = map(int, tp_match.groups())
                    tp_rate = Fraction(numerator, denominator) if denominator != 0 else 0
                    rule_tp_map[rule_name] = float(tp_rate)
                else:
                    rule_tp_map[rule_name] = None
                    print(f"Warning: No TP rate found for rule {rule_name}")
                    print(f"Rule content preview:\n{rule_content[:200]}...\n")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return rule_tp_map


def rules_to_dataframe(rule_tp_map, max_runs=15, max_cluster_num=8874):
    """
    Converts a rule-to-TP-rate map into a DataFrame with clusters as rows and runs as columns.
    Includes all clusters from Cluster0 to Cluster{max_cluster_num}, filling missing rows with 0.
    Sorts rows by the numeric part of cluster names (e.g., Cluster0, Cluster1, Cluster2).

    Args:
        rule_tp_map (dict): Dictionary mapping rule names (e.g., 'Cluster0_1') to TP rates.
        max_runs (int): Maximum number of runs (default: 30).
        max_cluster_num (int): Maximum cluster number (default: 9000).

    Returns:
        pd.DataFrame: DataFrame with clusters as rows, runs as columns, and TP rates as values.
    """
    # Extract clusters and runs
    print("LOG:max_cluster_num ", max_cluster_num)
    data = []
    for rule, tp_rate in rule_tp_map.items():
        try:
            cluster, run = rule.rsplit('_', 1)
            run = int(run)
            data.append({'cluster': cluster, 'run': run, 'tp_rate': tp_rate if tp_rate is not None else 0})
        except ValueError:
            print(f"Skipping invalid rule format: {rule}")
            continue

    # Create DataFrame
    df = pd.DataFrame(data)

    # Pivot to get clusters as rows and runs as columns
    pivot_df = df.pivot(index='cluster', columns='run', values='tp_rate')

    # Ensure all columns from 1 to max_runs exist
    columns = list(range(1, max_runs + 1))
    # pivot_df = pivot_df.reindex(columns=columns, fill_value=0)
    # Reindex without fill_value first
    pivot_df = pivot_df.reindex(columns=columns)

    # Then fill missing values with the median
    pivot_df = pivot_df.fillna(pivot_df.median())

    # Fill NaN values (missing TP rates) with 0
    pivot_df = pivot_df.fillna(0)

    # Create index with all clusters from Cluster0 to Cluster{max_cluster_num}
    all_clusters = [f'Cluster{i}' for i in range(max_cluster_num + 1)]
    pivot_df = pivot_df.reindex(index=all_clusters, fill_value=0)

    # Sort index by numeric part of cluster name
    def extract_cluster_number(cluster_name):
        try:
            number = int(re.search(r'\d+', cluster_name).group())
            return number
        except (AttributeError, ValueError):
            print(f"Warning: Could not extract number from cluster name: {cluster_name}")
            return float('inf')

    pivot_df = pivot_df.sort_index(key=lambda x: [extract_cluster_number(name) for name in x])

    return pivot_df


def ensure_columns(dataframes):
    if isinstance(dataframes, pd.DataFrame):
        dataframes = [dataframes]
    elif not isinstance(dataframes, list):
        raise ValueError("Input must be a pandas DataFrame or a list of DataFrames")

    # Make sure all column names are integers
    for i, df in enumerate(dataframes):
        try:
            df.columns = [int(col) for col in df.columns]
            dataframes[i] = df
        except (ValueError, TypeError):
            raise ValueError("All column names must be convertible to integers")

    # Find the maximum cluster size across all DataFrames
    max_size = 0
    for df in dataframes:
        if df.columns.size > 0:
            max_size = max(max_size, max(df.columns))

    cluster_list = list(range(1, max_size + 1))

    # Add all missing columns in a single concat instead of one-by-one
    for i, df in enumerate(dataframes):
        existing_clusters = set(df.columns)
        required_clusters = set(cluster_list)
        missing_clusters = required_clusters - existing_clusters

        if missing_clusters:
            missing_df = pd.DataFrame(
                None,
                index=df.index,
                columns=sorted(missing_clusters)
            )
            df = pd.concat([df, missing_df], axis=1)

        dataframes[i] = df.reindex(columns=cluster_list)

    return dataframes[0] if len(dataframes) == 1 else dataframes


def _bucket_scores_by_size(df_cluster, data, unique_vals):
    """Lay out per-cluster scores as one column per cluster size.

    Linear-time equivalent of Extractor's original loop, which looked up the first
    empty cell with ``df_new[col].isna()`` and grew the frame one ``.loc`` row at a
    time (quadratic in the number of rows). The result is the identical frame:

    * columns ``unique_vals`` (object dtype), index ``0..n_rows-1`` (int64);
    * the k-th score (in ``df_cluster`` order) whose cluster has size ``s`` sits in
      row k of column ``s``; every other cell is ``None``;
    * ``n_rows`` = largest number of clusters sharing one size;
    * if nothing matched, the untouched empty ``pd.DataFrame(columns=unique_vals)``.

    A NaN score leaves its cell "empty", so the next score of that size overwrites
    it, exactly as the original ``isna()`` lookup did.
    """
    cells = {col: [] for col in unique_vals}
    first_na = dict.fromkeys(unique_vals, 0)
    n_rows = 0
    for cluster_name, score in df_cluster.items():
        # Extract the key (e.g., Cluster0 → 0)
        key = int(cluster_name.replace('Cluster', ''))
        if key in data:
            col = data[key]
            column = cells[col]
            # First empty (None/NaN) row of this column; filled cells never empty again.
            i = first_na[col]
            while i < n_rows and not pd.isna(column[i]):
                i += 1
            first_na[col] = i
            if i == n_rows:  # column full -> append an all-None row
                for c in cells.values():
                    c.append(None)
                n_rows += 1
            column[i] = score
    if n_rows == 0:
        return pd.DataFrame(columns=unique_vals)
    return pd.DataFrame(cells, index=pd.Index(np.arange(n_rows, dtype='int64')),
                        columns=unique_vals, dtype=object)


def Extractor(csv_file, file_path, mr, clusSize=2, short=False):
    """Per-cluster mean TP rate of one YARA rule set, optionally grouped by cluster size.

    Args:
        csv_file: clustering CSV; only its ``Cluster_Label`` column is used. Labels
            < 0 (noise) and NaN are ignored.
        file_path: merged ``.yar`` file whose rules are named ``Cluster<i>_<run>`` and
            carry a ``// Input TP Rate: X/Y`` (or ``//X/Y``) comment.
        mr: number of runs per cluster to use (``max_runs``). Runs > mr are ignored;
            a missing run is filled with that run's median over clusters, and a run
            missing for every cluster counts as 0 (see ``rules_to_dataframe``).
        clusSize: minimum cluster size (in the CSV) for a cluster to be counted.
        short: if True return only the per-cluster Series.

    Returns:
        short=True:  ``pd.Series`` indexed ``Cluster0..Cluster<n>`` (n = number of
                     CSV clusters with size >= clusSize), value = mean TP rate over
                     the ``mr`` runs; clusters without rules are 0.
        short=False: ``pd.DataFrame`` with one column per distinct cluster size, see
                     ``_bucket_scores_by_size``. Rule cluster ``i`` is assigned the
                     size of CSV label ``i``.
    """
    df1 = pd.read_csv(csv_file)
    labels = df1['Cluster_Label'].dropna().astype(int).tolist()  # Ensure integers
    # Counter is O(rows); the former per-label labels.count() was O(rows x clusters).
    # Same keys, values and iteration order (still iterates set(labels)).
    counts = Counter(labels)
    cluster_sizes = {label: counts[label] for label in set(labels) if label >= 0}

    # Filter for clusters with size >= 2 (keep the key-value pairs)

    data = {label: size for label, size in cluster_sizes.items() if (size >= clusSize)}
    unique_vals = sorted(set(data.values()))

    result = extract_rule_tp_rates(file_path)
    # for rule_name, tp_rate in result.items():
    #     print(f"Rule: {rule_name}, TP Rate: {tp_rate}")
    df_cluster = rules_to_dataframe(result, max_runs=mr, max_cluster_num=len(data))
    df_cluster = df_cluster.transpose()
    df_cluster = df_cluster.mean(numeric_only=True)
    if short:
        print("Short mode enabled")
        return df_cluster
    # Step 3: Populate the new DataFrame (one column per cluster size)
    return _bucket_scores_by_size(df_cluster, data, unique_vals)