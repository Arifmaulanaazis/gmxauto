import logging

class GPUCommandBuilder:
    logger = logging.getLogger("GPUCommandBuilder")

    @staticmethod
    def build(base_cmd: str, num_gpus: int, num_cores: int, gpu_ids: str, engine: str, extra_flags: str = "") -> str:
        GPUCommandBuilder.logger.debug("🛠️ Building command according to engine")
        if engine == "CPU":
            # For CPU, no GPU flags, only -nt for number of cores
            cmd = f"{base_cmd} -nt {num_cores} {extra_flags}".strip()
        else:
            # CUDA GPU engine as before
            if num_gpus == 1:
                if "step4.0" in base_cmd:
                    cmd = f"{base_cmd} -gpu_id {gpu_ids} -pin on -pinoffset 0 -pinstride 1 {extra_flags}".strip()
                elif "step4.1" in base_cmd:
                    cmd = f"{base_cmd} -gpu_id {gpu_ids} -nb gpu -bonded gpu -pin on -pinoffset 0 -pinstride 1 {extra_flags}".strip()
                else:
                    cmd = f"{base_cmd} -gpu_id {gpu_ids} -pme gpu -pin on -pinoffset 0 -pinstride 1 -pmefft gpu {extra_flags}".strip()
            else:
                ntomp = num_cores/num_gpus
                if "step4.0" in base_cmd:
                    cmd = f"{base_cmd} -gpu_id {gpu_ids} -nb gpu -pin on -pinoffset 0 -pinstride 1 -npme 1 -ntmpi {num_gpus} -ntomp {int(ntomp)} {extra_flags}".strip()
                elif "step4.1" in base_cmd:
                    cmd = f"{base_cmd} -gpu_id {gpu_ids} -nb gpu -bonded gpu -pme gpu -pin on -pinoffset 0 -pinstride 1 -npme 1 -ntmpi {num_gpus} -ntomp {int(ntomp)} {extra_flags}".strip()
                else:
                    cmd = f"{base_cmd} -gpu_id {gpu_ids} -pme gpu -pin on -pinoffset 0 -pinstride 1 -npme 1 -ntmpi {num_gpus} -ntomp {int(ntomp)} -pmefft gpu {extra_flags}".strip()
        GPUCommandBuilder.logger.info(f"🔧 Command built: {cmd}")
        return cmd
