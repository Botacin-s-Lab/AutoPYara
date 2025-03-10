
# Get the directory containing the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define project root relative to script location
# Assuming this script is in the project root or a known location relative to it
PROJECT_ROOT = os.path.join(os.path.dirname(SCRIPT_DIR), "mlsec-prototype")

def get_project_path(*paths):
    """
    Join paths relative to the project root.
    Args:
        *paths: Variable number of path components to join
    Returns:
        str: Absolute path joined with project root
    """
    return os.path.join(PROJECT_ROOT, *paths)


def save_box_plot_data(box_plot_set, dataset_series, container_directory="graphs"):
    # Create output directory if it doesn't exist
    os.makedirs(get_project_path("output", container_directory), exist_ok=True)
    os.makedirs(get_project_path("output", container_directory, dataset_series), exist_ok=True)

    # Create filename with dataset series name
    filename = get_project_path("output", container_directory, dataset_series, "Evaluation Results.json")

    # Convert any numpy arrays to lists for JSON serialization
    serializable_data = {}
    for algorithm, metrics in box_plot_set.items():
        serializable_data[algorithm] = {
            metric: list(values) if hasattr(values, '__iter__') else values
            for metric, values in metrics.items()
        }

    # Save to file with nice formatting
    with open(filename, 'w') as f:
        json.dump(serializable_data, f, indent=4)

    print(f"Saved box plot data to: {filename}")

def load_box_plot_data_from_file(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"No saved data found at: {filename}")
        return None

def load_box_plot_data(dataset_series, container_directory="graphs"):
    filename = get_project_path("output", container_directory, dataset_series, "Evaluation Results.json")

    return load_box_plot_data_from_file(filename)

def save_plot(save_path=None):
    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save or display the plot
    if save_path:
        # Save as PDF for vector graphics
        if not save_path.endswith('.pdf'):
            save_path = save_path.rsplit('.', 1)[0] + '.pdf'

        plt.savefig(save_path,
                    format='pdf',
                    bbox_inches='tight',  # Ensures no labels are cut off
                    pad_inches=0.1,  # Adds small padding around the plot
                    dpi=300)  # High DPI for quality
    else:
        plt.show()

    # Close the figure to free memory
    plt.close()

def setup_plot_style():
    # Update plot to be LaTex friendly
    # plt.rcParams.update({
    #     "text.usetex": True,
    #     "font.family": "serif",
    #     "font.serif": ["Computer Modern Roman"],
    # })

    # Use a paper style
    plt.style.use('seaborn-v0_8-paper')

    # Increase font sizes
    plt.rcParams.update({
        'font.size': 14,          # Base font size
        'axes.titlesize': 16,     # Title font size
        'axes.labelsize': 14,     # Axis label size
        'xtick.labelsize': 12,    # X-axis tick label size
        'ytick.labelsize': 12,    # Y-axis tick label size
        'legend.fontsize': 12,    # Legend font size
        'figure.titlesize': 18    # Figure title size
    })

def human_readable_formatter(x, p):
    """Convert bytes to human readable string"""
    if x < 2**10:
        return f"{x:.0f}B"
    elif x < 2**20:
        return f"{x/2**10:.0f}KB"
    elif x < 2**30:
        return f"{x/2**20:.0f}MB"
    else:
        return f"{x/2**30:.0f}GB"

