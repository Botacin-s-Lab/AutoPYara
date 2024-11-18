import jpype
import jpype.imports
import atexit
import gc

class PythonInterface:
    _jvm_started = False

    @classmethod
    def _start_jvm(cls):
        if not cls._jvm_started:
            jvm_options = [
                "-Xmx14g",
                "-XX:+HeapDumpOnOutOfMemoryError",
                "-XX:HeapDumpPath=src/python/heapdump",
            ]
            jpype.startJVM(
                classpath=["/home/vboxuser/Desktop/github-mlsec-java/CapyMOASec/target/AutoYara-1.0-SNAPSHOT.jar"],
                convertStrings=True, *jvm_options)
            cls._jvm_started = True
            atexit.register(cls._shutdown_jvm)

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