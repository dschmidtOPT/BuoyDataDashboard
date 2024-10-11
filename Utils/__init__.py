from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import datetime
from datetime import datetime
import time
import sys
import traceback
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

### Stateful classes

class Styles:
    buttons = "border : 1.5px solid black; border-radius : 10px; background-color: whitesmoke"
    plotbutton = "border : 1.5px solid black; border-radius : 10px; background-color: rgb(19,202,219)"
    bg = "background-color: whitesmoke"
    OPTlogobg = "background-color: rgb(227, 239, 246)"

class Msg:
    '''
    Holds standard message payloads for UI
    '''
    startup = ['Welcome to the OPT Buoy Data Dashboard.',
               '  >If using the dashboard on a raw dataset, select "Compress Dataset."',
               '  >If concatenated data files are not generated ( <metric name>_full.dat ), select "Combine Metrics"',
               '  >If compression has already run and files exist with names <metric>_full.dat, select plot options.',
              '  >If unsure how to proceeed, select "Process Data" and follow prompts.',
              '',
               'Select an option to receive additional instructions.']
    buffer = []

class States:
    '''
    Used to set values from worker threads that are read from main thread loop
    These attributes will be updated during UI operation
    '''
    thread_running = False
    multi_progress = False
    selectedDates = False
    t0 = None
    tN = None
    now = QDateTime.currentDateTime().toPyDateTime()
    startDate = now
    endDate = startDate
    trendline = False
    plotted = False
    gridlines = True
    progress_barA = 0
    progress_barB = 0
    selected_pare = ''
    selected_key = ''
    CSV_output = False
    pareVal = 0
    
    def __init(self):
        self.startRef = None
        self.trendline = False
        self.selected_pare = "Raw Data"
        self.selected_key = "-- No Selection --"
        print(self.startDate, self.endDate)

class Vals:
    '''
    Critical UI constants used during initialization.
    '''
    embedded_log = True #False # All print statements appear in embedded text box
    gr = 1.618033988749894
    margin = 0.025
    dir_path = None
    file_path = None
    
    timeseries = []
    increment = 0
    numticks = 20
    h = None
    v = None
    win_w = None
    win_h = None
    startup = True
    event_delay = 500
    horzLayout = False
    startDate = None
    startTime = None
    endDate = None
    endTime = None
    CSVoutput = True
    targets = "All"
    keylib = ['Clear selections', 'CntrlBusV', 'GenDrvCrnt', 'SolarCrnt', 'WECLVCrnt', 'WindCrnt', 'DumpCrnt',
              'ExtChgCrnt', 'NoConnect1', 'ChgTo28VBusCrnt', 'HighPldCrnt', 'LVBat1Crnt', 'LVBat2Crnt',
              'CntrlBusCrnt', 'CritPldCrnt', 'MidPldCrnt', 'CritPld4Crnt', 'GenDrvLVCrnt', 'AccX', 'AccY',
              'AccZ', 'SparPres', 'PCBHumidity', 'PCBTemp', 'Position', 'Velocity', 'HVBusVolt', 'HVBusBUVolt',
              'LVBat1Volt', 'LVBat2Volt', 'SolarBusV', 'WindBusV', 'ChgBusV', 'BrkAccPres', 'BrkCylPres',
              'HighPld1Crnt', 'HighPld2Crnt', 'HighPld3Crnt', 'HighPld4Crnt', 'BallastPres', 'TopHumidity',
              'TopTemp', 'HVP_GndV', 'HVN_GndV', 'Spare420mA', 'AlogSpare1', 'AlogSpare2', 'AlogSpare3',
              'BETA', 'Igenset', 'AIMS1', 'AIMS2', 'AvgRMSVel', 'HighestVel', 'AccumPos', 'ZeroUpCross',
              'AvgPostion', 'HVelCount', 'UpImpCnt', 'LoImpCnt', 'AvgDumpPwr', 'AvgGenPwr', 'OilSpeedCmnd',
              'AccXFltMax', 'AccYFltMax', 'AccZFltMax', 'LoadFltAbsMax', 'HW_Serial', 'SW_Build', 'Spare1',
              'Spare2', 'DriveParam1', 'DriveParam2', 'DriveParam3', 'DriveParam4', 'DriveParam5', 'Batt1SOC',
              'Batt2SOC', 'Batt3SOC', 'Batt4SOC', 'BatLog1', 'BatLog2', 'BatLog3', 'DumpLoad', 'Latitude',
              'Longitude', 'State', 'PTOStatus', 'DI_15_0', 'DI_31_16', 'DO_15_0', 'DO_31_16', 'AlrmGroup1',
              'AlrmGroup2', 'AlrmGroup3', 'AlrmGroup4', 'AlrmGroup5','CPUPercent', 'Storage', 'FileSizekB',
              'StateTmr', 'ClockDiff', 'ParamAddress', 'ParamValue']
    pare_options = ["Raw Data","1:10 Sample Rate","1:20 Sample Rate",
                    "1:50 Sample Rate","1:100 Sample Rate",
                    "1:1000 Sample Rate","1:5000 Sample Rate"]
    pareModulo = [0,10,20,50,100,1000,5000]
    assets = ["TB1", "TB2", "SWPB-001", "PB3-005", "HWIL-OPT"]

