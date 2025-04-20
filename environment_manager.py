import os
import logging

class EnvironmentManager:
    def __init__(self, num_gpus: int, engine: str):
        self.num_gpus = num_gpus
        self.engine = engine  # "CUDA" or "CPU"
        self.gpu_ids = ",".join(str(i) for i in range(num_gpus)) if num_gpus > 0 else ""
        self.logger = logging.getLogger("EnvironmentManager")
    
    def setup(self):
        self.logger.debug("🔧 Setting environment variables")
        script_dir = os.path.dirname(os.path.realpath(__file__))
        if self.engine == "CUDA":
            gmx_folder = os.path.join(script_dir, "gmx")  # CUDA folder
            # Set environment variables for CUDA GPU
            os.environ["CUDA_VISIBLE_DEVICES"] = self.gpu_ids
            os.environ["GMX_ENABLE_DIRECT_GPU_COMM"] = "true"
            os.environ["GMX_GPU_DD_COMMS"] = "true"
            os.environ["GMX_GPU_PME_PP_COMMS"] = "true"
            os.environ["GMX_FORCE_UPDATE_DEFAULT_GPU"] = "true"
            os.environ["GMX_CUDA_STREAMS"] = "1"
            os.environ["GMX_USE_GPU_BUFFER_OPS"] = "true"
            os.environ["GMX_PIN_VERLET_BUFFER"] = "true"
            os.environ["GMX_CUDA_GRAPH"] = "1"
            self.logger.info(f"🖥️ CUDA environment configured with GPU IDs: {self.gpu_ids}")
        else:
            gmx_folder = os.path.join(script_dir, "gmx_cpu")  # CPU folder
            # Remove GPU environment variables if any
            for var in ["CUDA_VISIBLE_DEVICES", "GMX_ENABLE_DIRECT_GPU_COMM", "GMX_GPU_DD_COMMS",
                        "GMX_GPU_PME_PP_COMMS", "GMX_FORCE_UPDATE_DEFAULT_GPU", "GMX_CUDA_STREAMS",
                        "GMX_USE_GPU_BUFFER_OPS", "GMX_PIN_VERLET_BUFFER", "GMX_CUDA_GRAPH"]:
                os.environ.pop(var, None)
            self.logger.info("🖥️ Configured for GROMACS CPU without CUDA")

        os.environ["PATH"] = os.path.join(gmx_folder, "bin") + os.pathsep + os.environ.get("PATH", "")
        os.environ["GMXDATA"] = os.path.join(gmx_folder, "share", "gromacs")
        
        self.logger.info(f"📂 PATH and GMXDATA set from folder: {gmx_folder}")
