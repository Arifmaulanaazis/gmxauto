title: 'gmxauto: A GUI Tool for Automating GROMACS Molecular Dynamics Simulations on Windows'
tags:
  - python
  - pyqt6
  - gromacs
  - molecular dynamics
  - computational chemistry
  - gpu
  - simulation
authors:
  - name: Arif Maulana Azis
    orcid: 0000-0001-8216-9309
    affiliation: 1
affiliations:
  - name: Independent Researcher
    index: 1
date: 2025-04-20
---

# Summary

**gmxauto** is a Python-based graphical user interface (GUI) designed to automate the execution of molecular dynamics (MD) simulations using GROMACS 2025.1 on Windows systems. Built with PyQt6, it offers a streamlined workflow for researchers working with biomolecular systems prepared via CHARMM-GUI. gmxauto is especially suitable for those utilizing GPU-accelerated simulations through CUDA, offering both automation and monitoring features to enhance user productivity.

This software simplifies the multi-step GROMACS workflow—including energy minimization, equilibration, and production MD—into an accessible interface, with built-in logging, checkpoint recovery, and performance optimization. gmxauto is intended for researchers in computational chemistry, structural biology, and biophysics, particularly those running simulations on local Windows machines.

# Statement of Need

While GROMACS is a powerful and widely-used engine for molecular dynamics, its command-line interface can present a barrier to entry for new users or those unfamiliar with scripting. Furthermore, GROMACS GUI tools are primarily Linux-based, with limited or no support for Windows users.

**gmxauto** fills this gap by providing:
- A fully-featured Windows GUI for GROMACS users.
- Integrated automation for common simulation workflows based on CHARMM-GUI inputs.
- GPU and CPU configuration with CUDA-aware setup options.
- Live progress feedback, logging, and automatic restart from checkpoints.

This makes **gmxauto** a valuable tool for educational use, prototyping, or small-scale molecular simulations, where accessibility and ease-of-use are essential.

# Installation

To install and run gmxauto, the following steps are required:

```bash
git clone https://github.com/Arifmaulanaazis/gmxauto.git
cd gmxauto
pip install pyqt6
python main.py
```

For GPU support, users must install the CUDA Toolkit (12.0+) and a compatible NVIDIA driver (535+). GROMACS 2025.1 prebuilt binaries for Windows (including CUDA support) are recommended and provided via a companion repository:
[https://github.com/Arifmaulanaazis/Gromacs-2025.1-Prebuild-Windows](https://github.com/Arifmaulanaazis/Gromacs-2025.1-Prebuild-Windows)

# Usage

Users begin by preparing simulation input files using CHARMM-GUI, which are then loaded into gmxauto. The user can select hardware settings (CPU/GPU), set simulation duration, and execute the full MD pipeline via a single interface. All relevant output (logs, checkpoints, trajectories) is saved to a structured output directory.

Typical workflow:
1. Load CHARMM-GUI-prepared files (.gro, .top, .mdp)
2. Choose simulation backend (CPU or CUDA GPU)
3. Run MD steps sequentially: energy minimization, equilibration, production
4. Analyze outputs using VMD, PyMOL, or MDAnalysis

# Acknowledgements

This project makes use of the following open-source software:
- [GROMACS](https://www.gromacs.org/)
- [CHARMM-GUI](https://www.charmm-gui.org/)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)

# References

Please refer to `paper.bib` for all citation references.