import sys

from PyQt5.QtWidgets import QApplication

from work_sheet_window import WorkSheet

if __name__ == "__main__":
    app = QApplication(sys.argv)
    work_sheet = WorkSheet()
    work_sheet.show()

    sys.exit(app.exec_())
