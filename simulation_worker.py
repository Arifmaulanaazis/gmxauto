import os
import time
import logging
import subprocess

from PyQt6.QtCore import QObject, pyqtSignal, QRunnable

from environment_manager import EnvironmentManager
from mdp_file_manager import MDPFileManager
from command_runner import CommandRunner
from gpu_command_builder import GPUCommandBuilder

class WorkerSignals(QObject):
    progress = pyqtSignal(int, str)  # progress percent, step name
    log = pyqtSignal(str, str)       # level, message
    step_finished = pyqtSignal(str)  # step name
    finished = pyqtSignal()

class SimulationWorker(QRunnable):
    def __init__(self, workdir, num_gpus, num_cores, duration, unit, engine):
        super().__init__()
        self.workdir = workdir
        self.num_gpus = num_gpus
        self.num_cores = num_cores
        self.duration = duration
        self.unit = unit
        self.engine = engine
        self.signals = WorkerSignals()
        self.logger = logging.getLogger("SimulationHelper")
        self._is_interrupted = False

    def interrupt(self):
        self._is_interrupted = True

    def calculate_nsteps(self, timestep_ps: float) -> int:
        if self.unit == "ns":
            total_ps = self.duration * 1000
        elif self.unit == "ps":
            total_ps = self.duration
        else:
            self.signals.log.emit("ERROR", "❌ Invalid time unit. Use 'ns' or 'ps'")
            self.logger.error(f"Invalid time unit: {self.unit}")
            raise ValueError("Invalid time unit")

        nsteps = int(total_ps / timestep_ps)

        nsteps_mdp = MDPFileManager.read_nsteps("step5_production.mdp")
        if nsteps_mdp is None or int(nsteps) != int(nsteps_mdp):
            MDPFileManager.write_nsteps("step5_production.mdp", nsteps)

        self.signals.log.emit("INFO", f"⏳ Duration {self.duration}{self.unit} → dt = {timestep_ps} ps → nsteps = {nsteps}")
        self.logger.info(f"Duration {self.duration}{self.unit} → dt = {timestep_ps} ps → nsteps = {nsteps}")

        return nsteps

    def check_file_exists(self, file_path: str, step_name: str):
        if os.path.exists(file_path):
            self.signals.log.emit("SUCCESS", f"✅ {file_path} successfully created at {step_name}")
            self.logger.info(f"File {file_path} found after {step_name}")
        else:
            self.signals.log.emit("ERROR", f"❌ {file_path} not found after {step_name}")
            self.logger.error(f"File {file_path} not found after {step_name}")
            raise FileNotFoundError(f"{file_path} not found after {step_name}")

    def run_command(self, command, step_name):
        self.signals.log.emit("COMMAND", f"$ {command}")
        if self._is_interrupted:
            self.signals.log.emit("WARNING", f"⚠️ Step {step_name} cancelled before start.")
            raise RuntimeError(f"Step {step_name} cancelled.")
        try:
            CommandRunner.run_command(command)
            self.signals.log.emit("SUCCESS", f"✅ Success: {step_name}")
            self.logger.info(f"Step {step_name} completed successfully")
        except subprocess.CalledProcessError as e:
            self.signals.log.emit("ERROR", f"❌ Failed {step_name}: {e.stderr if e.stderr else str(e)}")
            self.logger.error(f"Step {step_name} failed: {e.stderr if e.stderr else str(e)}")
            raise

    def run_mdrun_with_progress(self, command, step_name):
        self.signals.log.emit("COMMAND", f"$ {command}")

        def update_progress(val):
            self.signals.progress.emit(int(val), step_name)

        def update_log():
            pass

        def check_interrupted():
            return self._is_interrupted

        try:
            CommandRunner.run_mdrun_with_progress(command, step_name, update_progress, update_log, check_interrupted)
            self.signals.progress.emit(100, step_name)
            self.signals.log.emit("SUCCESS", f"✅ Success: {step_name}")
            self.logger.info(f"Step {step_name} completed successfully")
        except subprocess.CalledProcessError as e:
            self.signals.log.emit("ERROR", f"❌ Failed {step_name}: {e.stderr if e.stderr else str(e)}")
            self.logger.error(f"Step {step_name} failed: {e.stderr if e.stderr else str(e)}")
            raise
        except RuntimeError as e:
            self.signals.log.emit("WARNING", f"⚠️ {str(e)}")
            self.logger.warning(str(e))
            raise

    def run(self):
        try:
            os.chdir(self.workdir)
            self.signals.log.emit("INFO", f"📂 Changed working directory to: {self.workdir}")
            self.logger.info(f"Changed directory to: {self.workdir}")

            env_manager = EnvironmentManager(self.num_gpus, self.engine)
            env_manager.setup()
            gpu_ids = env_manager.gpu_ids

            checkpoint_exists = os.path.exists("step5_1.cpt")
            if checkpoint_exists:
                self.signals.log.emit("WARNING", "⚠️ Checkpoint found, skipping Steps 1-5...")
                self.logger.info("Checkpoint found, skipping Steps 1-5")

                skipped_steps = [
                    (1, "Step 1: Preprocessing Minimization", "step4.0_minimization.tpr"),
                    (2, "Step 2: Minimization", "step4.0_minimization.gro"),
                    (3, "Step 3: Preprocessing Equilibration", "step4.1_equilibration.tpr"),
                    (4, "Step 4: Equilibration", "step4.1_equilibration.gro"),
                    (5, "Step 5: Preprocessing Production", "step5_1.tpr"),
                ]
                for step_num, step_name, check_file in skipped_steps:
                    if self._is_interrupted:
                        self.signals.log.emit("WARNING", "⚠️ Simulation cancelled by user.")
                        self.logger.warning("Simulation cancelled by user.")
                        self.signals.finished.emit()
                        return
                    self.signals.progress.emit(100, step_name)
                    self.signals.log.emit("SUCCESS", f"✅ Success: {step_name} (skipped due to checkpoint)")
                    if not os.path.exists(check_file):
                        self.signals.log.emit("WARNING", f"⚠️ File {check_file} not found after {step_name} (skipped)")
                        self.logger.warning(f"File {check_file} not found after {step_name} (skipped)")
                    time.sleep(0.1)

            else:
                # Step 1
                step_name = "Step 1: Preprocessing Minimization"
                if self._is_interrupted: raise RuntimeError("Simulation cancelled by user.")
                cmd1 = ("gmx grompp -f step4.0_minimization.mdp -o step4.0_minimization.tpr "
                        "-c step3_input.gro -r step3_input.gro -p topol.top -n index.ndx -maxwarn 1")
                self.run_command(cmd1, step_name)
                self.check_file_exists("step4.0_minimization.tpr", step_name)
                self.signals.progress.emit(100, step_name)

                # Step 2
                step_name = "Step 2: Minimization"
                if self._is_interrupted: raise RuntimeError("Simulation cancelled by user.")
                cmd2 = GPUCommandBuilder.build(
                    f"gmx mdrun -v -deffnm step4.0_minimization",
                    self.num_gpus, self.num_cores, gpu_ids, self.engine
                )
                self.run_mdrun_with_progress(cmd2, step_name)
                self.check_file_exists("step4.0_minimization.gro", step_name)

                # Step 3
                step_name = "Step 3: Preprocessing Equilibration"
                if self._is_interrupted: raise RuntimeError("Simulation cancelled by user.")
                cmd3 = ("gmx grompp -f step4.1_equilibration.mdp -o step4.1_equilibration.tpr "
                        "-c step4.0_minimization.gro -r step3_input.gro -p topol.top -n index.ndx -maxwarn 1")
                self.run_command(cmd3, step_name)
                self.check_file_exists("step4.1_equilibration.tpr", step_name)
                self.signals.progress.emit(100, step_name)

                # Step 4
                step_name = "Step 4: Equilibration"
                if self._is_interrupted: raise RuntimeError("Simulation cancelled by user.")
                cmd4 = GPUCommandBuilder.build(
                    f"gmx mdrun -v -deffnm step4.1_equilibration",
                    self.num_gpus, self.num_cores, gpu_ids, self.engine
                )
                self.run_mdrun_with_progress(cmd4, step_name)
                self.check_file_exists("step4.1_equilibration.gro", step_name)

                # Step 5
                step_name = "Step 5: Preprocessing Production"
                if self._is_interrupted: raise RuntimeError("Simulation cancelled by user.")
                cmd5 = ("gmx grompp -f step5_production.mdp -o step5_1.tpr -c step4.1_equilibration.gro "
                        "-p topol.top -n index.ndx")
                self.run_command(cmd5, step_name)
                self.check_file_exists("step5_1.tpr", step_name)
                self.signals.progress.emit(100, step_name)

            # Step 6 Production
            step_name = "Step 6: Production"
            if self._is_interrupted: raise RuntimeError("Simulation cancelled by user.")
            timestep = MDPFileManager.extract_dt("step5_production.mdp")
            nstlist = MDPFileManager.extract_and_replace_nstlist("step5_production.mdp", 300)
            nsteps = self.calculate_nsteps(timestep)

            if os.path.exists("step5_1.cpt"):
                self.signals.log.emit("WARNING", "⚠️ Detected checkpoint (step5_1.cpt), resuming simulation...")
                self.logger.info("Checkpoint found, resuming production simulation")
                if self.engine == "CPU":
                    cmd6 = GPUCommandBuilder.build(
                        (f"gmx mdrun -v -deffnm step5_1 -cpi step5_1.cpt -append"),
                        self.num_gpus, self.num_cores, gpu_ids, self.engine,
                        extra_flags=f"-resetstep 90000 -nstlist {nstlist} -nsteps {nsteps}"
                    )
                else:
                    cmd6 = GPUCommandBuilder.build(
                        (f"gmx mdrun -v -deffnm step5_1 -cpi step5_1.cpt -append -nb gpu -bonded gpu"),
                        self.num_gpus, self.num_cores, gpu_ids, self.engine,
                        extra_flags=f"-resetstep 90000 -nstlist {nstlist} -nsteps {nsteps}"
                    )
            else:
                if self.engine == "CPU":
                    cmd6 = GPUCommandBuilder.build(
                        (f"gmx mdrun -v -deffnm step5_1"),
                        self.num_gpus, self.num_cores, gpu_ids, self.engine,
                        extra_flags=f"-resetstep 90000 -nstlist {nstlist} -nsteps {nsteps}"
                    )
                else:
                    cmd6 = GPUCommandBuilder.build(
                        (f"gmx mdrun -v -deffnm step5_1 -nb gpu -bonded gpu"),
                        self.num_gpus, self.num_cores, gpu_ids, self.engine,
                        extra_flags=f"-resetstep 90000 -nstlist {nstlist} -nsteps {nsteps}"
                    )
            self.run_mdrun_with_progress(cmd6, step_name)
            self.check_file_exists("step5_1.gro", step_name)
            self.signals.progress.emit(100, step_name)

            self.signals.log.emit("INFO", "🎉 Simulation completed. All steps succeeded!")
            self.logger.info("Simulation completed with all steps successful")
            self.signals.finished.emit()

        except Exception as e:
            self.signals.log.emit("ERROR", f"❌ Error: {str(e)}")
            self.logger.error(f"Error: {str(e)}")
            self.signals.finished.emit()
