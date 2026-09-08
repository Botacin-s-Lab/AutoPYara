import unittest
import os
import shutil
import csv
import time
import threading
import concurrent.futures
from autopyara import AutoPYara
import jpype

# ==========================================
# CONFIGURATION
# ==========================================
MALWARE_DIR = "/mnt/data/stanic_copy/malware/MLSec21"
TEST_FILE_COUNT = 5
MAX_WORKERS = 3  # <--- Number of parallel threads

EXPERIMENT_FLAGS = [
    "autopyara", 
    "ember", 
    "/home/mtech-server/RetrainedBloomFilters" 
]

# Thread synchronization for CSV writing
CSV_LOCK = threading.Lock()

class TestAutoPYaraExhaustiveMT(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n[+] Setting up Multi-Threaded Test Environment...")
        
        # 1. Load Files Once
        if not os.path.exists(MALWARE_DIR):
            raise FileNotFoundError(f"Malware directory not found: {MALWARE_DIR}")
        
        all_files = [os.path.join(MALWARE_DIR, f) for f in os.listdir(MALWARE_DIR) 
                     if os.path.isfile(os.path.join(MALWARE_DIR, f))]
        
        cls.input_files = all_files[:TEST_FILE_COUNT]
        print(f"    - Loaded {len(cls.input_files)} files.")

        # 2. Ensure JVM is started (globally) before threads spawn
        # We instantiate one dummy just to force JVM start if not running
        try:
            _ = AutoPYara() 
            print("    - JVM initialized.")
        except Exception as e:
            raise RuntimeError(f"JVM Init Failed: {e}")

        # 3. Setup Results
        cls.root_results = os.path.join(os.getcwd(), "test_results_mt")
        if os.path.exists(cls.root_results):
            shutil.rmtree(cls.root_results)
        os.makedirs(cls.root_results)
        
        cls.csv_path = os.path.join(cls.root_results, "exhaustive_mt_summary.csv")
        
        # Initialize CSV Header
        with open(cls.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Index", "Bloom_Source", "Bicluster", "Cluster_Alg", 
                "Heuristic", "K_Mode", "Input_K", "Target_K", 
                "Status", "Result_K", "Time(s)", "Error"
            ])

    def run_single_task(self, task_data):
        """
        Worker function to run a single configuration.
        Must create its own AutoPYara instance for thread safety.
        """
        t = task_data
        idx = t['index']
        
        # Attach thread to JVM (Good practice in JPype multithreading)
        if not jpype.isThreadAttachedToJVM():
            jpype.attachThreadToJVM()

        # Instantiate dedicated tool for this thread
        # (Prevents state collision between threads)
        local_tool = AutoPYara(ngram_top_k=500)

        # Path Logic
        if t['flag'] in ["autopyara", "ember"]:
            b_mal = t['flag']
            b_ben = t['flag']
            config_name = t['flag']
        else:
            b_mal = os.path.join(t['flag'], "malicious")
            b_ben = os.path.join(t['flag'], "benign")
            config_name = "Custom"

        print(f"[START] Task {idx}: {config_name} | {t['cl']} | {t['mode']}\n", end="")

        start_time = time.time()
        status = "SUCCESS"
        error_msg = ""
        result_k = "N/A"

        try:
            result = local_tool.generate(
                input_files=self.input_files,
                bloom_malicious=b_mal,
                bloom_benign=b_ben,
                bicluster_alg=t['bi'],
                cluster_alg=t['cl'],
                selection_heuristic=t['heur'],
                k_cluster=t['k_in'],
                augmented_target_k=t['aug_k'],
                output_format="string",
                verbose=False
            )
            
            result_k = result.get('k_clusters') or result.get('k') or "Unknown"

            # Save Rule Artifact
            if 'output' in result:
                safe_alg = t['cl'].replace(" ", "_")
                safe_mode = t['mode'].replace("=", "_")
                fname = f"{idx}_{config_name}_{safe_alg}_{safe_mode}.yar"
                save_path = os.path.join(self.root_results, fname)
                with open(save_path, 'w') as f:
                    f.write(result['output'])

        except Exception as e:
            status = "ERROR"
            error_msg = str(e)
            print(f"[FAIL] Task {idx}: {e}\n", end="")

        duration = time.time() - start_time
        print(f"[DONE] Task {idx} finished in {duration:.2f}s (K={result_k})\n", end="")

        # Write to CSV (Thread Safe)
        with CSV_LOCK:
            with open(self.csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    idx, config_name, t['bi'], t['cl'], 
                    t['heur'], t['mode'], t['k_in'], t['aug_k'], 
                    status, result_k, f"{duration:.2f}", error_msg
                ])

    def test_every_single_configuration_mt(self):
        
        # --- DEFINITIONS ---
        bicluster_opts = ['SpectralCoCluster', 'SpectralCoClusterScale']
        heuristics = ['AutoYara', 'PYara']
        
        manual_k_algs = ['KMeans', 'KMeansSoft', 'Random']
        manual_k_values = [2, 4]

        native_auto_algs = ['VBGMM']
        native_k_modes = [(0, None, "Implicit"), (3, None, "Forced")]

        augmented_algs = [
            'AugmentedKMeansDBSCAN', 'AugmentedKMeansDBSCANSoft',
            'AugmentedKMeansVT', 'AugmentedKMeansVTSoft'
        ]
        augmented_modes = [(0, None, "Auto-Calc"), (0, 4, "Target-Opt")]

        # --- GENERATE TASK LIST ---
        tasks = []
        counter = 1

        for flag in EXPERIMENT_FLAGS:
            for bi in bicluster_opts:
                for heur in heuristics:
                    
                    # 1. Manual K
                    for alg in manual_k_algs:
                        for k in manual_k_values:
                            tasks.append({
                                'index': counter, 'flag': flag, 'bi': bi, 'cl': alg, 'heur': heur,
                                'k_in': k, 'aug_k': None, 'mode': f"Manual_K={k}"
                            })
                            counter += 1

                    # 2. Native Auto (VBGMM)
                    for alg in native_auto_algs:
                        for k, _, mode_desc in native_k_modes:
                            tasks.append({
                                'index': counter, 'flag': flag, 'bi': bi, 'cl': alg, 'heur': heur,
                                'k_in': k, 'aug_k': None, 'mode': mode_desc
                            })
                            counter += 1

                    # 3. Augmented
                    for alg in augmented_algs:
                        for k, aug_k, mode_desc in augmented_modes:
                            tasks.append({
                                'index': counter, 'flag': flag, 'bi': bi, 'cl': alg, 'heur': heur,
                                'k_in': k, 'aug_k': aug_k, 'mode': mode_desc
                            })
                            counter += 1

        total_tasks = len(tasks)
        print(f"\n--- Starting Multi-Threaded Matrix ({total_tasks} Tasks) ---")
        print(f"--- Max Workers: {MAX_WORKERS} ---\n")

        # --- EXECUTE WITH THREAD POOL ---
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # map preserves order in result, but we handle writes inside the function
            # so submit is better here to just let them fire
            futures = [executor.submit(self.run_single_task, t) for t in tasks]
            concurrent.futures.wait(futures)

if __name__ == '__main__':
    unittest.main()