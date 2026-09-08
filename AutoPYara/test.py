import os
from autopyara import AutoPYara

# --- CONFIGURATION ---
malware_dir = "/usr/src/app/HDDdata/datacopy/MLSec19/"
custom_bloom_mal = "/home/mtech-server/RetrainedBloomFilters/malicious/"
custom_bloom_ben = "/home/mtech-server/RetrainedBloomFilters/benign/"

# Get list of files
input_files = [os.path.join(malware_dir, f) for f in os.listdir(malware_dir) 
               if os.path.isfile(os.path.join(malware_dir, f))]

# Limit files for faster testing if needed (optional)
# input_files = input_files[:20] 

print(f"[*] Loaded {len(input_files)} malware samples.")

# Initialize Tool
tool = AutoPYara()

# Define test cases: (Bloom Name, Malicious Path, Benign Path)
bloom_configs = [
    ("EMBER (Built-in)", "ember", "ember"),
    ("AutoPYara (Built-in)", "autopyara", "autopyara"),
    ("Custom (Retrained)", custom_bloom_mal, custom_bloom_ben)
]

print("\n========================================")
print("   STARTING COMPREHENSIVE TEST SUITE   ")
print("========================================\n")

# Store results for final summary
test_results = []

for config_name, bloom_mal, bloom_ben in bloom_configs:
    print(f"\n>>> TESTING CONFIG: {config_name}")
    print(f"    Bloom Mal: {bloom_mal}")
    print(f"    Bloom Ben: {bloom_ben}")
    print("-" * 40)
    
    current_results = {"config": config_name}

    # ---------------------------------------------------------
    # TEST 1: PRESET = AutoYara (VBGMM - Auto-K)
    # ---------------------------------------------------------
    # NOTE: We do NOT pass k_cluster here. VBGMM will infer it.
    print(f"  [Test 1] Preset='AutoYara' (VBGMM - Standard)")
    try:
        res_standard = tool.generate(
            input_files=input_files,
            bloom_malicious=bloom_mal,
            bloom_benign=bloom_ben,
            preset="AutoYara",     # <--- Uses VBGMM + AutoYara Heuristic
            # k_cluster=3,         # <--- REMOVED: Let VBGMM decide K
            output_format="string",
            verbose=False
        )
        k_val = res_standard.get('k_clusters')
        current_results['autoyara_k'] = k_val
        print(f"    SUCCESS: VBGMM generated rule with k={k_val}")
        
    except Exception as e:
        current_results['autoyara_k'] = "FAIL"
        print(f"    FAILED: {e}")

    # ---------------------------------------------------------
    # TEST 2: PRESET = AutoPYara (Augmented - Auto-K)
    # ---------------------------------------------------------
    print(f"  [Test 2] Preset='AutoPYara' (Augmented - DBSCAN)")
    try:
        res_augmented = tool.generate(
            input_files=input_files,
            bloom_malicious=bloom_mal,
            bloom_benign=bloom_ben,
            preset="AutoPYara",    # <--- Uses AugmentedKMeansDBSCANSoft
            output_format="string",
            verbose=False
        )
        k_val = res_augmented.get('k_clusters')
        current_results['autopyara_k'] = k_val
        print(f"    SUCCESS: AutoPYara calculated k={k_val}")
        
    except Exception as e:
        current_results['autopyara_k'] = "FAIL"
        print(f"    FAILED: {e}")

    # ---------------------------------------------------------
    # TEST 3: TARGETED K (Augmented - Force K=4)
    # ---------------------------------------------------------
    print(f"  [Test 3] Preset='AutoPYara' + Target K=4")
    try:
        res_target = tool.generate(
            input_files=input_files,
            bloom_malicious=bloom_mal,
            bloom_benign=bloom_ben,
            preset="AutoPYara",
            augmented_target_k=4, # <--- Force the optimizer to find 4 clusters
            output_format="string",
            verbose=False
        )
        k_val = res_target.get('k_clusters')
        current_results['target_k'] = k_val
        print(f"    SUCCESS: Optimized for Target K=4 -> Result k={k_val}")

    except Exception as e:
        current_results['target_k'] = "FAIL"
        print(f"    FAILED: {e}")
        
    test_results.append(current_results)

print("\n========================================")
print("           FINAL RESULTS SUMMARY        ")
print("========================================")
print(f"{'Configuration':<25} | {'AutoYara K (VBGMM)':<18} | {'AutoPYara K (DBSCAN)':<20} | {'Target K (Goal=4)':<15}")
print("-" * 85)

for res in test_results:
    print(f"{res['config']:<25} | {str(res.get('autoyara_k', 'N/A')):<18} | {str(res.get('autopyara_k', 'N/A')):<20} | {str(res.get('target_k', 'N/A')):<15}")

print("\n========================================")
