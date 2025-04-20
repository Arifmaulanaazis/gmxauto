import os
import sys
import base64
import time
import logging

from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QComboBox, QFileDialog, QTextEdit, QProgressBar,
    QFrame, QGridLayout
)
from PyQt6.QtGui import QIcon, QColor, QTextCursor, QPixmap
from PyQt6.QtCore import Qt, QByteArray, QBuffer, QIODevice

from simulation_worker import SimulationWorker
from gambar import ICONAPP
from environment_manager import EnvironmentManager
from mdp_file_manager import MDPFileManager
from command_runner import CommandRunner
from gpu_command_builder import GPUCommandBuilder

from PyQt6.QtCore import QObject, pyqtSignal, QThreadPool

# Logger signal for GUI log updates
class LogSignal(QObject):
    new_log = pyqtSignal(str, str)  # level, message

log_signal = LogSignal()

class QtHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        level = record.levelname
        log_signal.new_log.emit(level, msg)

log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="[%X]")
qt_handler = QtHandler()
qt_handler.setFormatter(log_formatter)

for logger_name in ["EnvironmentManager", "MDPFileManager", "CommandRunner", "GPUCommandBuilder", "SimulationHelper"]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(qt_handler)
    logger.addHandler(logging.FileHandler("gmxauto.log", mode="a", encoding="utf-8"))

