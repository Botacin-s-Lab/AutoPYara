import os
import pandas as pd
from tqdm import tqdm
import pefile
import argparse

def find_pe_files(folder_path, output_file):
    """
    Scan a folder recursively for valid PE files using pefile.
    
    Args:
        folder_path (str): Path to the folder to scan
        output_file (str): Name of the output CSV file
        
    Returns:
        pd.DataFrame: DataFrame containing file names and full paths of valid PE files
    """
    # Initialize empty lists to store file information
    file_paths = []
    file_names = []
    
    # Check if folder exists
    if not os.path.exists(folder_path):
        raise ValueError(f"The folder path {folder_path} does not exist")
    
    # Get total number of files for progress bar (initial estimate)
    total_files = sum(len(files) for _, _, files in os.walk(folder_path))
    
    # Walk through directory with progress bar
    print(f"Scanning folder: {folder_path}")
    with tqdm(total=total_files, desc="Processing files", unit="file") as pbar:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                
                # Verify if it's a valid PE file using pefile
                try:
                    pe = pefile.PE(full_path, fast_load=True)  # Fast load for quicker validation
                    pe.close()  # Close the PE object to free resources
                    file_paths.append(full_path)
                    file_names.append(file)
                except pefile.PEFormatError:
                    # Silently skip non-PE files
                    pass
                except Exception as e:
                    print(f"Error processing {full_path}: {str(e)}")
                
                pbar.update(1)
    
    # Create DataFrame
    df = pd.DataFrame({
        'File_Name': file_names,
        'Full_Path': file_paths
    })
    
    # Save to CSV with robust encoding handling
    try:
        # Try UTF-8 with error replacement
        df.to_csv(output_file, index=False, encoding='utf-8', errors='replace')
        print(f"\nFound {len(df)} valid PE files")
        print(f"Results saved to {output_file} with UTF-8 encoding (replaced invalid characters)")
    except Exception as e:
        print(f"Primary save failed: {str(e)}")
        # Alternative approach: Clean the data first
        df_cleaned = df.copy()
        df_cleaned['File_Name'] = df['File_Name'].apply(
            lambda x: x.encode('utf-8', errors='replace').decode('utf-8')
        )
        df_cleaned['Full_Path'] = df['Full_Path'].apply(
            lambda x: x.encode('utf-8', errors='replace').decode('utf-8')
        )
        try:
            df_cleaned.to_csv(output_file, index=False, encoding='utf-8')
            print(f"\nFound {len(df)} valid PE files")
            print(f"Results saved to {output_file} after cleaning special characters")
        except Exception as final_e:
            print(f"Failed to save CSV even after cleaning: {str(final_e)}")
            # Log problematic entries for debugging
            problematic = df[df['File_Name'].str.contains(r'[^\x00-\x7F]', regex=True)]
            print(f"Found {len(problematic)} entries with special characters:")
            print(problematic.head())
            return None
    
    return df

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Scan a folder for valid PE files and save results to CSV")
    parser.add_argument("input_folder", help="Path to the folder to scan for PE files")
    parser.add_argument("output_csv", help="Name of the output CSV file")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Use the provided arguments
    try:
        pe_files_df = find_pe_files(args.input_folder, args.output_csv)
        if pe_files_df is not None:
            print("\nFirst few entries:")
            print(pe_files_df.head())
    except ValueError as e:
        print(f"Error: {str(e)}")