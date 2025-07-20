import hashlib
import os
import time
import requests
import pandas as pd
from tqdm import tqdm
import json
import signal
import re
from collections import deque

# List of VirusTotal API keys
API_KEYS = [
    'ae0eaf50c5f7cac4756413a4ebd53cbe7d073c8a8d3a00d3c72fe8ed41e721b5',  # Marcus API
    'bb8c073346e504fd1ec60c7997597a2a201ef778a6609cbf6e49f5fd229f7df3',
    '02ceedd9ebcfe6858cb28c37d25842fb7dc22d46bd7f07ccbc0fafd14d18c785',
    'c967a1fe183f1cb02f246d0fc2b6077605dbef3362514a4707307903556fc50c',
    'c6be15a7dd46b44eadbf988fbd6940ad2e8059c2d9dd7dfe1964383fa0ff7278'
]

# Initialize API key management
class APIKeyManager:
    def __init__(self, api_keys):
        self.keys = deque(api_keys)
        self.current_key = self.keys[0]
        self.error_count = {key: 0 for key in api_keys}
        self.max_errors = 3  # Max consecutive errors before rotating
    
    def get_key(self):
        return self.current_key
    
    def rotate_key(self):
        self.keys.rotate(-1)
        self.current_key = self.keys[0]
        print(f"Rotated to API key: {self.current_key[:8]}...")
    
    def report_error(self):
        self.error_count[self.current_key] += 1
        if self.error_count[self.current_key] >= self.max_errors:
            print(f"Too many errors with key {self.current_key[:8]}..., rotating")
            self.rotate_key()
            self.error_count[self.current_key] = 0

# Initialize API key manager
key_manager = APIKeyManager(API_KEYS)

VT_API_URL = 'https://www.virustotal.com/api/v3/files'
VT_REPORT_URL = 'https://www.virustotal.com/api/v3/analyses/'

# Define output directory for reports
OUTPUT_DIR = '/home/mabon/research/Autoyara/AutoPYara/AutoPYara/scripts/clusteringAlgosGTgen/output/'

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

def calculate_sha256(file_path):
    try:
        with open(file_path, 'rb') as f:
            sha256 = hashlib.sha256()
            while chunk := f.read(8192):
                sha256.update(chunk)
            return sha256.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None

def check_existing_report(sha256):
    headers = {'x-apikey': key_manager.get_key()}
    url = f"{VT_API_URL}/{sha256}"
    
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(180)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            key_manager.error_count[key_manager.get_key()] = 0  # Reset error count on success
            return response.json()
        elif response.status_code == 429:  # Rate limit
            key_manager.report_error()
            key_manager.rotate_key()
            return check_existing_report(sha256)  # Retry with new key
        elif response.status_code == 404:
            return None
        else:
            key_manager.report_error()
            print(f"Error checking existing report for {sha256}: {response.status_code}")
            return None
    except TimeoutException:
        print(f"Checking existing report timed out after 3 minutes for {sha256}")
        return None
    except Exception as e:
        key_manager.report_error()
        print(f"Error checking existing report for {sha256}: {e}")
        return None
    finally:
        signal.alarm(0)

def check_local_report(file_name, sha256, output_dir=OUTPUT_DIR):
    safe_file_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in file_name)
    for file in os.listdir(output_dir):
        if file.startswith(f"vt_report_{safe_file_name}_{sha256[:8]}") and file.endswith('.json'):
            json_file_path = os.path.join(output_dir, file)
            try:
                with open(json_file_path, 'r') as f:
                    return json.load(f), json_file_path
            except Exception as e:
                print(f"Error reading local report {json_file_path}: {e}")
    return None, None

def upload_file(file_path):
    headers = {'x-apikey': key_manager.get_key()}
    
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(180)
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = requests.post(VT_API_URL, headers=headers, files=files)
            if response.status_code == 200:
                key_manager.error_count[key_manager.get_key()] = 0
                return response.json()['data']['id']
            elif response.status_code == 429:
                key_manager.report_error()
                key_manager.rotate_key()
                return upload_file(file_path)
            else:
                key_manager.report_error()
                response.raise_for_status()
    except TimeoutException:
        print(f"Upload timed out after 3 minutes for {file_path}")
        return None
    except Exception as e:
        key_manager.report_error()
        print(f"Error uploading {file_path}: {e}")
        return None
    finally:
        signal.alarm(0)

