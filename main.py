import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor
from gui_main import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor("#121212"))
    palette.setColor(palette.ColorRole.WindowText, QColor("#EEEEEE"))
    palette.setColor(palette.ColorRole.Base, QColor("#1e1e1e"))
    palette.setColor(palette.ColorRole.AlternateBase, QColor("#2c2c2c"))
    palette.setColor(palette.ColorRole.ToolTipBase, QColor("#EEEEEE"))
    palette.setColor(palette.ColorRole.ToolTipText, QColor("#EEEEEE"))
    palette.setColor(palette.ColorRole.Text, QColor("#EEEEEE"))
    palette.setColor(palette.ColorRole.Button, QColor("#007ACC"))
    palette.setColor(palette.ColorRole.ButtonText, QColor("#FFFFFF"))
    palette.setColor(palette.ColorRole.BrightText, QColor("#F44336"))
    palette.setColor(palette.ColorRole.Highlight, QColor("#007ACC"))
    palette.setColor(palette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