class CheckableComboBox(QComboBox):
    texts = ""
    # Subclass Delegate to increase item height
    class Delegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            size.setHeight(20)
            return size

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the combo editable to set a custom text, but readonly
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.texts = ""
        # Make the lineedit the same color as QPushButton
        palette = qApp.palette()
        palette.setBrush(QPalette.Base, palette.button())
        self.lineEdit().setPalette(palette)
        # Use custom delegate
        self.setItemDelegate(CheckableComboBox.Delegate())
        # Update the text when an item is toggled
        self.model().dataChanged.connect(self.updateText)
        # Hide and show popup when clicking the line edit
        self.lineEdit().installEventFilter(self)
        self.closeOnLineEditClick = False
        # Prevent popup from closing when clicking on an item
        self.view().viewport().installEventFilter(self)

    def resizeEvent(self, event):
        # Recompute text to elide as needed
        self.updateText()
        super().resizeEvent(event)

    def eventFilter(self, object, event):

        if object == self.lineEdit():
            if event.type() == QEvent.MouseButtonRelease:
                if self.closeOnLineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return False

        if object == self.view().viewport():
            if event.type() == QEvent.MouseButtonRelease:
                index = self.view().indexAt(event.pos())
                item = self.model().item(index.row())

                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                return True
        return False

    def showPopup(self):
        super().showPopup()
        # When the popup is displayed, a click on the lineedit should close it
        self.closeOnLineEditClick = True

    def hidePopup(self):
        super().hidePopup()
        # Used to prevent immediate reopening when clicking on the lineEdit
        self.startTimer(100)
        # Refresh the display text when closing
        self.updateText()

    def timerEvent(self, event):
        # After timeout, kill timer, and reenable click on line edit
        self.killTimer(event.timerId())
        self.closeOnLineEditClick = False

    def clearAll(self):
        for i in range(self.model().rowCount()):
            self.model().item(i).setCheckState(Qt.Unchecked)
            self.setCurrentIndex(-1)

    def updateText(self):
        texts = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                if self.model().item(i).text() == "Clear selections":
                    text = ""
                    self.clearAll()
                    break
                else:
                    texts.append(self.model().item(i).text())
        text = ", ".join(texts)
        self.texts = texts
        

        # Compute elided text (with "...")
        metrics = QFontMetrics(self.lineEdit().font())
        elidedText = metrics.elidedText(text, Qt.ElideRight, self.lineEdit().width())
        self.lineEdit().setText(elidedText)

    def addItem(self, text, data=None):
        item = QStandardItem()
        item.setText(text)
        if data is None:
            item.setData(text)
        else:
            item.setData(data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, texts, datalist=None):
        for i, text in enumerate(texts):
            try:
                data = datalist[i]
            except (TypeError, IndexError):
                data = None
            self.addItem(text, data)

    def currentData(self):
        # Return the list of selected items data
        res = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                res.append(self.model().item(i).data())
        return res

### Stateful classes ###
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=Vals.h, height=Vals.v, dpi=200):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)        
        super(MplCanvas, self).__init__(fig)

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        No data
    error
        tuple (exctype, value, traceback.format_exc() )
    result
        object data returned from processing, anything
    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    #result = pyqtSignal(object)
    result = pyqtSignal(tuple)

class Worker(QRunnable):
    '''
    Worker thread
    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    '''
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn( *self.args, **self.kwargs) 
        except:
            print( "Entered Exception" )
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            try:
                self.signals.result.emit(result)  # Return the result of the processing
            except Exception as e:
                print(e)
                pass
                
        finally:
            self.signals.finished.emit()  # Done
            
class EmittingStream(QObject):
    textWritten = pyqtSignal(str)
    def write(self, text):
        self.textWritten.emit(str(text))

class AnotherWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent,
    it will appear as a free-floating window.
    """
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.vgridabel = QLabel("Another Window")
        layout.addWidget(self.vgridabel)
        self.setLayout(layout)

class Data(list):
    def __init__(self):
        super().__init__()


            ### Toggle settings and radio button
##        ra = QLabel()
##        ra.setText("")
##        ra.setFrameShape(QFrame.VLine)
##        radioA = QRadioButton()
##        radioA.setText("ARPA Only")
##        radioA.clicked.connect(lambda checked: self.set_targets( radioA.text() ))
##        radioB = QRadioButton()
##        radioB.setText(" AIS Only")
##        radioB.clicked.connect(lambda checked: self.set_targets( radioB.text() ))
##        radioC = QRadioButton()
##        radioC.setText("All Targets")
##        radioC.clicked.connect(lambda checked: self.set_targets( radioC.text() ))
##        for radio in (radioA,radioB,radioC):
##            AssetColN.addWidget(radio)            

