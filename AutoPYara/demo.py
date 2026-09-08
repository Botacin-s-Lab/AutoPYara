import os
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN, SpectralCoclustering
from sklearn.mixture import BayesianGaussianMixture
from skfuzzy.cluster import cmeans

# 1. TRAVERSE ALL DATE DIRECTORIES
def collect_exe_data(root_path):
    features = []
    file_metadata = [] # To keep track of filename and parent folder (date)
    
    print(f"Scanning directories in {root_path}...")
    
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if file.lower().endswith('.exe'):
                path = os.path.join(root, file)
                try:
                    stats = os.stat(path)
                    parent_dir = os.path.basename(root)
                    
                    # BASIC FEATURE EXTRACTION
                    # We use file size and the 'date' from the folder name as features
                    # Convert date '2012-05-20' into a numerical timestamp or year
                    year = int(parent_dir.split('-')[0]) if '-' in parent_dir else 0
                    
                    features.append([stats.st_size, year])
                    file_metadata.append(f"{parent_dir}/{file}")
                except Exception as e:
                    continue

    return np.array(features), file_metadata

# PATH TO YOUR MAIN FOLDER
root_folder = './path_to_your_data' 
data, labels = collect_exe_data(root_folder)

if len(data) == 0:
    print("No .exe files found. Check your path!")
else:
    # SCALE DATA
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)
    
    # 2D PROJECTION FOR PLOTTING
    pca = PCA(n_components=2)
    pca_data = pca.fit_transform(data_scaled)

    # 2. RUN THE 4 ALGORITHMS
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))

    # A. DBSCAN (The Heuristic Predictor)
    db = DBSCAN(eps=0.3, min_samples=3).fit_predict(data_scaled)
    axes[0, 0].scatter(pca_data[:, 0], pca_data[:, 1], c=db, cmap='tab10', s=10)
    axes[0, 0].set_title("DBSCAN (Heuristic Pre-step)")

    # B. VBGMM (The AutoYara Baseline)
    vbgmm = BayesianGaussianMixture(n_components=10, random_state=42).fit_predict(data_scaled)
    axes[0, 1].scatter(pca_data[:, 0], pca_data[:, 1], c=vbgmm, cmap='viridis', s=10)
    axes[0, 1].set_title("VBGMM (Baseline)")

    # C. Fuzzy C-Means (The Conceptual Foundation)
    # Requires transpose: (features, samples)
    cntr, u, u0, d, jm, p, fpc = cmeans(data_scaled.T, c=5, m=2, error=0.005, maxiter=1000)
    fcm_labels = np.argmax(u, axis=0)
    axes[1, 0].scatter(pca_data[:, 0], pca_data[:, 1], c=fcm_labels, cmap='plasma', s=10)
    axes[1, 0].set_title("Fuzzy C-Means (Soft Partitioning)")

    # D. Spectral Co-Clustering (Biclustering Framework)
    # We use abs() because Co-Clustering expects a non-negative data matrix
    sc = SpectralCoclustering(n_clusters=5, random_state=0)
    sc.fit(np.abs(data_scaled))
    axes[1, 1].scatter(pca_data[:, 0], pca_data[:, 1], c=sc.row_labels_, cmap='coolwarm', s=10)
    axes[1, 1].set_title("Spectral Co-Clustering (Z-Matrix)")

    plt.suptitle(f"Clustering Analysis of {len(data)} Executables across Date Folders")
    plt.show()
