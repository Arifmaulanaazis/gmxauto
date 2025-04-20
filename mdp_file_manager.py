import os
import re
import logging

class MDPFileManager:
    logger = logging.getLogger("MDPFileManager")

    @staticmethod
    def read_nsteps(file_path: str) -> int:
        MDPFileManager.logger.debug(f"📖 Reading nsteps from file: {file_path}")
        if not os.path.exists(file_path):
            MDPFileManager.logger.warning(f"⚠️ File {file_path} not found")
            return None
        with open(file_path, 'r') as file:
            for line in file:
                if line.strip().startswith('nsteps'):
                    _, value = line.split('=', 1)
                    nsteps = int(value.strip())
                    MDPFileManager.logger.info(f"✅ nsteps found: {nsteps}")
                    return nsteps
        MDPFileManager.logger.warning(f"⚠️ nsteps not found in {file_path}")
        return None

    @staticmethod
    def write_nsteps(file_path: str, new_value: int) -> None:
        MDPFileManager.logger.debug(f"✍️ Writing nsteps={new_value} to file: {file_path}")
        if not os.path.exists(file_path):
            MDPFileManager.logger.warning(f"⚠️ File {file_path} not found")
            return
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        nsteps_found = False
        for i, line in enumerate(lines):
            if line.strip().startswith('nsteps'):
                key, _ = line.split('=', 1)
                lines[i] = f"{key.rstrip()}                  = {new_value}\n"
                nsteps_found = True
                break

        if not nsteps_found:
            lines.append(f"nsteps                  = {new_value}\n")
            MDPFileManager.logger.info("ℹ️ nsteps not found, appended at end of file")

        with open(file_path, 'w') as file:
            file.writelines(lines)
        MDPFileManager.logger.info(f"✅ nsteps successfully written: {new_value}")
    
    @staticmethod
    def extract_dt(mdp_path: str) -> float:
        MDPFileManager.logger.debug(f"🔍 Extracting dt from: {mdp_path}")
        if not os.path.exists(mdp_path):
            MDPFileManager.logger.warning(f"⚠️ {mdp_path} not found, using default dt=0.004")
            return 0.004

        with open(mdp_path, 'r') as f:
            content = f.read()
        match = re.search(r'^\s*dt\s*=\s*([0-9.eE+-]+)', content, re.MULTILINE)
        if match:
            dt_val = float(match.group(1))
            MDPFileManager.logger.info(f"✅ dt found: {dt_val}")
            return dt_val
        else:
            MDPFileManager.logger.warning("⚠️ dt not found, using default dt=0.004")
            return 0.004
        
    @staticmethod
    def extract_and_replace_nstlist(mdp_path: str, nstlist: int) -> int:
        MDPFileManager.logger.debug(f"🔍 Extracting and replacing nstlist in: {mdp_path}")
        if not os.path.exists(mdp_path):
            MDPFileManager.logger.warning(f"⚠️ {mdp_path} not found, using default nstlist=300")
            return 300

        with open(mdp_path, 'r') as file:
            lines = file.readlines()
        
        nstlist_found = False
        for i, line in enumerate(lines):
            if line.strip().startswith('nstlist'):
                key, _ = line.split('=', 1)
                lines[i] = f"{key.rstrip()}                 = {nstlist}\n"
                nstlist_found = True
                break

        if not nstlist_found:
            lines.append(f"nstlist                 = {nstlist}\n")
            MDPFileManager.logger.info("ℹ️ 'nstlist' not found in MDP, appended default nstlist=300 at end")

        with open(mdp_path, 'w') as file:
            file.writelines(lines)
        MDPFileManager.logger.info(f"✅ nstlist successfully written: {nstlist}")
        return nstlist
