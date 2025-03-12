import hashlib
import os
import time
import requests
import pandas as pd
from tqdm import tqdm
import json
# Replace with your VirusTotal API key
API_KEY = 'bb8c073346e504fd1ec60c7997597a2a201ef778a6609cbf6e49f5fd229f7df3'
VT_API_URL = 'https://www.virustotal.com/api/v3/files'
VT_REPORT_URL = 'https://www.virustotal.com/api/v3/analyses/'
OUTPUT_DIR = "vt_reports/"  # Directory where JSON reports will be saved




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
    """Upload file to VirusTotal"""
    headers = {
        'x-apikey': api_key
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = requests.post(VT_API_URL, headers=headers, files=files)
            response.raise_for_status()
            return response.json()['data']['id']
    except Exception as e:
        print(f"Error uploading {file_path}: {e}")
        return None

def get_analysis_report(analysis_id, api_key):
    """Get analysis report from VirusTotal"""
    headers = {
        'x-apikey': api_key
    }
    
    try:
        url = f"{VT_REPORT_URL}{analysis_id}"
        while True:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result['data']['attributes']['status'] == 'completed':
                return result
            time.sleep(15)  # Wait before polling again
    except Exception as e:
        print(f"Error getting report for {analysis_id}: {e}")
        return None

def save_report_to_json(report, file_name, output_dir=OUTPUT_DIR):
    """Save the VirusTotal report to a JSON file"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create a safe filename by replacing special characters
    safe_file_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in file_name)
    json_file_path = os.path.join(output_dir, f"vt_report_{safe_file_name}_{time.strftime('%Y%m%d_%H%M%S')}.json")
    
    try:
        with open(json_file_path, 'w') as f:
            json.dump(report, f, indent=2)
        return json_file_path
    except Exception as e:
        print(f"Error saving JSON report for {file_name}: {e}")
        return None
    


def process_csv(csv_path):
    """Process CSV file and collect raw VT reports, saving each as JSON"""
    try:
        # Read main CSV with pandas
        df = pd.read_csv(csv_path)
        
        # Ensure column names are correct
        if 'File_Name' not in df.columns or 'Full_Path' not in df.columns:
            raise ValueError("CSV must contain 'File_Name' and 'Full_Path' columns")
        
        # Load the UnAccounted.csv file
        unaccounted_csv_path = "output/UnAccountedData.csv"
        unaccounted_df = pd.read_csv(unaccounted_csv_path)
        
        if 'File_Name' not in unaccounted_df.columns:
            raise ValueError("UnAccounted.csv must contain a 'File_Name' column")
        
        unaccounted_files = set(unaccounted_df['File_Name'].str.strip())  # Convert to set for efficient lookup
        results = []
        
        # Iterate through rows of the main CSV with tqdm
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing files"):
            file_name = str(row['File_Name']).strip()
            full_path = str(row['Full_Path']).strip()
            
            # Check if the file exists
            if not os.path.exists(full_path):
                print(f"File not found: {full_path}")
                results.append((file_name, full_path, None))
                continue
            
            # Check if the file is in UnAccounted.csv
            if file_name in unaccounted_files:
                print(f"Processing: {file_name} ({full_path})")
                # Calculate hash
                sha256 = calculate_sha256(full_path)
                if not sha256:
                    print(f"Skipping {file_name} due to hash error")
                    results.append((file_name, full_path, None))
                    continue
                    
                # Upload file
                analysis_id = upload_file(full_path, API_KEY)
                if not analysis_id:
                    print(f"Skipping {file_name} due to upload error")
                    results.append((file_name, full_path, None))
                    continue
                    
                # Get report
                report = get_analysis_report(analysis_id, API_KEY)
                
                # Save the report to a JSON file immediately after retrieval
                json_path = save_report_to_json(report, file_name) if report else None
                
                # Store the path to the JSON file in results
                results.append((file_name, full_path, json_path))
                print(f"Report saved for {file_name} at {json_path if json_path else 'None'}")
                
                # Respect VirusTotal's rate limit (4 requests/min for free tier)
                time.sleep(15)
        
        # Create results DataFrame and save to CSV
        results_df = pd.DataFrame(results, columns=['File_Name', 'Full_Path', 'VT_Report_Path'])
        results_df.to_csv('output/vt_report_paths.csv', index=False)
        print(f"Summary saved to 'vt_report_paths.csv'. JSON reports saved in '{OUTPUT_DIR}' folder.")
        
    except Exception as e:
        print(f"Error processing CSV: {e}")



# Example usage
if __name__ == "__main__":
    process_csv("output/dataSet/APTs_pe_files.csv")