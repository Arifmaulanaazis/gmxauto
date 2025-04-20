import subprocess
import shlex
import time
import re
import logging
from mdp_file_manager import MDPFileManager

class CommandRunner:
    logger = logging.getLogger("CommandRunner")

    @staticmethod
    def run_command(command: str):
        CommandRunner.logger.debug(f"💻 Running command: {command}")
        result = subprocess.run(command, shell=True, check=True, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result

    @staticmethod
    def run_mdrun_with_progress(command: str, step_name: str, update_progress_callback, update_log_callback, check_interrupted_callback=None):
        CommandRunner.logger.debug(f"🚀 Running mdrun with progress: {command}")
        safe_name = step_name.replace(" ", "_").replace(":", "")
        log_file = f"progress_{safe_name}.log"
        output_file = f"output_{safe_name}.txt"
        
        total_nsteps = None
        if "step4.0" in command:
            total_nsteps = MDPFileManager.read_nsteps("step4.0_minimization.mdp")
        elif "step4.1" in command:
            total_nsteps = MDPFileManager.read_nsteps("step4.1_equilibration.mdp")
        elif "step5_1" in command or "step5_production" in command:
            total_nsteps = MDPFileManager.read_nsteps("step5_production.mdp")
        
        if not total_nsteps:
            raise RuntimeError(f"❌ nsteps not found for {step_name}")
        
        if "-deffnm" in command:
            cmd_parts = shlex.split(command)
            for i, part in enumerate(cmd_parts):
                if part == "-deffnm" and i + 1 < len(cmd_parts):
                    deffnm = cmd_parts[i + 1]
                    log_file = f"{deffnm}.log"
                    break
        
        if "-g" not in command:
            command = f"{command} -g {log_file}"

        with open(output_file, 'w') as f:
            process = subprocess.Popen(
                shlex.split(command),
                stdout=f,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        
        current = 0
        last_step = 0
        while process.poll() is None:
            if check_interrupted_callback and check_interrupted_callback():
                process.terminate()
                CommandRunner.logger.info(f"⚠️ Process {step_name} terminated by user.")
                raise RuntimeError(f"Simulation {step_name} terminated by user.")

            with open(output_file, 'r') as f_read:
                data = f_read.read()
                for line in data.splitlines():
                    if "step" in line.lower():
                        if "step4.0" in command:
                            match = re.search(r"(?<!\S)step=\s*(\d+)", line, re.IGNORECASE)
                        else:
                            match = re.search(r"(?<!\S)(steps?\s*=\s*|step\s*)(\d+)", line, re.IGNORECASE)

                        if match:
                            step_val = int(match.group(1) if "step4.0" in command else match.group(2))
                            if step_val >= last_step:
                                current = step_val
                                last_step = step_val

                                progress_percent = min((current / total_nsteps) * 100, 99.9)
                                update_progress_callback(progress_percent)
                                CommandRunner.logger.info(
                                    f"⏳ {step_name} | Step {current}/{total_nsteps} | Progress: {progress_percent:.2f}%"
                                )
            update_log_callback()
            time.sleep(0.3)

        update_progress_callback(100)
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
