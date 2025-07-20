for cluster in cluster_*; do
  if [ -d "$cluster" ]; then
    # look for the subfolder matching TrueBEST_K_x
    best=$(find "$cluster" -maxdepth 1 -type d -name 'TrueBEST_K_*' | head -n 1)
    if [ -n "$best" ]; then
      # rename it to "1"
      mv "$best" "$cluster/1"
      # delete all other subfolders in this cluster
      find "$cluster" -mindepth 1 -maxdepth 1 -type d ! -name '1' -exec rm -rf {} +
    fi
  fi
done


2
for cluster in cluster_*; do
  if [ -d "$cluster" ]; then
    best=$(find "$cluster" -maxdepth 1 -type d -name 'TrueBEST_K_*' | head -n 1)
    
    if [ -z "$best" ]; then
      best=$(find "$cluster" -maxdepth 1 -type d -name 'TOP_K_CANDIDATE*' | head -n 1)
    fi
    
    if [ -z "$best" ]; then
      # pick a random *_iKsearch folder
      iksearch_folders=( "$cluster"/*_iKsearch )
      if [ ${#iksearch_folders[@]} -gt 0 ]; then
        rand_index=$(( RANDOM % ${#iksearch_folders[@]} ))
        best="${iksearch_folders[$rand_index]}"
      fi
    fi
    
    if [ -n "$best" ]; then
      mv "$best" "$cluster/1"
      # remove all other folders except 1, but keep files like k_values.csv
      find "$cluster" -mindepth 1 -maxdepth 1 -type d ! -name '1' -exec rm -rf {} +
    fi
  fi
done



3
for cluster in cluster_*; do
  if [ -d "$cluster" ]; then
    # find the yara file
    yara_file=$(find "$cluster" -maxdepth 1 -type f -name '*.yara' | head -n 1)
    if [ -n "$yara_file" ]; then
      mkdir -p "$cluster/1"
      mv "$yara_file" "$cluster/1/"
    fi
  fi
done
