# cnt = count
# comp = component
# curr = current
# idx = index
# props = properties
# ui = user interface


from PyQt5.QtWidgets import (QWidget, QLabel, QMenuBar, QMenu, QAction, QStatusBar,
                             QTableWidget, QTableWidgetItem, QPushButton, QAction,
                             QFileDialog, QAbstractItemView, QMessageBox, QListWidgetItem)
from PyQt5.QtCore import Qt
from openpyxl import load_workbook
import traceback

from substance import Substance
from stream import Stream


class ComponentsLibrary(QWidget):

    def __init__(self, stream_name, streams_list, streams, conds_names):
        super().__init__()
        self.comp_set = set()
        self.chosen_comps = {}

        self.stream_name = stream_name
        self.streams_list = streams_list
        self.streams = streams
        self.conds_names = conds_names

        self.init_ui()

    def init_ui(self):
        self.resize(800, 500)
        self.setWindowTitle("Components Library")
        self.setFixedSize(800, 500)

        self.create_menubar()
        self.create_statusbar()
        self.create_library_table()
        self.create_curr_stream_table()
        self.create_btn_add_comp_to_stream()
        self.create_btn_remove_comp_from_stream()
        self.create_btn_add_stream_to_worksheet()

    def create_menubar(self):
        self.menubar = QMenuBar(self)

        self.file_menu = QMenu(self.menubar)
        self.file_menu.setTitle("File")
        self.menubar.addMenu(self.file_menu)

        self.open_file = QAction('Open', self)
        self.open_file.setShortcut('Ctrl+Q')
        self.open_file.triggered.connect(self.open_library_file)

        self.test_program = QAction('Test', self)
        self.test_program.setShortcut('Ctrl+1')
        self.test_program.triggered.connect(self.test_program_func)

        self.test_program_sep = QAction('Test Sep', self)
        self.test_program_sep.setShortcut('Ctrl+2')
        self.test_program_sep.triggered.connect(self.test_program_sep_func)

        self.file_menu.addAction(self.open_file)
        try:
            self.file_menu.addAction(self.test_program)
            self.file_menu.addAction(self.test_program_sep)
        except:
            traceback.print_exc()

    def test_program_func(self):
        try:
            curr_row = 2
            if curr_row != -1:  # if user don't choose the cell, current row is equal -1
                # comp_key = substance class + id
                comp_substance_class = self.library_table.item(curr_row, 0).text()
                comp_id = str(self.library_table.item(curr_row, 1).text())
                comp_key = comp_substance_class + comp_id
                if comp_key not in self.comp_set:  # if substance is already in the stream, don't add it again
                    rows_cnt = self.curr_stream_table.rowCount() + 1
                    self.curr_stream_table.setRowCount(rows_cnt)
                    row_for_add = rows_cnt - 1
                    for col_idx in range(0, self.curr_stream_table.columnCount()):
                        chosen_comp_substance_class = self.library_table.item(curr_row, 0).text()
                        chosen_comp_id = self.library_table.item(curr_row, 1).text()
                        chosen_comp_key = chosen_comp_substance_class + chosen_comp_id
                        self.chosen_comps[chosen_comp_key] = self.all_comps[chosen_comp_key]
                        chosen_comp_classification = self.all_comps[chosen_comp_key].general_info.classification
                        classification_vals = list(chosen_comp_classification.output_props().values())
                        item = classification_vals[col_idx]
                        val = QTableWidgetItem(str(item))
                        val.setTextAlignment(Qt.AlignCenter)
                        self.curr_stream_table.setItem(row_for_add, col_idx, QTableWidgetItem(val))
                    self.comp_set.add(comp_key)

            self.curr_stream_table.sortItems(1, Qt.AscendingOrder)
            self.curr_stream_table.resizeColumnsToContents()

            self.add_stream_to_worksheet()

            self.streams["Stream 1"].conds["Temperature [C]"] = "45"
            self.streams["Stream 1"].conds["Pressure [Pa]"] = "200000"
            self.streams["Stream 1"].conds["Mass Flow [kg/sec]"] = "7"
            self.streams["Stream 1"].conds["Phase"] = "empty (phase)"
            self.streams["Stream 1"].fracs["component 1"]["Mass Fraction"] = "1.0"

            curr_row = 0
            comp_key = str(self.curr_stream_table.item(curr_row, 0).text()) + str(self.curr_stream_table.item(curr_row, 1).text())
            del self.chosen_comps[comp_key]
            self.curr_stream_table.removeRow(curr_row)

            self.stream_name = "Stream 2"
            curr_row = 6
            if curr_row != -1:  # if user don't choose the cell, current row is equal -1
                # comp_key = substance class + id
                comp_substance_class = self.library_table.item(curr_row, 0).text()
                comp_id = str(self.library_table.item(curr_row, 1).text())
                comp_key = comp_substance_class + comp_id
                if comp_key not in self.comp_set:  # if substance is already in the stream, don't add it again
                    rows_cnt = self.curr_stream_table.rowCount() + 1
                    self.curr_stream_table.setRowCount(rows_cnt)
                    row_for_add = rows_cnt - 1
                    for col_idx in range(0, self.curr_stream_table.columnCount()):
                        chosen_comp_substance_class = self.library_table.item(curr_row, 0).text()
                        chosen_comp_id = self.library_table.item(curr_row, 1).text()
                        chosen_comp_key = chosen_comp_substance_class + chosen_comp_id
                        self.chosen_comps[chosen_comp_key] = self.all_comps[chosen_comp_key]
                        chosen_comp_classification = self.all_comps[chosen_comp_key].general_info.classification
                        classification_vals = list(chosen_comp_classification.output_props().values())
                        item = classification_vals[col_idx]
                        val = QTableWidgetItem(str(item))
                        val.setTextAlignment(Qt.AlignCenter)
                        self.curr_stream_table.setItem(row_for_add, col_idx, QTableWidgetItem(val))
                    self.comp_set.add(comp_key)

            self.curr_stream_table.sortItems(1, Qt.AscendingOrder)
            self.curr_stream_table.resizeColumnsToContents()


            self.add_stream_to_worksheet()

            self.streams["Stream 2"].conds["Temperature [C]"] = "80"
            self.streams["Stream 2"].conds["Pressure [Pa]"] = "200000"
            self.streams["Stream 2"].conds["Mass Flow [kg/sec]"] = "3.31"
            self.streams["Stream 2"].conds["Phase"] = "empty (phase)"
            self.streams["Stream 2"].fracs["component 1"]["Mass Fraction"] = "1.0"
        except:
            traceback.print_exc()

    def test_program_sep_func(self):
        try:
            curr_row = 0
            if curr_row != -1:  # if user don't choose the cell, current row is equal -1
                # comp_key = substance class + id
                comp_substance_class = self.library_table.item(curr_row, 0).text()
                comp_id = str(self.library_table.item(curr_row, 1).text())
                comp_key = comp_substance_class + comp_id
                if comp_key not in self.comp_set:  # if substance is already in the stream, don't add it again
                    rows_cnt = self.curr_stream_table.rowCount() + 1
                    self.curr_stream_table.setRowCount(rows_cnt)
                    row_for_add = rows_cnt - 1
                    for col_idx in range(0, self.curr_stream_table.columnCount()):
                        chosen_comp_substance_class = self.library_table.item(curr_row, 0).text()
                        chosen_comp_id = self.library_table.item(curr_row, 1).text()
                        chosen_comp_key = chosen_comp_substance_class + chosen_comp_id
                        self.chosen_comps[chosen_comp_key] = self.all_comps[chosen_comp_key]
                        chosen_comp_classification = self.all_comps[chosen_comp_key].general_info.classification
                        classification_vals = list(chosen_comp_classification.output_props().values())
                        item = classification_vals[col_idx]
                        val = QTableWidgetItem(str(item))
                        val.setTextAlignment(Qt.AlignCenter)
                        self.curr_stream_table.setItem(row_for_add, col_idx, QTableWidgetItem(val))
                    self.comp_set.add(comp_key)
            curr_row = 1
            if curr_row != -1:  # if user don't choose the cell, current row is equal -1
                # comp_key = substance class + id
                comp_substance_class = self.library_table.item(curr_row, 0).text()
                comp_id = str(self.library_table.item(curr_row, 1).text())
                comp_key = comp_substance_class + comp_id
                if comp_key not in self.comp_set:  # if substance is already in the stream, don't add it again
                    rows_cnt = self.curr_stream_table.rowCount() + 1
                    self.curr_stream_table.setRowCount(rows_cnt)
                    row_for_add = rows_cnt - 1
                    for col_idx in range(0, self.curr_stream_table.columnCount()):
                        chosen_comp_substance_class = self.library_table.item(curr_row, 0).text()
                        chosen_comp_id = self.library_table.item(curr_row, 1).text()
                        chosen_comp_key = chosen_comp_substance_class + chosen_comp_id
                        self.chosen_comps[chosen_comp_key] = self.all_comps[chosen_comp_key]
                        chosen_comp_classification = self.all_comps[chosen_comp_key].general_info.classification
                        classification_vals = list(chosen_comp_classification.output_props().values())
                        item = classification_vals[col_idx]
                        val = QTableWidgetItem(str(item))
                        val.setTextAlignment(Qt.AlignCenter)
                        self.curr_stream_table.setItem(row_for_add, col_idx, QTableWidgetItem(val))
                    self.comp_set.add(comp_key)
            curr_row = 2
            if curr_row != -1:  # if user don't choose the cell, current row is equal -1
                # comp_key = substance class + id
                comp_substance_class = self.library_table.item(curr_row, 0).text()
                comp_id = str(self.library_table.item(curr_row, 1).text())
                comp_key = comp_substance_class + comp_id
                if comp_key not in self.comp_set:  # if substance is already in the stream, don't add it again
                    rows_cnt = self.curr_stream_table.rowCount() + 1
                    self.curr_stream_table.setRowCount(rows_cnt)
                    row_for_add = rows_cnt - 1
                    for col_idx in range(0, self.curr_stream_table.columnCount()):
                        chosen_comp_substance_class = self.library_table.item(curr_row, 0).text()
                        chosen_comp_id = self.library_table.item(curr_row, 1).text()
                        chosen_comp_key = chosen_comp_substance_class + chosen_comp_id
                        self.chosen_comps[chosen_comp_key] = self.all_comps[chosen_comp_key]
                        chosen_comp_classification = self.all_comps[chosen_comp_key].general_info.classification
                        classification_vals = list(chosen_comp_classification.output_props().values())
                        item = classification_vals[col_idx]
                        val = QTableWidgetItem(str(item))
                        val.setTextAlignment(Qt.AlignCenter)
                        self.curr_stream_table.setItem(row_for_add, col_idx, QTableWidgetItem(val))
                    self.comp_set.add(comp_key)
            curr_row = 4
            if curr_row != -1:  # if user don't choose the cell, current row is equal -1
                # comp_key = substance class + id
                comp_substance_class = self.library_table.item(curr_row, 0).text()
                comp_id = str(self.library_table.item(curr_row, 1).text())
                comp_key = comp_substance_class + comp_id
                if comp_key not in self.comp_set:  # if substance is already in the stream, don't add it again
                    rows_cnt = self.curr_stream_table.rowCount() + 1
                    self.curr_stream_table.setRowCount(rows_cnt)
                    row_for_add = rows_cnt - 1
                    for col_idx in range(0, self.curr_stream_table.columnCount()):
                        chosen_comp_substance_class = self.library_table.item(curr_row, 0).text()
                        chosen_comp_id = self.library_table.item(curr_row, 1).text()
                        chosen_comp_key = chosen_comp_substance_class + chosen_comp_id
                        self.chosen_comps[chosen_comp_key] = self.all_comps[chosen_comp_key]
                        chosen_comp_classification = self.all_comps[chosen_comp_key].general_info.classification
                        classification_vals = list(chosen_comp_classification.output_props().values())
                        item = classification_vals[col_idx]
                        val = QTableWidgetItem(str(item))
                        val.setTextAlignment(Qt.AlignCenter)
                        self.curr_stream_table.setItem(row_for_add, col_idx, QTableWidgetItem(val))
                    self.comp_set.add(comp_key)
            curr_row = 6
            if curr_row != -1:  # if user don't choose the cell, current row is equal -1
                # comp_key = substance class + id
                comp_substance_class = self.library_table.item(curr_row, 0).text()
                comp_id = str(self.library_table.item(curr_row, 1).text())
                comp_key = comp_substance_class + comp_id
                if comp_key not in self.comp_set:  # if substance is already in the stream, don't add it again
                    rows_cnt = self.curr_stream_table.rowCount() + 1
                    self.curr_stream_table.setRowCount(rows_cnt)
                    row_for_add = rows_cnt - 1
                    for col_idx in range(0, self.curr_stream_table.columnCount()):
                        chosen_comp_substance_class = self.library_table.item(curr_row, 0).text()
                        chosen_comp_id = self.library_table.item(curr_row, 1).text()
                        chosen_comp_key = chosen_comp_substance_class + chosen_comp_id
                        self.chosen_comps[chosen_comp_key] = self.all_comps[chosen_comp_key]
                        chosen_comp_classification = self.all_comps[chosen_comp_key].general_info.classification
                        classification_vals = list(chosen_comp_classification.output_props().values())
                        item = classification_vals[col_idx]
                        val = QTableWidgetItem(str(item))
                        val.setTextAlignment(Qt.AlignCenter)
                        self.curr_stream_table.setItem(row_for_add, col_idx, QTableWidgetItem(val))
                    self.comp_set.add(comp_key)

            self.curr_stream_table.sortItems(1, Qt.AscendingOrder)
            self.curr_stream_table.resizeColumnsToContents()

            self.add_stream_to_worksheet()

            self.streams["Stream 1"].conds["Temperature [C]"] = "20"
            self.streams["Stream 1"].conds["Pressure [Pa]"] = "100000"
            self.streams["Stream 1"].conds["Mass Flow [kg/sec]"] = "1"
            self.streams["Stream 1"].conds["Phase"] = "empty (phase)"
            self.streams["Stream 1"].fracs["component 1"]["Molar Fraction"] = "0.605"
            self.streams["Stream 1"].fracs["component 2"]["Molar Fraction"] = "0.175"
            self.streams["Stream 1"].fracs["component 3"]["Molar Fraction"] = "0.147"
            self.streams["Stream 1"].fracs["component 4"]["Molar Fraction"] = "0.044"
            self.streams["Stream 1"].fracs["component 5"]["Molar Fraction"] = "0.029"


        except:
            traceback.print_exc()

    def create_statusbar(self):
        self.statusbar = QStatusBar(self)
        self.statusbar.showMessage("Open Library File")
        self.statusbar.setStyleSheet("QStatusBar{background:rgb(255,0,0);color:black;font-weight:bold;}")
        self.statusbar.setGeometry(0, 480, 800, 20)

    def open_library_file(self):
        # the "r" character is needed because Python thinks that \ is a character that describes the next word to skip.
        # standard_folder = r"D:\Chemical programming\ChemTech\Streams Menu\Component Library Excel"
        # self.library_path = QFileDialog.getOpenFileName(self, "Open Library File", standard_folder)[0]
        self.library_path = r".\Hydrocarbons C1-C10.xlsx" #PC
        self.load_data_library_table(self.library_path)

        self.statusbar.showMessage("Add components to stream")
        self.statusbar.setStyleSheet("QStatusBar{background:rgb(0,255,0);color:black;font-weight:bold;}")
        # when we loaded data, we understood what columns headers are needed, then we set headers for current stream table
        self.curr_stream_table.setRowCount(0)
        self.curr_stream_table.setColumnCount(self.cols_count)

        self.curr_stream_table.setHorizontalHeaderLabels(self.headers)
        self.curr_stream_table.resizeColumnsToContents()
        self.curr_stream_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def create_library_table(self):
        self.library_table = QTableWidget(self)
        self.library_table.setGeometry(20, 40, 300, 400)

    def load_data_library_table(self, path):

        self.transfer_all_comps_to_dict(path)
        self.fill_library_table_with_values()

    def transfer_all_comps_to_dict(self, path):
        self.all_comps = {}

        workbook = load_workbook(path)
        sheets_names = workbook.sheetnames
        for sheet in sheets_names:
            sheet_vals = list(workbook[sheet].values)
            props_groups = {}
            for row_idx in range(len(sheet_vals)):
                if row_idx == 0:
                    props_cnt_in_props_group = 1
                    previous = sheet_vals[row_idx][0]
                    for val in sheet_vals[row_idx]:
                        if (val is not None) and (val not in props_groups.keys()):
                            props_groups[val] = props_cnt_in_props_group
                            props_cnt_in_props_group = 1
                            previous = val
                        else:
                            props_cnt_in_props_group += 1
                            props_groups[previous] = props_cnt_in_props_group
                elif row_idx == 1:
                    props = sheet_vals[row_idx]
                    counter = 0
                    for props_group, props_cnt_in_props_group in props_groups.items():
                        props_groups[props_group] = props[counter:counter + props_cnt_in_props_group]
                        counter += props_cnt_in_props_group
                else:
                    props_class = sheet
                    props_vals = sheet_vals[row_idx]
                    substance_class, substance_id = props_vals[0], props_vals[1]
                    comp_key = substance_class + str(substance_id)
                    if comp_key not in self.all_comps.keys():
                        self.all_comps[comp_key] = Substance()
                    counter = 0
                    for props_group, props in props_groups.items():
                        props_cnt = len(props)
                        self.all_comps[comp_key].get_props(props_class, props_group, props_vals[counter:counter + props_cnt])
                        counter += props_cnt

    def fill_library_table_with_values(self):
        self.headers = ["Substance Class", "ID", "Name", "Chemical Formula"]

        self.rows_cnt = len(self.all_comps)  # components count in library file
        self.cols_count = len(self.headers)  # columns count is equal number of headers (component characteristics)
        self.library_table.setRowCount(self.rows_cnt)
        self.library_table.setColumnCount(self.cols_count)

        self.library_table.setHorizontalHeaderLabels(self.headers)

        row_idx = 0
        for comp_key in self.all_comps.keys():
            col_idx = 0
            classification = self.all_comps[comp_key].general_info.classification
            classification_vals = list(classification.output_props().values())
            for val in classification_vals:
                val = QTableWidgetItem(str(val))
                val.setTextAlignment(Qt.AlignCenter)
                self.library_table.setItem(row_idx, col_idx, QTableWidgetItem(val))
                col_idx += 1
            row_idx += 1

        self.library_table.resizeColumnsToContents()
        self.library_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # cells can not be changed now

    def create_curr_stream_table(self):
        self.curr_stream_table = QTableWidget(self)
        self.curr_stream_table.setGeometry(480, 40, 300, 400)

    def create_btn_add_comp_to_stream(self):
        self.btn_add_comp_to_stream = QPushButton(self)
        self.btn_add_comp_to_stream.setGeometry(360, 160, 80, 40)
        self.btn_add_comp_to_stream.setText("Add")

        self.btn_add_comp_to_stream.clicked.connect(self.add_comp_to_stream)

    def add_comp_to_stream(self):
        curr_row = self.library_table.currentRow()
        if curr_row != -1:  # if user don't choose the cell, current row is equal -1
            # comp_key = substance class + id
            comp_substance_class = self.library_table.item(curr_row, 0).text()
            comp_id = str(self.library_table.item(curr_row, 1).text())
            comp_key = comp_substance_class + comp_id
            if comp_key not in self.comp_set:  # if substance is already in the stream, don't add it again
                rows_cnt = self.curr_stream_table.rowCount() + 1
                self.curr_stream_table.setRowCount(rows_cnt)
                row_for_add = rows_cnt - 1
                for col_idx in range(0, self.curr_stream_table.columnCount()):
                    chosen_comp_substance_class = self.library_table.item(curr_row, 0).text()
                    chosen_comp_id = self.library_table.item(curr_row, 1).text()
                    chosen_comp_key = chosen_comp_substance_class + chosen_comp_id
                    self.chosen_comps[chosen_comp_key] = self.all_comps[chosen_comp_key]
                    chosen_comp_classification = self.all_comps[chosen_comp_key].general_info.classification
                    classification_vals = list(chosen_comp_classification.output_props().values())
                    item = classification_vals[col_idx]
                    val = QTableWidgetItem(str(item))
                    val.setTextAlignment(Qt.AlignCenter)
                    self.curr_stream_table.setItem(row_for_add, col_idx, QTableWidgetItem(val))
                self.comp_set.add(comp_key)

        self.curr_stream_table.sortItems(1, Qt.AscendingOrder)
        self.curr_stream_table.resizeColumnsToContents()

    def create_btn_remove_comp_from_stream(self):
        self.btn_remove_comp_from_stream = QPushButton(self)
        self.btn_remove_comp_from_stream.setGeometry(360, 240, 80, 40)
        self.btn_remove_comp_from_stream.setText("Remove")

        self.btn_remove_comp_from_stream.clicked.connect(self.remove_comp_from_stream)

    def remove_comp_from_stream(self):
        curr_row = self.curr_stream_table.currentRow()
        comp_key = str(self.curr_stream_table.item(curr_row, 0).text()) + str(self.curr_stream_table.item(curr_row, 1).text())
        del self.chosen_comps[comp_key]
        self.curr_stream_table.removeRow(curr_row)

    def create_btn_add_stream_to_worksheet(self):
        self.btn_add_stream = QPushButton(self)
        self.btn_add_stream.setGeometry(480, 440, 300, 40)
        self.btn_add_stream.setText("Add stream")

        self.btn_add_stream.clicked.connect(self.add_stream_to_worksheet)

    def add_stream_to_worksheet(self):
        # adding stream in streams list
        if self.curr_stream_table.rowCount() == 0:  # check if stream is empty
            message_empty_curr_stream_table = QMessageBox(self)
            message_empty_curr_stream_table.setWindowTitle("Error")
            message_empty_curr_stream_table.setText("You haven't added any components")
            message_empty_curr_stream_table.show()
        else:
            stream = Stream(self.stream_name, self.conds_names, self.chosen_comps)
            # saving information about the stream in a dictionary for further use
            self.streams_list.addItem(QListWidgetItem(self.stream_name))
            self.streams[self.stream_name] = stream

            self.close()
            self.deleteLater()  # by my design, this line of code should delete the Components Library class object,
            # because I don't want to use RAM to store all information from every library I open
