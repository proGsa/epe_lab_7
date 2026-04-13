from PyQt5.QtWidgets import (
    QMainWindow,
    QHeaderView,
    QTableWidgetItem,
    QMessageBox,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QSpinBox,
)
import matplotlib.pyplot as plt

from gui.gui import Ui_MainWindow
from logic.fp import calculate_fp, adjust_fp, get_loc_by_fp
from logic.cocomo2 import app_composition, early_architecture


class Window(QMainWindow):
    def __init__(self) -> None:
        super(Window, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setupCocomoModelTabs()
        self.setupArchitectureLocInput()
        self.setupEarlyArchitectureFactorValues()
        self.resizeTables()

        # Data
        self.loc = None

        # Buttons
        self.ui.resultFuncDotBtn.clicked.connect(self.funcDotsMethod)
        self.ui.resultCompositionBtn.clicked.connect(self.appCompositionCocomo2)
        self.ui.resultArchitectureBtn.clicked.connect(self.earlyArchitectureCocomo2)


    def setupCocomoModelTabs(self):
        self.cocomoModelTabs = QTabWidget(self.ui.cocomo2)
        compositionTab = QWidget()
        architectureTab = QWidget()

        compositionLayout = QVBoxLayout(compositionTab)
        self.ui.groupBox_5.setParent(compositionTab)
        self.ui.groupBox_6.setParent(compositionTab)
        compositionLayout.addWidget(self.ui.groupBox_5)
        compositionLayout.addWidget(self.ui.groupBox_6)

        architectureLayout = QVBoxLayout(architectureTab)
        self.architectureFactorsGroup, self.architectureFactorComboboxes = self.createArchitectureFactorsGroup()
        self.ui.groupBox_7.setParent(architectureTab)
        architectureLayout.addWidget(self.architectureFactorsGroup)
        architectureLayout.addWidget(self.ui.groupBox_7)

        self.clearLayout(self.ui.horizontalLayout_41)
        self.ui.horizontalLayout_41.addWidget(self.cocomoModelTabs)

        self.cocomoModelTabs.addTab(compositionTab, "COCOMO II (Композиция приложения)")
        self.cocomoModelTabs.addTab(architectureTab, "COCOMO II (ранняя разработка архитектуры)")


    def createArchitectureFactorsGroup(self):
        factorSources = [
            self.ui.factorSelectPREC,
            self.ui.factorSelectFLEX,
            self.ui.factorSelectRESL,
            self.ui.factorSelectTEAM,
            self.ui.factorSelectPMAT,
        ]
        factorLabels = ["PREC", "FLEX", "RESL", "TEAM", "PMAT"]

        group = QGroupBox("Факторы показателя степени модели", self.ui.cocomo2)
        groupLayout = QVBoxLayout(group)
        comboboxes = []

        for labelText, source in zip(factorLabels, factorSources):
            rowLayout = QHBoxLayout()
            label = QLabel(labelText, group)
            combobox = QComboBox(group)

            for i in range(source.count()):
                combobox.addItem(source.itemText(i))
            combobox.setCurrentIndex(source.currentIndex())

            rowLayout.addWidget(label)
            rowLayout.addWidget(combobox)
            rowLayout.setStretch(0, 1)
            rowLayout.setStretch(1, 5)
            groupLayout.addLayout(rowLayout)
            comboboxes.append(combobox)

        return group, comboboxes


    def clearLayout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            childLayout = item.layout()
            childWidget = item.widget()
            if childLayout is not None:
                self.clearLayout(childLayout)
            if childWidget is not None:
                childWidget.setParent(None)


    def setupArchitectureLocInput(self):
        locLayout = QHBoxLayout()
        locLabel = QLabel("LOC", self.ui.groupBox_7)
        self.locArchitectureInput = QSpinBox(self.ui.groupBox_7)
        self.locArchitectureInput.setMaximum(99999999)
        self.locArchitectureInput.setValue(2731)

        locLayout.addWidget(locLabel)
        locLayout.addWidget(self.locArchitectureInput)
        locLayout.setStretch(0, 1)
        locLayout.setStretch(1, 1)

        insertIndex = max(self.ui.verticalLayout_16.count() - 1, 0)
        self.ui.verticalLayout_16.insertLayout(insertIndex, locLayout)


    def setupEarlyArchitectureFactorValues(self):
        multiplier_values = {
            self.ui.modelSelectPERS: [2.12, 1.62, 1.26, 1.00, 0.83, 0.63, 0.50],
            self.ui.modelSelectRCPX: [0.49, 0.60, 0.83, 1.00, 1.33, 1.91, 2.72],
            self.ui.modelSelectRUSE: [0.95, 1.00, 1.07, 1.15, 1.24],
            self.ui.modelSelectPDIF: [0.87, 1.00, 1.29, 1.81, 2.61],
            self.ui.modelSelectPREX: [1.59, 1.33, 1.22, 1.00, 0.87, 0.74, 0.62],
            self.ui.modelSelectFSIL: [1.43, 1.30, 1.10, 1.00, 0.87, 0.73, 0.62],
            self.ui.modelSelectSCED: [1.43, 1.14, 1.00, 1.00, 1.00],
        }

        for combobox, values in multiplier_values.items():
            if combobox.count() < len(values):
                combobox.insertItem(0, "Сверхнизкий")
            for i, value in enumerate(values):
                level = combobox.itemText(i)
                combobox.setItemText(i, f"{level} ({self.formatFactorValue(value)})")


    def formatFactorValue(self, value: float) -> str:
        formatted = f"{value:.2f}".rstrip("0").rstrip(".")
        return formatted if "." in formatted else f"{formatted}.0"


    def earlyArchitectureCocomo2(self):
        # 1. Get data
        loc = self.locArchitectureInput.value()
        if loc <= 0:
            QMessageBox.warning(self, "Ошибка", "Введите LOC больше 0")
            return
        
        parametersDict = {
            "MULTIPLIERS": [self.ui.modelSelectPERS.currentIndex(),
                            self.ui.modelSelectRCPX.currentIndex(),
                            self.ui.modelSelectRUSE.currentIndex(),
                            self.ui.modelSelectPDIF.currentIndex(),
                            self.ui.modelSelectPREX.currentIndex(),
                            self.ui.modelSelectFSIL.currentIndex(),
                            self.ui.modelSelectSCED.currentIndex(),],
            "FACTORS"    : [combobox.currentIndex() for combobox in self.architectureFactorComboboxes],
            "LOC"        : loc,
        }

        salary = self.ui.avgSalaryArchitectureInput.value()

        # 2. Calculate
        resultDict = early_architecture(salary, parametersDict)

        # 3. Show result
        self.ui.resultArchitectureTable.setItem(0, 0, QTableWidgetItem(str(resultDict["WORK"])))
        self.ui.resultArchitectureTable.setItem(0, 1, QTableWidgetItem(str(resultDict["TIME"])))
        self.ui.resultArchitectureTable.setItem(0, 2, QTableWidgetItem(str(resultDict["BUDGET"])))



    def appCompositionCocomo2(self):
        # 1. Get data
        parametersDict = {
            "FORMS"  : [self.ui.screenFormEasyInput.value(), 
                        self.ui.screenFormNormalInput.value(), 
                        self.ui.screenFormHardInput.value(),],
            "REPORTS": [self.ui.reportEasyInput.value(),
                        self.ui.reportNormalInput.value(),
                        self.ui.reportHardInput.value(),],
            "MODULES": self.ui.modulesInput.value(),
            "RUSE"   : self.ui.RUSEPercentInput.value(),
            "PROD"   : self.ui.teamExpSelect.currentIndex(),
            "FACTORS": [self.ui.factorSelectPREC.currentIndex(),
                        self.ui.factorSelectFLEX.currentIndex(),
                        self.ui.factorSelectRESL.currentIndex(),
                        self.ui.factorSelectTEAM.currentIndex(),
                        self.ui.factorSelectPMAT.currentIndex(),],
        }

        salary = self.ui.avgSalaryCompositionInput.value()

        # 2. Calculate
        resultDict = app_composition(salary, parametersDict)

        # 3. Show result
        self.ui.resultCompositionTable.setItem(0, 0, QTableWidgetItem(str(resultDict["WORK"])))
        self.ui.resultCompositionTable.setItem(0, 1, QTableWidgetItem(str(resultDict["TIME"])))
        self.ui.resultCompositionTable.setItem(0, 2, QTableWidgetItem(str(resultDict["BUDGET"])))


    def funcDotsMethod(self):
        # 1. Get data
        productAttributes = self.getPoductAttributes()
        # print(f"1. productAttributes = {productAttributes}")

        languagePercents = self.getLanguagePercents()
        # print(f"2. languagePercents = {languagePercents}")

        funcDotsTableMatrix = self.getFuncDotsTableMatrix()
        if (funcDotsTableMatrix is None): return
        # print(f"3. funcTableMatrix = \n")
        # [print(row) for row in funcDotsTableMatrix]

        # 2. Calculate
        fp = calculate_fp(funcDotsTableMatrix)
        afp = adjust_fp(fp[-1], productAttributes)
        loc = get_loc_by_fp(afp, languagePercents)
        self.loc = loc
        self.locArchitectureInput.setValue(loc)

        # print(f"4. fp = {fp}; afp = {afp}; loc = {loc}")

        # 3. Show result
        self.ui.resultFuncDotsTable.setItem(0, 0, QTableWidgetItem(str(fp[1])))
        self.ui.resultFuncDotsTable.setItem(0, 1, QTableWidgetItem(str(round(afp, 2))))
        self.ui.resultFuncDotsTable.setItem(0, 2, QTableWidgetItem(str(loc)))

        rows = self.ui.funcDotsTable.rowCount()
        column = self.ui.funcDotsTable.columnCount() - 1
        table = self.ui.funcDotsTable

        for row in range(rows):
            table.setItem(row, column, QTableWidgetItem(str(fp[0][row])))
            

    def getFuncDotsTableMatrix(self):
        matrix = []

        rows = self.ui.funcDotsTable.rowCount()
        columns = self.ui.funcDotsTable.columnCount()
        table = self.ui.funcDotsTable

        for row in range(rows):
            rowMatrix = []

            for column in range(columns - 1):
                try:
                    rowMatrix.append(int(table.item(row, column).text()))
                except:
                    QMessageBox.warning(self, "Ошибка", "Не целое число в таблице")
                    return None
            
            matrix.append(rowMatrix)

        return matrix


    def getPoductAttributes(self):
        return [
            self.ui.productAttributeSelect1.currentIndex(),
            self.ui.productAttributeSelect2.currentIndex(),
            self.ui.productAttributeSelect3.currentIndex(),
            self.ui.productAttributeSelect4.currentIndex(),
            self.ui.productAttributeSelect5.currentIndex(),
            self.ui.productAttributeSelect6.currentIndex(),
            self.ui.productAttributeSelect7.currentIndex(),
            self.ui.productAttributeSelect8.currentIndex(),
            self.ui.productAttributeSelect9.currentIndex(),
            self.ui.productAttributeSelect10.currentIndex(),
            self.ui.productAttributeSelect11.currentIndex(),
            self.ui.productAttributeSelect12.currentIndex(),
            self.ui.productAttributeSelect13.currentIndex(),
            self.ui.productAttributeSelect14.currentIndex(),
        ]
    

    def getLanguagePercents(self):
        return [
            self.ui.languagePercentInput1.value(),
            self.ui.languagePercentInput2.value(),
            self.ui.languagePercentInput3.value(),
            self.ui.languagePercentInput4.value(),
            self.ui.languagePercentInput5.value(),
            self.ui.languagePercentInput6.value(),
            self.ui.languagePercentInput7.value(),
            self.ui.languagePercentInput8.value(),
            self.ui.languagePercentInput9.value(),
            self.ui.languagePercentInput10.value(),
            self.ui.languagePercentInput11.value(),
            self.ui.languagePercentInput12.value(),
            self.ui.languagePercentInput13.value(),
            self.ui.languagePercentInput14.value(),
            self.ui.languagePercentInput15.value(),
            self.ui.languagePercentInput16.value(),
        ]
    

    def resizeTables(self):
        self.ui.funcDotsTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.funcDotsTable.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.ui.resultFuncDotsTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.resultFuncDotsTable.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.ui.resultCompositionTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.resultCompositionTable.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.ui.resultArchitectureTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.resultArchitectureTable.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
