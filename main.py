import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from worksheet_window import Worksheet

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    worksheet = Worksheet(app)
    worksheet.show()

    sys.exit(app.exec_())