def get_analysis_report(analysis_id):
    headers = {'x-apikey': key_manager.get_key()}
    
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(240)
        url = f"{VT_REPORT_URL}{analysis_id}"
        start_time = time.time()
        
        while True:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                key_manager.error_count[key_manager.get_key()] = 0
                result = response.json()
                
                elapsed_time = time.time() - start_time
                
                if result['data']['attributes']['status'] == 'completed':
                    if elapsed_time < 180:
                        time_to_wait = 180 - elapsed_time
                        print(f"Analysis completed early. Waiting {time_to_wait:.2f} seconds...")
                        time.sleep(time_to_wait)
                    return result
                
                if elapsed_time < 180:
                    time.sleep(15)
                else:
                    break
            elif response.status_code == 429:
                key_manager.report_error()
                key_manager.rotate_key()
                headers = {'x-apikey': key_manager.get_key()}
                continue
            else:
                key_manager.report_error()
                response.raise_for_status()
    except TimeoutException:
        print(f"Report retrieval timed out after 4 minutes for {analysis_id}")
        return None
    except Exception as e:
        key_manager.report_error()
        print(f"Error getting report for {analysis_id}: {e}")
        return None
    finally:
        signal.alarm(0)

def save_report_to_json(report, file_name, sha256, output_dir=OUTPUT_DIR):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    safe_file_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in file_name)
    json_file_path = os.path.join(output_dir, f"vt_report_{safe_file_name}_{sha256[:8]}_{time.strftime('%Y%m%d_%H%M%S')}.json")
    
    try:
        with open(json_file_path, 'w') as f:
            json.dump(report, f, indent=2)
        return json_file_path
    except Exception as e:
        print(f"Error saving JSON report for {file_name}: {e}")
        return None

def main():
    csv_file = '/home/mabon/research/Autoyara/YaraResults/virusTotalRaw/MissedReports.csv'
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"Error loading CSV file {csv_file}: {e}")
        return
    
    if not all(col in df.columns for col in ['File_Name', 'Full_Path']):
        print("CSV must contain 'File_Name' and 'Full_Path' columns")
        return
    
    # List to store file information for final CSV
    results = []
    
    for index, row in tqdm(df.iterrows(), total=len(df), desc="Processing files"):
        file_name = row['File_Name']
        file_path = row['Full_Path']
        report_path = None
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            results.append({'File_Name': file_name, 'Full_Path': file_path, 'Report_Path': report_path})
            continue
        
        sha256 = calculate_sha256(file_path)
        if not sha256:
            print(f"Skipping {file_name} due to hash calculation error")
            results.append({'File_Name': file_name, 'Full_Path': file_path, 'Report_Path': report_path})
            continue
        
        local_report, local_report_path = check_local_report(file_name, sha256, OUTPUT_DIR)
        if local_report:
            print(f"Local report found for {file_name}")
            report_path = local_report_path
            results.append({'File_Name': file_name, 'Full_Path': file_path, 'Report_Path': report_path})
            continue
        
        vt_report = check_existing_report(sha256)
        if vt_report:
            print(f"Existing VirusTotal report found for {file_name}")
            report_path = save_report_to_json(vt_report, file_name, sha256, OUTPUT_DIR)
            results.append({'File_Name': file_name, 'Full_Path': file_path, 'Report_Path': report_path})
            continue
        
        print(f"Uploading {file_name} to VirusTotal")
        analysis_id = upload_file(file_path)
        if not analysis_id:
            print(f"Skipping {file_name} due to upload error")
            results.append({'File_Name': file_name, 'Full_Path': file_path, 'Report_Path': report_path})
            continue
        
        report = get_analysis_report(analysis_id)
        if report:
            report_path = save_report_to_json(report, file_name, sha256, OUTPUT_DIR)
            if report_path:
                print(f"Report saved for {file_name} at {report_path}")
            else:
                print(f"Failed to save report for {file_name}")
        else:
            print(f"No report retrieved for {file_name}")
        results.append({'File_Name': file_name, 'Full_Path': file_path, 'Report_Path': report_path})
    
    # Save results to CSV
    results_df = pd.DataFrame(results)
    output_csv_path = os.path.join(OUTPUT_DIR, f"vt_report_summary_{time.strftime('%Y%m%d_%H%M%S')}.csv")
    try:
        results_df.to_csv(output_csv_path, index=False)
        print(f"Summary CSV saved at {output_csv_path}")
    except Exception as e:
        print(f"Error saving summary CSV: {e}")

if __name__ == "__main__":
    main()