def truncate_string(text, max_length=20, suffix='...'):
    """Cuts off strings if they're too long"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def get_directory_size_histogram(directory_path, series_name="Generic", save_path=None):
    sizes = []
    names = []
    for file_name in os.listdir(directory_path):
        sizes.append(os.path.getsize(os.path.join(directory_path, file_name)))
        names.append(truncate_string(file_name, 15))

    print("name before", names)
    sizes, names = zip(*sorted(zip(sizes, names)))
    sizes = list(sizes)
    names = list(names)

    # Set up the plot
    setup_plot_style()
    plt.figure(figsize=(12, 6), dpi=300)

    # Create the bar plot
    # Using bar instead of hist to avoid interpolation
    print("labels", names)
    print("values", sizes)
    plt.bar(names, sizes, width=1, align='center')

    # Customize the plot
    plt.title(f"Size distribution of {series_name} dataset")
    plt.xlabel("Sample")
    plt.ylabel("File Size")
    plt.grid(True, axis='y', alpha=0.7)
    plt.yscale("log", base=2)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    # Set custom y-axis formatter
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(human_readable_formatter))

    # Save the plot
    save_plot(save_path)

def get_rule_fp_bar(box_plot_set, series_name="Generic", save_path=None):
    fp_global = []
    fp_small = []
    fp_medium = []
    fp_large = []

    fp_global_good = []

    label_algorithm = []

    width = 0.2

    def average(list):
        return sum(list) / len(list)

    for algorithm, dataset in box_plot_set.items(): # we just need this to get the list of metrics
        fp_global.append(average(dataset['FP Labeled Global (malware)']))
        fp_small.append(average(dataset['FP Labeled Small (malware)']))
        fp_medium.append(average(dataset['FP Labeled Medium (malware)']))
        fp_large.append(average(dataset['FP Labeled Large (malware)']))
        fp_global_good.append(average(dataset['FP Labeled Global (benign)']))
        label_algorithm.append(algorithm)

    # Set up the plot
    setup_plot_style()

    # malicious bar graph
    plt.figure(figsize=(12, 6), dpi=300)

    x = np.arange(len(label_algorithm))
    plt.bar(x-width*0.75, fp_small, width=width*0.5)
    plt.bar(x-width*0.25, fp_medium, width=width*0.5)
    plt.bar(x+width*0.25, fp_large, width=width*0.5)
    plt.bar(x+width*0.75, fp_global, width=width*0.5)

    # Customize the plot
    plt.title(f"Malicious FP: {series_name}")
    plt.xlabel("Samples")
    plt.ylabel("Average FP")
    plt.grid(True, axis='y', alpha=0.7)
    plt.xticks(x, label_algorithm)
    plt.legend(["Small", "Medium", "Large", "Global Malware"])

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    # Save the plot
    save_plot(save_path + " Malicious")

    # benign bar graph
    plt.figure(figsize=(12, 6), dpi=300)

    x = np.arange(len(label_algorithm))
    plt.bar(x, fp_global_good, width=width)

    # Customize the plot
    plt.title(f"Benign FP: {series_name}")
    plt.xlabel("Samples")
    plt.ylabel("Average FP")
    plt.grid(True, axis='y', alpha=0.7)
    plt.xticks(x, label_algorithm)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    # Save the plot
    save_plot(save_path + " Benign")

def get_global_clusters_average_size(directory_path, save_path=None):
    # Get all directory names
    directories = os.listdir(directory_path)

    # For each cluster's average size box plot
    cluster_index = []
    size_dataset = []

    # For average file size per cluster

    for dir_name in directories:
        # Pattern matches "ClusterN_SizeX" and captures X
        match = re.match(r'Cluster\d+_Size(\d+)', dir_name)
        if match:
            index = match.group(0)
            cluster_index.append(str(index))

        file_sizes = []
        directory_files_path = os.path.join(directory_path, dir_name)
        directory_files = os.listdir(directory_files_path)
        for file in directory_files:
            size = os.path.getsize(os.path.join(directory_files_path, file))
            # file_sizes.append(size)
            size_dataset.append(size)

        # size_dataset.append(file_sizes)

    # Set up the plot
    setup_plot_style()
    plt.figure(figsize=(12, 6), dpi=300)

    # Create box plots
    plt.boxplot(
        size_dataset,
        # tick_labels=cluster_index,
    )

    # Customize the plot
    plt.title("Average File Size per Cluster")
    plt.xlabel("Cluster Index")
    plt.ylabel("File Size")
    plt.grid(True, axis='y', alpha=0.7)
    plt.yscale("log", base=2)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    # Set custom y-axis formatter
    ax = plt.gca()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(human_readable_formatter))

    # Save the plot
    save_plot(save_path)

def get_clusters_histogram(directory_path, save_path=None):
    # Get all directory names
    directories = os.listdir(directory_path)

    # For frequency histogram
    size_counts = {}
    bin_keys = []

    # For average file size per cluster

    for dir_name in directories:
        # Pattern matches "ClusterN_SizeX" and captures X
        match = re.match(r'Cluster\d+_Size(\d+)', dir_name)
        if match:
            size = int(match.group(1))
            if not str(size) in size_counts:
                size_counts[str(size)] = 0
                bin_keys.append(size)
            size_counts[str(size)] += 1

    # Sort sizes and counts for plotting
    # Converting to sorted lists to ensure proper ordering
    labels = [str(key) for key in sorted(bin_keys)]  # Sizes for x-axis
    frequencies = [size_counts[str(size)] for size in sorted(bin_keys)]  # Frequencies for y-axis

    # Set up the plot
    setup_plot_style()
    plt.figure(figsize=(12, 6), dpi=300)

    # Create the bar plot
    # Using bar instead of hist to avoid interpolation
    print("labels", labels)
    print("frequencies", frequencies)
    bars = plt.bar(labels, frequencies, width=1, align='center')

    # Customize the plot
    plt.title("Distribution of Cluster Sizes")
    plt.xlabel("Cluster Size")
    plt.ylabel("Frequency")
    plt.grid(True, axis='y', alpha=0.7)

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height,
                f'{height}',
                ha='center', va='bottom')

    # Rotate x-axis labels for better readability
    # plt.xticks(rotation=90)

    # Save the plot
    save_plot(save_path)

def normalize_number_list(list, min_val, max_val):
    if not list:
        return []

    # Avoid division by zero if all numbers are the same
    if max_val == min_val:
        return [50] * len(list)  # Or another default value

    return [((x - min_val) / (max_val - min_val)) * 100 for x in list]

def plot_yara_metrics(box_plot_set, targeted_metric="TP", save_path=None, series_name="Generic", yscale="linear", file_count=0, measure_fp=False):
    if not measure_fp and re.match("FP Label", targeted_metric):
        return

    setup_plot_style()

    # Set up the plot with higher DPI for better quality
    plt.figure(figsize=(12, 6), dpi=300)

    box_plot_data = []
    for algorithm, data in box_plot_set.items():
        box_plot_data.append(
            normalize_number_list(
                data[targeted_metric],
                0,
                file_count
            ) if targeted_metric == "TP" else data[targeted_metric]
        )

    # Create box plots
    plt.boxplot(
        box_plot_data,
        tick_labels=list(box_plot_set.keys()),
    )

    # Customize the plot
    if yscale == "log2":
        plt.yscale("log", base=2)

        ticks = [1, 8, 16, 32, 64, 128, 256, 512, 1024]
        plt.yticks(ticks, [str(i) for i in ticks])

    #if targeted_metric == "TP":
        #plt.ylim(0, 105)

    plt.title(f"YARA Rules {targeted_metric} Distribution ({series_name} dataset)", pad=20)
    plt.ylabel("TP % Coverage" if targeted_metric == "TP" else "Execution Time (s)" if targeted_metric == "Execution Time" else targeted_metric)
    plt.grid(True, axis='y', alpha=0.7)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    save_plot(save_path)

def plot_yara_metrics_bar(box_plot_set, targeted_metric="TP", save_path=None, series_name="Generic", yscale="linear", file_count=0, measure_fp=False):
    if not measure_fp and re.match("FP Label", targeted_metric):
        return

    setup_plot_style()

    # Set up the plot with higher DPI for better quality
    plt.figure(figsize=(12, 6), dpi=300)

    box_plot_data = []
    for algorithm, data in box_plot_set.items():
        value_list = normalize_number_list(
                data[targeted_metric],
                0,
                file_count
            ) if targeted_metric == "TP" else data[targeted_metric]

        box_plot_data.append(sum(value_list) / len(value_list))

    # Create box plots
    plt.bar(
        box_plot_set.keys(), box_plot_data,
    )

    # Customize the plot
    if yscale == "log2":
        plt.yscale("log", base=2)
        plt.yticks([1, 8, 16, 32, 64, 128, 256, 512, 1024])

    #if targeted_metric == "TP":
        #plt.ylim(0, 105)

    plt.title(f"YARA Rules {targeted_metric} Distribution ({series_name} dataset)", pad=20)
    plt.ylabel("TP % Coverage" if targeted_metric == "TP" else targeted_metric)
    plt.grid(True, axis='y', alpha=0.7)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)

    save_plot(save_path)



def generate_fullscale_plots(box_plot_set, series_name, file_count, container_directory="graphs", measure_fp=False):
    get_directory_size_histogram(
        get_project_path("input_testing", "malicious", "output_preprocessed", series_name),
        series_name=series_name,
        save_path=get_project_path("output", container_directory, series_name, f"Directory Size"),
    )

    if measure_fp:
        get_rule_fp_bar(
            box_plot_set,
            series_name=series_name,
            save_path=get_project_path("output", container_directory, series_name, f"FP Bar"),
        )

    for algorithm, dataset in box_plot_set.items(): # we just need this to get the list of metrics
        for metric, list in dataset.items():
            plot_yara_metrics(
                box_plot_set,
                targeted_metric=metric,
                save_path=get_project_path("output", container_directory, series_name, f"{metric}"),
                series_name=series_name,
                yscale='log2' if metric == "Gram Size" else 'linear',
                file_count=file_count,
                measure_fp=measure_fp,
            )
        break