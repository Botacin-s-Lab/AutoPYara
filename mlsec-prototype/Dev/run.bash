#!/bin/bash

# Base directory where all folders are located (modify this path as needed)
BASE_DIR="/mnt/data_disk1/mabon/datacopy"

# Output directory
OUTPUT_DIR="output"

# List of folders to process
FOLDERS=("APTs" "BB" "BluePex" "CodexGiga" "evasive-it" "Honeypots" "Malshare" 
         "MLSec19" "MLSec20" "MLSec21" "Stefano" "theZoo" "UCSB" "UCSB.JP" "VxHeaven")

# Python script name (assuming it's in the current directory)
PYTHON_SCRIPT="findMyData.py"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Loop through each folder and run the Python script
for FOLDER in "${FOLDERS[@]}"; do
    INPUT_PATH="$BASE_DIR/$FOLDER"
    OUTPUT_CSV="$OUTPUT_DIR/${FOLDER}_pe_files.csv"
    
    echo "Processing folder: $INPUT_PATH"
    echo "Output will be saved to: $OUTPUT_CSV"
    
    # Run the Python script with the folder path and output CSV as arguments
    python3 "$PYTHON_SCRIPT" "$INPUT_PATH" "$OUTPUT_CSV"
    
    # Check if the command was successful
    if [ $? -eq 0 ]; then
        echo "Successfully processed $FOLDER"
    else
        echo "Error processing $FOLDER"
    fi
    
    echo "----------------------------------------"
done

echo "All folders processed!"