class MainWindow(QWidget):
    ICONS = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "COMMAND": "💻",
        "DEBUG": "🐞",
        "HIGHLIGHT": "⭐"
    }

    COLORS = {
        "INFO": "#2196F3",
        "SUCCESS": "#4CAF50",
        "WARNING": "#FFC107",
        "ERROR": "#F44336",
        "COMMAND": "#9C27B0",
        "DEBUG": "#607D8B",
        "HIGHLIGHT": "#FF5722"
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GROMACS Simulation GUI v1.0.0")
        self.setStyleSheet("font-family: Arial, sans-serif; color: #EEEEEE;")
     
        image_data = base64.b64decode(ICONAPP)
        byte_array = QByteArray(image_data)
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.data())
        self.setWindowIcon(QIcon(pixmap))

        self.threadpool = None

        self._init_ui()
        log_signal.new_log.connect(self.append_log)
        self.worker = None

    def _init_ui(self):
        self.threadpool = QThreadPool()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15,15,15,15)
        main_layout.setSpacing(12)

        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(15)
        form_layout.setVerticalSpacing(10)

        # Working folder
        lbl_folder = QLabel("📁 Working Folder:")
        self._set_label_dark(lbl_folder)
        self.input_folder = QLineEdit()
        self.input_folder.setPlaceholderText("Select working folder...")
        self.input_folder.setMinimumWidth(400)
        self._set_lineedit_dark(self.input_folder)
        self.btn_browse = QPushButton("Select Folder")
        self._set_button_dark(self.btn_browse)
        self.btn_browse.clicked.connect(self.browse_folder)

        form_layout.addWidget(lbl_folder, 0, 0)
        form_layout.addWidget(self.input_folder, 0, 1)
        form_layout.addWidget(self.btn_browse, 0, 2)

        # GROMACS Engine
        lbl_engine = QLabel("⚙️ GROMACS Engine:")
        self._set_label_dark(lbl_engine)
        self.combo_engine = QComboBox()
        self.combo_engine.addItems(["CUDA (GPU)", "CPU"])
        self.combo_engine.setMaximumWidth(120)
        self._set_combobox_dark(self.combo_engine)
        self.combo_engine.currentIndexChanged.connect(self.engine_changed)

        form_layout.addWidget(lbl_engine, 1, 0)
        form_layout.addWidget(self.combo_engine, 1, 1)

        # Number of GPUs
        lbl_gpu = QLabel("🧠 Number of GPUs:")
        self._set_label_dark(lbl_gpu)
        self.input_gpu = QLineEdit("1")
        self.input_gpu.setMaximumWidth(80)
        self._set_lineedit_dark(self.input_gpu)
        form_layout.addWidget(lbl_gpu, 2, 0)
        form_layout.addWidget(self.input_gpu, 2, 1)

        # Number of CPU cores
        lbl_core = QLabel("🧵 Number of CPU Cores:")
        self._set_label_dark(lbl_core)
        self.input_core = QLineEdit("8")
        self.input_core.setMaximumWidth(80)
        self._set_lineedit_dark(self.input_core)
        form_layout.addWidget(lbl_core, 3, 0)
        form_layout.addWidget(self.input_core, 3, 1)

        # Simulation duration
        lbl_duration = QLabel("⏱️ Simulation Duration:")
        self._set_label_dark(lbl_duration)
        self.input_duration = QLineEdit("5")
        self.input_duration.setMaximumWidth(80)
        self._set_lineedit_dark(self.input_duration)
        form_layout.addWidget(lbl_duration, 4, 0)
        form_layout.addWidget(self.input_duration, 4, 1)

        # Time unit
        lbl_unit = QLabel("📏 Time Unit:")
        self._set_label_dark(lbl_unit)
        self.combo_unit = QComboBox()
        self.combo_unit.addItems(["ns", "ps"])
        self.combo_unit.setMaximumWidth(80)
        self._set_combobox_dark(self.combo_unit)
        form_layout.addWidget(lbl_unit, 5, 0)
        form_layout.addWidget(self.combo_unit, 5, 1)

        main_layout.addLayout(form_layout)

        # Start and stop buttons
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶️ Start Simulation")
        self._set_button_dark(self.btn_start, primary=True)
        self.btn_start.clicked.connect(self.start_simulation)
        btn_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("⏹️ Stop")
        self._set_button_dark(self.btn_stop, secondary=True)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_simulation)
        btn_layout.addWidget(self.btn_stop)

        main_layout.addLayout(btn_layout)

        # Progress bars and log output
        self.progress_overall = QProgressBar()
        self.progress_overall.setFormat("Overall Progress: %p%")
        self.progress_overall.setValue(0)
        self.progress_overall.setTextVisible(True)
        self.progress_overall.setStyleSheet(self._progress_style_dark())
        main_layout.addWidget(self.progress_overall)

        self.progress_step = QProgressBar()
        self.progress_step.setFormat("Step Progress: %p%")
        self.progress_step.setValue(0)
        self.progress_step.setTextVisible(True)
        self.progress_step.setStyleSheet(self._progress_style_dark())
        main_layout.addWidget(self.progress_step)

        self.label_current_step = QLabel("Current Step: Ready to start...")
        self.label_current_step.setStyleSheet("font-weight: bold; font-size: 14px; color: #EEEEEE;")
        main_layout.addWidget(self.label_current_step)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.log_output.setStyleSheet("""
            background-color: #1e1e1e;
            font-family: Consolas, monospace;
            font-size: 12px;
            color: #CCCCCC;
            border: 1px solid #444444;
        """)
        self.log_output.setMinimumHeight(350)
        main_layout.addWidget(self.log_output)

        self.log_output.setFrameShape(QFrame.Shape.Box)
        self.log_output.setFrameShadow(QFrame.Shadow.Plain)

        # Set initial GPU input state
        self.engine_changed(self.combo_engine.currentIndex())

    def engine_changed(self, index):
        engine_text = self.combo_engine.currentText()
        if engine_text == "CPU":
            self.input_gpu.setText("0")
            self.input_gpu.setEnabled(False)
        else:
            if self.input_gpu.text() == "0":
                self.input_gpu.setText("1")
            self.input_gpu.setEnabled(True)

    def _set_label_dark(self, label):
        label.setStyleSheet("color: #EEEEEE; font-weight: 600;")

    def _set_lineedit_dark(self, lineedit):
        lineedit.setStyleSheet("""
            background-color: #2d2d2d;
            border: 1px solid #555555;
            color: #EEEEEE;
            padding: 4px;
            border-radius: 4px;
        """)

    def _set_button_dark(self, button, primary=False, secondary=False):
        if primary:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #007ACC;
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 10px 20px;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #005F9E;
                }
                QPushButton:pressed {
                    background-color: #004C7A;
                }
            """)
        elif secondary:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #CC0000;
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 10px 20px;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #AA0000;
                }
                QPushButton:pressed {
                    background-color: #880000;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3a;
                    color: #EEEEEE;
                    font-weight: normal;
                    padding: 6px 12px;
                    border-radius: 6px;
                    border: 1px solid #555555;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #404040;
                }
            """)

    def _set_combobox_dark(self, combobox):
        combobox.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                color: #EEEEEE;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #555555;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: #3a3a3a;
            }
            QComboBox::down-arrow {
                width: 10px;
                height: 10px;
            }
        """)

    def _progress_style_dark(self):
        return """
        QProgressBar {
            border: 2px solid #444444;
            border-radius: 8px;
            text-align: center;
            background-color: #2d2d2d;
            height: 20px;
            color: #EEEEEE;
        }
        QProgressBar::chunk {
            background-color: #007ACC;
            border-radius: 8px;
        }
        """

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Working Folder", os.getcwd())
        if folder:
            self.input_folder.setText(folder)

    def append_log(self, level, message):
        icon = self.ICONS.get(level.upper(), "")
        color = self.COLORS.get(level.upper(), "#000000")
        formatted = f'<span style="color:{color}; font-weight:bold;">{icon} [{level}]</span> {message}'
        self.log_output.append(formatted)
        self.log_output.moveCursor(QTextCursor.MoveOperation.End)

    def disable_inputs(self):
        self.input_folder.setEnabled(False)
        self.input_gpu.setEnabled(False)
        self.input_core.setEnabled(False)
        self.input_duration.setEnabled(False)
        self.combo_unit.setEnabled(False)
        self.btn_browse.setEnabled(False)
        self.combo_engine.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def enable_inputs(self):
        self.input_folder.setEnabled(True)
        self.input_gpu.setEnabled(True)
        self.input_core.setEnabled(True)
        self.input_duration.setEnabled(True)
        self.combo_unit.setEnabled(True)
        self.btn_browse.setEnabled(True)
        self.combo_engine.setEnabled(True)
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def start_simulation(self):
        self.log_output.clear()
        self.progress_overall.setValue(0)
        self.progress_step.setValue(0)
        self.disable_inputs()
        self.label_current_step.setText("Current Step: -")

        folder = self.input_folder.text().strip()
        if not folder or not os.path.isdir(folder):
            self.append_log("ERROR", "❌ Invalid or no working folder selected.")
            self.enable_inputs()
            return
        try:
            engine_text = self.combo_engine.currentText()
            engine = "CUDA" if engine_text == "CUDA (GPU)" else "CPU"
            num_gpus = int(self.input_gpu.text())
            num_cores = int(self.input_core.text())
            duration = float(self.input_duration.text())
            unit = self.combo_unit.currentText()
        except Exception:
            self.append_log("ERROR", "❌ GPU count, core count, and duration must be valid numbers.")
            self.enable_inputs()
            return

        self.worker = SimulationWorker(folder, num_gpus, num_cores, duration, unit, engine)
        self.worker.signals.log.connect(self.append_log)
        self.worker.signals.progress.connect(self.update_progress)
        self.worker.signals.finished.connect(self.simulation_finished)

        self.steps_order = [
            "Step 1: Preprocessing Minimization",
            "Step 2: Minimization",
            "Step 3: Preprocessing Equilibration",
            "Step 4: Equilibration",
            "Step 5: Preprocessing Production",
            "Step 6: Production"
        ]
        self.current_step_index = -1

        self.threadpool.start(self.worker)

    def stop_simulation(self):
        if self.worker:
            self.worker.interrupt()
            self.append_log("WARNING", "⚠️ Stop request sent to simulation...")
            self.btn_stop.setEnabled(False)

    def update_progress(self, percent, step_name):
        if step_name != self.label_current_step.text()[14:]:
            self.current_step_index = self.steps_order.index(step_name) if step_name in self.steps_order else -1
            self.label_current_step.setText(f"Current Step: {step_name}")
            self.progress_step.setValue(0)

        self.progress_step.setValue(percent)
        total_steps = len(self.steps_order)
        overall_percent = 0
        if self.current_step_index >= 0:
            overall_percent = ((self.current_step_index) + percent/100) / total_steps * 100
        self.progress_overall.setValue(int(overall_percent))

    def simulation_finished(self):
        self.label_current_step.setText("Simulation completed 🎉")
        self.progress_step.setValue(100)
        self.progress_overall.setValue(100)
        self.enable_inputs()
        self.append_log("INFO", "🎉 Simulation completed. All steps succeeded!")
