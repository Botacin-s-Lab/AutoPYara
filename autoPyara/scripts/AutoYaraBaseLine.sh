#!/bin/bash
# ./run_yara.sh Output MALWAREFAMILY
# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <output_dir> <malicious_path>"
    echo "Example: $0 /usr/src/app/NETS/ /usr/src/app/datacopy/dataYara/APT/"
    exit 1
fi

# Assign input arguments to variables
OUTPUT_DIR="$1"  # -o parameter
MALICIOUS_PATH="$2"  # -mP parameter

# Fixed arguments as provided
BLOOM_FILTER_MALICIOUS="/usr/src/app/intermediate/bloom_filters/malicious"
BLOOM_FILTER_BENIGN="/usr/src/app/intermediate/bloom_filters/benign"
GENERATE_RULES="False"
RULE_OUTPUT_TYPE="yaramod"
CLUSTER_ALGORITHM="VBGMM"
BINARY_CLUSTER_TYPE="SpectralCoCluster"

# Run the Python script with the arguments
python /usr/src/app/yaraMain.py \
    -bfM "$BLOOM_FILTER_MALICIOUS" \
    -bfB "$BLOOM_FILTER_BENIGN" \
    -mP "$MALICIOUS_PATH" \
    -o "$OUTPUT_DIR" \
    -gR "$GENERATE_RULES" \
    -rOT "$RULE_OUTPUT_TYPE" \
    -cA "$CLUSTER_ALGORITHM" \
    -bCT "$BINARY_CLUSTER_TYPE"

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo "Script executed successfully."
else
    echo "Error: Script execution failed."
    exit 1
fi

