import hashlib
import os
import time
import requests
import pandas as pd
from tqdm import tqdm
import json
import signal  # Added for timeout handling

# Replace with your VirusTotal API key
API_KEY = 'bb8c073346e504fd1ec60c7997597a2a201ef778a6609cbf6e49f5fd229f7df3'
VT_API_URL = 'https://www.virustotal.com/api/v3/files'
VT_REPORT_URL = 'https://www.virustotal.com/api/v3/analyses/'
OUTPUT_DIR = "vt_reports/"
FAILED_CSV = "output/failed_vt_queries.csv"  # New CSV for failed queries

# Timeout handler
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

def calculate_sha256(file_path):
    """Calculate SHA256 hash of a file"""
    try:
        with open(file_path, 'rb') as f:
            sha256 = hashlib.sha256()
            while chunk := f.read(8192):
                sha256.update(chunk)
            return sha256.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None

def upload_file(file_path, api_key):
    """Upload file to VirusTotal with 2-minute timeout"""
    headers = {'x-apikey': api_key}
    
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(120)  # 2 minutes in seconds
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = requests.post(VT_API_URL, headers=headers, files=files)
            response.raise_for_status()
            return response.json()['data']['id']
    except TimeoutException:
        print(f"Upload timed out after 2 minutes for {file_path}")
        return None
    except Exception as e:
        print(f"Error uploading {file_path}: {e}")
        return None
    finally:
        signal.alarm(0)  # Cancel the alarm

def get_analysis_report(analysis_id, api_key):
    """Get analysis report from VirusTotal with 2-minute timeout"""
    headers = {'x-apikey': api_key}
    
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(120)  # 2 minutes in seconds
    
    try:
        url = f"{VT_REPORT_URL}{analysis_id}"
        while True:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result['data']['attributes']['status'] == 'completed':
                return result
            time.sleep(15)
    except TimeoutException:
        print(f"Report retrieval timed out after 2 minutes for {analysis_id}")
        return None
    except Exception as e:
        print(f"Error getting report for {analysis_id}: {e}")
        return None
    finally:
        signal.alarm(0)  # Cancel the alarm

def save_report_to_json(report, file_name, output_dir=OUTPUT_DIR):
    """Save the VirusTotal report to a JSON file"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    safe_file_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in file_name)
    json_file_path = os.path.join(output_dir, f"vt_report_{safe_file_name}_{time.strftime('%Y%m%d_%H%M%S')}.json")
    
    try:
        with open(json_file_path, 'w') as f:
            json.dump(report, f, indent=2)
        return json_file_path
    except Exception as e:
        print(f"Error saving JSON report for {file_name}: {e}")
        return None

def append_to_failed_csv(file_name, full_path, reason):
    """Append failed file info to a separate CSV"""
    if not os.path.exists('output'):
        os.makedirs('output')
    
    data = {
        'File_Name': [file_name],
        'Full_Path': [full_path],
        'Failure_Reason': [reason],
        'Timestamp': [time.strftime('%Y-%m-%d %H:%M:%S')]
    }
    
    df = pd.DataFrame(data)
    # Append to CSV if exists, create new if not
    if os.path.exists(FAILED_CSV):
        df.to_csv(FAILED_CSV, mode='a', header=False, index=False)
    else:
        df.to_csv(FAILED_CSV, mode='w', header=True, index=False)

def process_csv(csv_path):
    """Process CSV file and collect raw VT reports, saving each as JSON"""
    try:
        df = pd.read_csv(csv_path)
        
        if 'File_Name' not in df.columns or 'Full_Path' not in df.columns:
            raise ValueError("CSV must contain 'File_Name' and 'Full_Path' columns")
        
        unaccounted_csv_path = "output/UnAccountedData.csv"
        unaccounted_df = pd.read_csv(unaccounted_csv_path)
        
        if 'File_Name' not in unaccounted_df.columns:
            raise ValueError("UnAccounted.csv must contain a 'File_Name' column")
        
        unaccounted_files = set(unaccounted_df['File_Name'].str.strip())
        results = []
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing files"):
            file_name = str(row['File_Name']).strip()
            full_path = str(row['Full_Path']).strip()
            
            if not os.path.exists(full_path):
                print(f"File not found: {full_path}")
                results.append((file_name, full_path, None))
                append_to_failed_csv(file_name, full_path, "File not found")
                continue
            
            if file_name in unaccounted_files:
                print(f"Processing: {file_name} ({full_path})")
                sha256 = calculate_sha256(full_path)
                if not sha256:
                    print(f"Skipping {file_name} due to hash error")
                    results.append((file_name, full_path, None))
                    append_to_failed_csv(file_name, full_path, "Hash calculation failed")
                    continue
                    
                analysis_id = upload_file(full_path, API_KEY)
                if not analysis_id:
                    print(f"Skipping {file_name} due to upload error")
                    results.append((file_name, full_path, None))
                    append_to_failed_csv(file_name, full_path, "Upload failed or timed out")
                    continue
                    
                report = get_analysis_report(analysis_id, API_KEY)
                if not report:
                    print(f"Skipping {file_name} due to report retrieval error")
                    results.append((file_name, full_path, None))
                    append_to_failed_csv(file_name, full_path, "Report retrieval failed or timed out")
                    continue
                
                json_path = save_report_to_json(report, file_name)
                results.append((file_name, full_path, json_path))
                print(f"Report saved for {file_name} at {json_path if json_path else 'None'}")
                
                time.sleep(15)
        
        results_df = pd.DataFrame(results, columns=['File_Name', 'Full_Path', 'VT_Report_Path'])
        results_df.to_csv('output/vt_report_paths.csv', index=False)
        print(f"Summary saved to 'vt_report_paths.csv'. JSON reports saved in '{OUTPUT_DIR}' folder.")
        print(f"Failed queries logged to '{FAILED_CSV}'.")
        
    except Exception as e:
        print(f"Error processing CSV: {e}")

if __name__ == "__main__":
    process_csv("output/dataSet/APTs_pe_files.csv")