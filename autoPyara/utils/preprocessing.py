import ssdeep
import os
from typing import List, Dict, Optional
import argparse
from pathlib import Path
import sys
import json

def compute_file_hash(filepath: str) -> Optional[str]:
    """
    Compute the ssdeep hash for a single file.

    Args:
        filepath: Path to the file to hash

    Returns:
        The ssdeep hash as a string, or None if there was an error
    """
    try:
        # Read the file in binary mode
        with open(filepath, 'rb') as f:
            file_data = f.read()
            return ssdeep.hash(file_data)
    except Exception as e:
        print(f"Error processing {filepath}: {str(e)}", file=sys.stderr)
        return None

def process_file_list(file_paths: List[str]) -> Dict[str, str]:
    """
    Process a list of file paths and generate ssdeep hashes.

    Args:
        file_paths: List of paths to files

    Returns:
        Dictionary mapping file paths to their ssdeep hashes
    """
    results = {}

    for filepath in file_paths:
        # Normalize path and check if file exists
        path = Path(str(filepath)).resolve()
        if not path.is_file():
            print(f"Warning: {filepath} is not a file or doesn't exist", file=sys.stderr)
            continue

        hash_result = compute_file_hash(str(filepath))
        if hash_result:
            results[str(path)] = hash_result

def java_to_python_paths(file_paths: List[Path]) -> List[str]:
    results = list()

    for filepath in file_paths:
        # Normalize path and check if file exists
        results.append(str(filepath))

    return results