import jpype
import jpype.imports
import atexit
import gc
import os


def get_repo_paths():
    """
    Calculate paths to both repositories based on current file location.
    Assumes both repos are in the Desktop directory.
    """
    # Get the current file's directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Navigate up to the Desktop directory (adjust if your structure is different)
    while not os.path.basename(current_dir) == "Desktop":
        current_dir = os.path.dirname(current_dir)

    # Define paths to both repositories
    PYTHON_REPO = os.path.join(current_dir, "github-mlsec-python")
    JAVA_REPO = os.path.join(current_dir, "github-mlsec-java")

    return PYTHON_REPO, JAVA_REPO


class PythonInterface:
    _jvm_started = False
    PYTHON_REPO, JAVA_REPO = get_repo_paths()

    @classmethod
    def _start_jvm(cls):
        if not cls._jvm_started:
            jvm_options = [
                "-Xmx14g",
                "-XX:+HeapDumpOnOutOfMemoryError",
                "-XX:HeapDumpPath=src/python/heapdump",
            ]

            # Use the JAVA_REPO path to locate the jar file
            classpath = [os.path.join(
                cls.JAVA_REPO,
                "CapyMOASec/target/AutoYara-1.0-SNAPSHOT.jar"
            )]

            jpype.startJVM(
                classpath=classpath,
                convertStrings=True, *jvm_options)
            cls._jvm_started = True
            atexit.register(cls._shutdown_jvm)

            print("JVM Started")
            cls.print_memory_usage(cls)

    @classmethod
    def _shutdown_jvm(cls):
        if cls._jvm_started and jpype.isJVMStarted():
            jpype.shutdownJVM()
            cls._jvm_started = False

    def __init__(self):
        self._start_jvm()

    def print_memory_usage(self, label="Memory"):
        memory_monitor = jpype.JClass("edu.lps.acs.ml.autoyara.MemoryMonitor")
        used_memory = memory_monitor.getUsedMemory() / (1024 * 1024)  # Convert to MB
        free_memory = memory_monitor.getFreeMemory() / (1024 * 1024)  # Convert to MB
        total_memory = memory_monitor.getTotalMemory() / (1024 * 1024)  # Convert to MB
        max_memory = memory_monitor.getMaxMemory() / (1024 * 1024)  # Convert to MB
        print(f"{label}")
        print(f"\tUsed Memory: {used_memory:.2f} MB")
        print(f"\tFree Memory: {free_memory:.2f} MB")
        print(f"\tTotal Memory: {total_memory:.2f} MB")
        print(f"\tMax Memory: {max_memory:.2f} MB")

    def reset_memory(self):
        # after we run a yara method through java, sometimes the java virtual machine
        # has excess memory allocated, we call this after every operation to
        # avoid the heap overflowing
        gc.collect()
        jpype.java.lang.System.gc()

    @classmethod
    def get_python_repo_path(cls, *paths):
        """Helper method to get paths in the Python repository"""
        return os.path.join(cls.PYTHON_REPO, *paths)

    @classmethod
    def get_java_repo_path(cls, *paths):
        """Helper method to get paths in the Java repository"""
        return os.path.join(cls.JAVA_REPO, *paths)