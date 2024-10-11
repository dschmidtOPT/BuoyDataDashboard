#!/usr/bin/python3
import os
import sys
import time
import blosc
import pickle
import traceback
import datetime
import numpy as np
import pandas as pd
from PIL import Image
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from datetime import datetime
from screeninfo import get_monitors
#from PySide6.QtCore import QDateTime

import matplotlib.pyplot as plt
from matplotlib import transforms
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT 

## Relative library imports ##
sys.path.append( os.path.abspath( os.getcwd( ) ) )
from Logger import icons
import Utils, Parser

### Helper functions
def open_image(path_to_image, rotation=0):
    image = Image.open(path_to_image) # Open the image
    if rotation:
        image = image.rotate(rotation)
    image_array = np.array(image) # Convert to a numpy array
    return image_array # Output

def exception_hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._excepthook(exctype, value, traceback) 
    sys.exit(1)


### Application Code ###
class MainWindow(QMainWindow):
    '''
    Generates main GUI window
    '''
    keys = []
    data = {}
    lines = []
    labels = []
    twins = []
    def __init__(self,qapp):
        super().__init__()
        self.threadpool = QThreadPool( )
        self.threadpool.daemon = True
        self.states = Utils.States()
        self.worker = None
        self.setupUI()
        
        self.qapp = qapp
        if Utils.Vals.embedded_log:
            self.setupThread( self.stdout_assignment )
            self.setupThread( self.stderr_assignment )
        #self.startTimer()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        self.show()
        for line in Utils.Msg.startup:
            print(line)
        self.qapp.processEvents()

    def setupUI( self ):
        pwd = os.getcwd( )
        self.setWindowIcon( self.setupThumbnail( ) )
        self.setWindowTitle( "Buoy Data Dashboard" )
        logo = QLabel( self )
        logo.setFrameShape( QFrame.HLine )

        ## Adjust to window size ##
        pixmap = QPixmap( os.path.join(pwd,"Logger","icons","OPTfulllogo.png" ) )
        Utils.Vals.h = int( pixmap.width( ) )
        Utils.Vals.v = int( pixmap.width( )*Utils.Vals.gr )
        for m in get_monitors( ):
            if m.is_primary:
                break
        Utils.Vals.win_w = m.width
        Utils.Vals.win_h = m.height

        ## Select layout based upon size of screen.  
        if Utils.Vals.win_h < 0.5 * Utils.Vals.v:
            pixmap = QPixmap( os.path.join(pwd,"Logger","icons","OPTlogo.png" ) )
            Utils.Vals.h = 2 * int( pixmap.width( ) )
            Utils.Vals.v = int( pixmap.width( )*Utils.Vals.gr )
            Utils.Vals.horzLayout = True
            myFont=QFont( 'Ubuntu', 12, QFont.Bold )
        elif Utils.Vals.win_h < Utils.Vals.v:
            pixmap = QPixmap( os.path.join(pwd,"Logger","icons","OPTlogo.png" ) )
            Utils.Vals.h = int( Utils.Vals.win_w*.975 ) # 5 * int(pixmap.width())
            Utils.Vals.v = int( Utils.Vals.win_h*.950 ) #5 *int( pixmap.width())
            Utils.Vals.horzLayout = True
            myFont=QFont( 'Ubuntu', 9, QFont.Bold )
        else:
            myFont=QFont( 'Ubuntu', 14, QFont.Bold )

        toprowHeight = int( 0.22*Utils.Vals.v )

        self.resize( Utils.Vals.h , Utils.Vals.v )
        logo.setPixmap( pixmap )
        self.window1 = Utils.AnotherWindow( ) 
        self.window2 = Utils.AnotherWindow( )

        ## Setup widgets ##
        if Utils.Vals.horzLayout:
            self.wide_h = QHBoxLayout( )
        self.hgrid = QHBoxLayout( )
        self.vgrid = QVBoxLayout( )
        top_vert = QVBoxLayout( )
        self.vgrid.addWidget( logo )
        horiz = QHBoxLayout( )
        AssetColA = QVBoxLayout( )
        AssetColM = QVBoxLayout( )
        AssetColR = QVBoxLayout( )

        ## Text output console ##
        text_layout = QVBoxLayout( )
        self.text_edit = QTextEdit( )
        self.text_edit.setStyleSheet(Utils.Styles.bg)
        self.text_edit.setMaximumHeight( toprowHeight )
        self.text_edit.resize( int(0.20*Utils.Vals.h), toprowHeight )
        AssetColA.addWidget( self.text_edit )

        ## Data Operations Buttons
        l1 = QLabel( ); l1.setText( "Data Management" ); l1.setFrameStyle( QFrame.Raised )
        l1.setLineWidth( 3 )
        l1.setFont( myFont )
        l1.setAlignment(Qt.AlignCenter)
        #l1.setFrameShape(QFrame.VLine)
        AssetColM.addWidget( l1)
        
        # Populate logos:
        icons = {icon.split( "." )[0] : QPixmap( icon ) for icon in
                 os.listdir( os.path.join( os.getcwd(), "Logger", "icons" ))}
        self.setStatusBar( QStatusBar(self) )
        #self.cmp_button = QPushButton( "Compress Dataset" )
        #self.cmp_button.setStyleSheet(Utils.Styles.bg)
        #self.cmp_button.clicked.connect( lambda: self.fileIO_kickoff(self.compress_dataset) )
        #AssetColM.addWidget( self.cmp_button )
        button2 = QPushButton( "Compress Data" )
        button2.setStyleSheet( Utils.Styles.buttons )
        button2.clicked.connect( lambda: self.fileIO_nonThreadKickoff( self.build_metric ) )
        #button2.clicked.connect( self.build_metric )
        button = QPushButton( "Process Data" )
        button.setStyleSheet( Utils.Styles.buttons )
        button.clicked.connect( lambda: self.fileIO_nonThreadKickoff( self.build_metric ) )
        button3 = QPushButton("Power Stat Calc")
        button3.setStyleSheet( Utils.Styles.buttons )
        button3.clicked.connect( self.calculate_power_gen )
        AssetColM.addWidget( button2 )
        AssetColM.addWidget( button )
        AssetColM.setAlignment(Qt.AlignCenter)
        l1 = QLabel()
        l1.setText("Data Processing" ); l1.setFont( myFont ); l1.setAlignment(Qt.AlignCenter)
        AssetColM.addWidget( l1 )  
        button =  QPushButton("Max Date Range")
        button.setStyleSheet( Utils.Styles.buttons )
        button.clicked.connect( self.reset_dates )
        plotting_all = QPushButton("Generate Plots")
        plotting_all.clicked.connect( self.build_report )
        plotting_all.setStyleSheet( Utils.Styles.buttons )
        AssetColM.addWidget( button3 )
        AssetColM.addWidget( button )
        AssetColM.addWidget( plotting_all )
        #AssetColM.addWidget( button )

        ### Calendar #################
        AssetColL = QVBoxLayout()
        AssetColZ = QVBoxLayout()        
        self.dateA = QCalendarWidget(self)
        self.dateA.setCursor(Qt.PointingHandCursor)
        self.dateA.setFixedSize(QSize(int(0.215*Utils.Vals.win_w), int(.82*toprowHeight )))
        self.dateA.setStyleSheet("border : 1px solid black;"
                                 "color: black;")
        self.dateA.adjustSize()
        
        self.dateB = QCalendarWidget(self)
        self.dateB.setCursor(Qt.PointingHandCursor)
        self.dateB.setFixedSize(QSize(int(0.215*Utils.Vals.win_w), int(.82*toprowHeight )))
        self.dateB.setStyleSheet("border : 1px solid black;"
                                 "color: black;")
        self.dateB.adjustSize()
        
        Utils.Vals.startDate = self.dateA.selectedDate()
        Utils.Vals.endDate = self.dateB.selectedDate()
        
        self.dateEditA = QDateTimeEdit( QDateTime.currentDateTime( ) )
        self.dateEditA.setFixedSize( QSize( int( 0.165*Utils.Vals.win_w ), int( .1*toprowHeight ) ) )
        self.dateEditA.setDisabled( False )
        self.dateEditA.setStyleSheet( "background-color: white" )
        self.dateEditA.setDisplayFormat( "yyyy.MM.dd hh:mm:ss" )
        self.dateEditB = QDateTimeEdit( QDateTime.currentDateTime( ) )
        self.dateEditB.setFixedSize( QSize( int( 0.165*Utils.Vals.win_w ), int( .1*toprowHeight ) ) )
        self.dateEditB.setDisabled( False )
        self.dateEditB.setStyleSheet( "background-color: white" )
        self.dateEditB.setDisplayFormat( "yyyy.MM.dd hh:mm:ss" )
        self.dateA.clicked.connect( lambda: self.unifyStartDate(self.dateA.selectedDate(), self.dateEditA ) )
        self.dateB.clicked.connect( lambda: self.unifyEndDate(self.dateB.selectedDate(), self.dateEditB ) )

        #dateA.editingFinished.connect(lambda: date_method(which="START"))
        #dateB.editingFinished.connect(lambda: date_method(which="END"))
        AssetColL.addWidget( self.dateA )
        h = QHBoxLayout()
        l1 = QLabel("Data Start:")
        l1.setFont( myFont )
        l1.setAlignment( Qt.AlignLeft | Qt.AlignVCenter)
        h.addWidget( l1 )
        h.addWidget( self.dateEditA )
        AssetColL.addLayout( h )
        
        AssetColZ.addWidget( self.dateB )
        l1 = QLabel("Data End:")
        l1.setFont( myFont )
        l1.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        h = QHBoxLayout()
        h.addWidget( l1 )
        h.addWidget( self.dateEditB )
        AssetColZ.addLayout( h )
        
        horiz.addLayout( AssetColM )
        horiz.addLayout( AssetColA )
        
        horiz.addLayout( AssetColL )
        horiz.addLayout( AssetColZ )
        self.vgrid.addLayout( horiz )
        
        ### Plot controls and plot area
        tv = QVBoxLayout( )
        ### File browser
        file_browse = QPushButton( 'Browse' )
        file_browse.setStyleSheet( Utils.Styles.buttons )
        file_browse.clicked.connect( self.open_file_dialog )
        self.filename_edit = QLineEdit( )
        self.filename_edit.setFixedSize( QSize( int( 0.3815*Utils.Vals.win_w), int(.1*toprowHeight ) ) )
        self.filename_edit.setStyleSheet("background-color: white")

        ### Dropdown combo boxes
        self.pare_control = QComboBox(  )
        self.pare_control.setStyleSheet("background-color: white")
        self.pare_control.setEditable(False)
        for el in Utils.Vals.pare_options:
            self.pare_control.addItem( el )
        self.pare_control.setGeometry(0, 80, 100, 20)
        self.pare_control.setStyleSheet(Utils.Styles.bg)
        self.pare_control.move( -280, 120 )
        self.pare_control.currentIndexChanged.connect( self.dropdownChanged )
        #i = self.pare_control.findText( self.states.selected_pare , Qt.MatchFixedString )
        self.pare_control.setCurrentIndex( 0 )      
        self.key_select = Utils.CheckableComboBox(  )
        self.key_select.setStyleSheet(Utils.Styles.bg)
        self.key_select.addItems( Utils.Vals.keylib )
        i = self.key_select.findText( self.states.selected_key, Qt.MatchFixedString )
        self.key_select.setCurrentIndex( 0 )

        ### Progress Bar
        self.progress = QProgressBar()
        self.progress.setGeometry(200, 80, 250, 20)
        self.progress.setValue(0)

        self.subprogress = QProgressBar( )
        self.subprogress.setGeometry( 200, 80, 250, 20 )
        self.subprogress.setValue( 0)
        self.subprogress.setVisible( False )

        sample = QLabel( "Sample Rate:" )
        sample.setAlignment( Qt.AlignRight | Qt.AlignVCenter )
        sample.setFont( myFont )
        sample.setFixedWidth( 100 )
        selected = QLabel( "Selected Columns:" )
        selected.setAlignment( Qt.AlignRight | Qt.AlignVCenter )
        selected.setFont( myFont )
        selected.setFixedWidth( 140 )
        hu = QHBoxLayout( )
        hb = QHBoxLayout( )
        b1 = QCheckBox( "CSV Output" )
        b1.setChecked( False )
        b1.stateChanged.connect( lambda:self.CSVbtnstate( b1 ) )
        b2 = QCheckBox( "Plot Column Stats" )
        b2.setChecked( False )
        b2.stateChanged.connect( lambda:self.trendbtnstate( b2 ) )
        b3 = QCheckBox( "Show Gridlines" )
        b3.setChecked( True )
        b3.stateChanged.connect( lambda:self.gridbtnstate( b3 ) )
        ql = QLabel(self)
        ql.setFrameShape(QFrame.VLine)
        clearlog = QPushButton('Clear Log')
        button =  QPushButton("Export Log")
        button.setStyleSheet(Utils.Styles.buttons )
        clearlog.setStyleSheet(Utils.Styles.buttons )
        button.clicked.connect( self.export_log )
        clearlog.clicked.connect( self.text_edit.clear )
        hu.addWidget( b1 )
        hu.addWidget( b2 )
        hu.addWidget( b3 )
        l = QLabel( '' )
        hu.addWidget( l )
        hu.addWidget( l )
        hu.addWidget( l )
        hu.addWidget( l )
        hu.addWidget( l )
        hu.addWidget( clearlog )
        hu.addWidget( button )
        l = QLabel( 'Data Path:' )
        l.setAlignment( Qt.AlignRight | Qt.AlignVCenter )
        
        hu.addWidget( self.filename_edit )
        hu.addWidget( file_browse )
        self.l = QLabel( "Completion:" )
        
        self.l.setVisible( False )
        self.progress.setVisible( False )
        hu.addWidget( self.l )
        hu.addWidget( self.progress )

        tv.addLayout( hu )
        tv.addLayout( hb )
            
        self.vgrid.addLayout( tv )
        self.timer=QTimer()
        self.timer.timeout.connect(lambda: self.eventLoop)
        plotbtn = QPushButton('Plot Columns')
        plotbtn.clicked.connect( self.build_plots )
        plotbtn.setStyleSheet( Utils.Styles.plotbutton )

        clearbtn = QPushButton('Clear Plot')
        clearbtn.clicked.connect( self.clear_plots )
        save = QPushButton("Save Plot")
        save.clicked.connect( self.save_cfg )
        hlpbtn = QPushButton("Help")
        hlpbtn.clicked.connect( self.open_hlp )
        h = QHBoxLayout()
        ln = QLabel("")
        ql = QLabel("")
        ql.setFrameShape(QFrame.VLine)
        h.addWidget( plotbtn )
        for wid in ( selected,self.key_select, sample, self.pare_control, save,clearbtn, ql, hlpbtn):
            if not isinstance(wid,QLabel) and not isinstance(wid,QComboBox):
                wid.setStyleSheet( Utils.Styles.buttons )
            h.addWidget( wid )
        self.vgrid.addLayout( h )
        ### --- Plot stuff --------
        self.sc = Utils.MplCanvas(self, width=Utils.Vals.win_w*.96, height=3*Utils.Vals.v, dpi=300)      
        toolbar = NavigationToolbar2QT(self.sc, self)
        ## Intro scene
        Fs = 8000
        waves = 2.5
        sample = 8000
        sky = (169/255.0, 215/255.0, 252/255.0)
        opt_blue = (7/255.0, 60/255.0, 100/255.0)
        x = np.arange(sample)
        y = np.sin(1.5 * np.pi * waves * x / Fs)
        top = np.ones(sample)*4.5
        self.sc.figure.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
        PB3 = open_image(os.path.join(pwd,"Logger","Icons","PB3.png"), rotation=-5)
        TB = open_image(os.path.join(pwd,"Logger","Icons","TB.png"), rotation=2)
        self.sc.axes.set_ylim(-2,4.5)
        self.sc.axes.set_xlim(0,sample)
        self.sc.axes.plot(x,y,'-w')
        self.sc.axes.plot(x,top,linestyle="-",color=sky)
        self.sc.axes.fill_between(x, y, top, color=sky)
        self.sc.axes.fill_between(x, -2, y, color=opt_blue)
        self.ax_image_PB3 = self.sc.figure.add_axes([0.16, 0.15, 0.45, 0.3])
        self.ax_image_PB3.axis( 'off' )
        self.ax_image_PB3.imshow(PB3)
        self.ax_image_TB = self.sc.figure.add_axes([0.5, 0.40, 0.3, 0.375])
        self.ax_image_TB.axis( 'off' )
        self.ax_image_TB.imshow(TB)

        bottom = QVBoxLayout()
        bottom.addWidget(self.sc)
        bottom.addWidget(toolbar)
        self.vgrid.addLayout( horiz )
        self.vgrid.addLayout( bottom )       
        widget = QWidget()
        widget.setLayout(self.vgrid)
        widget.setStyleSheet(Utils.Styles.OPTlogobg)
        self.setCentralWidget(widget)

    def print_output(self, s):
        print(s)

    def update_progress(self, s):
        self.progress.setValue( s[0] )
        if s[0] == 100:
            time.sleep(0.5)
            self.progress.setValue( 0 )
            self.progress.setVisible( False )
            self.l.setVisible(False)
            print("Operation completed.")
        if s[1]:
            self.progress.setValue( 0 )
            self.progress.setVisible( False )
            self.l.setVisible(False)
            print(f"Metric build completed.")

    def finished(self):
        print("Thread finished")

    def stdout_assignment(self):
        sys.stdout = Utils.EmittingStream(textWritten=self.normalOutputWritten)
        return (0,0)

    def stderr_assignment(self):
        sys.stderr = Utils.EmittingStream(textWritten=self.normalOutputWritten)
        return (0,0)

    def reset_dates( self ):
        '''Adjusts the calendar and stored date bounds to the earliest and latest
           datapoints
        '''
        ### If there are already stored maxima, dont open the Timeseries.dat ###
        if self.states.t0 and self.states.tN:
            self.states.startDate = self.states.t0
            self.states.endDate = self.states.tN
            startlabel = start.strftime("%m/%d/%Y %H:%M:%S")
            endlabel = end.strftime("%m/%d/%Y %H:%M:%S")
            self.dateEditA.setDateTime(
                QDateTime( start.year,
                           start.month,
                           start.day,
                           start.hour,
                           start.minute,
                           start.second) )
            self.dateEditB.setDateTime(
                QDateTime( end.year,
                           end.month,
                           end.day,
                           end.hour,
                           end.minute,
                           end.second) )
            print(f"Expanded date range to first and final timestamp:\n \
            {startlabel} --> {endlabel}")
            return 
        if not Utils.Vals.dir_path:
            if not self.open_dir_dialog( ):
                return
        base_path = Utils.Vals.dir_path
        if not os.path.exists( os.path.join( base_path, "Timeseries.dat" ) ):
            self.acknowledge_window( 'Expected date datastructure "Timeseries.dat" not found.  Try running "Process Data".')
            Utils.Vals.dir_path = None
            self.filename_edit.setText("")
            return
        fname = os.path.join( base_path, "Timeseries.dat" )
        df = Parser.read_pickle( fname )
        df = Parser.clean_whitespace( df )
        start = datetime.fromisoformat( df['Timeseries'].values[0].astype(str) )
        self.dateA.setSelectedDate( QDate( start.year, start.month, start.day ) )
        end = datetime.fromisoformat( df['Timeseries'].values[-1].astype(str) )
        self.dateB.setSelectedDate( QDate( end.year, end.month, end.day ) )
        self.states.startDate = start
        self.states.endDate = end
        ### Set dataset maxima timestamps so they do not need to be calculated again ###
        self.states.t0 = start
        self.states.tN = end
        startlabel = start.strftime("%m/%d/%Y %H:%M:%S")
        endlabel = end.strftime("%m/%d/%Y %H:%M:%S")
        self.dateEditA.setDateTime(
            QDateTime( start.year,
                       start.month,
                       start.day,
                       start.hour,
                       start.minute,
                       start.second) )
        self.dateEditB.setDateTime(
            QDateTime( end.year,
                       end.month,
                       end.day,
                       end.hour,
                       end.minute,
                       end.second) )
            
        print(f"Expanded date range to first and final timestamp:\n \
        {startlabel} --> {endlabel}")
        return
                                           
        
            

    def open_hlp(self):
        pwd = os.getcwd()
        hlpname = os.path.join( pwd, "README.md" )
        if os.path.exists( hlpname ):
            os.system( f"start notepad.exe {hlpname}" )

    def fileIO_nonThreadKickoff(self, func):    
        if not Utils.Vals.dir_path:
            if not self.open_dir_dialog( ):
                return
        self.states.thread_running = True
        self.currentThread =  func( Utils.Vals.dir_path )
        self.states.thread_running = False
        return

    def fileIO_kickoff(self, func):
        
        if not Utils.Vals.dir_path:
            if not self.open_dir_dialog( ):
                return
        self.states.thread_running = True
        self.currentThread = self.setupThread( func, args=Utils.Vals.dir_path )
        self.states.thread_running = False
        return

    def compress_dataset( self, data_path ):
        print("Compressing dataset and grabbing table keys...")
        data_dirs = [f for f in os.listdir( data_path ) if
                     ( f.find( "Folder_") != -1 ) ] #and os.path.isdir( f ) ]
        problematic = []
        numdirs = len(data_dirs)
        print(f'There are {numdirs} directories for processing')
        for i,subdir in enumerate(data_dirs):
            self.instance = i
            self.progress.setValue( int( np.round( (i + 1 ) / numdirs *100)) )
            df_merged = pd.DataFrame({})
            files = os.listdir( os.path.join( data_path, subdir ) )
            if "combinedDF.dat" in files:
                if self.keys:
                    continue  # Dont compress and overwrite a file if it already exists
            for dat_file in files:
                fname = os.path.join( data_path, subdir, dat_file )
                try: 
                    df = pd.read_csv(fname, sep ="\t")
                    if not self.keys: self.keys = Parser.grab_keys( df )
                except Exception as e:
                    if "combinedDF" in fname:
                        continue
                    else: problematic.append(fname)
                df_merged = Parser.soft_merge( df_merged, df, index=True)
            #For each data directory, create one compressed binary pickle file
            Parser.pickle_df( os.path.join( data_path, subdir, "combinedDF.dat" ), df_merged )
        print( "Files compressed to ./Folder_###/combinedDF.dat" )
        self.progress.setValue( 0 )
        if problematic:
            print( "The following input files were skipped:" )
            for problem in problematic:
                print(problem)
        return 0

    def threaded_df_merge( self, args ):
        [ keynum, numkeys, data_dirs, column_name, newname, csvname] = args
        Utils.Vals.increment += 1
        progressA = int( np.round( ( Utils.Vals.increment + 1 ) / numkeys *100 ) )
        start = time.time()
        df_merged = pd.DataFrame({column_name:[]})
        data = Utils.Data()
        dirlen = len(data_dirs)
        for subdir in data_dirs:
            fname = os.path.join( Utils.Vals.dir_path, subdir, "combinedDF.dat" )
            try:
                df = Parser.read_pickle( fname, [column_name] )
            except Exception as e:
                print(f"Problem processing {fname}, skipping.")
                df = pd.DataFrame( { } )
            data.extend(df[ column_name ].to_list( ))
        df_merged[ column_name ] = pd.Series( data ) 
        df_merged.reset_index( drop=True, inplace=True )
        if self.states.CSV_output:
            df_merged.to_csv( newname.split(".dat")[ 0 ] + ".csv" )
        if not os.path.exists( newname ):
            Parser.pickle_df( newname, df_merged )
        duration = time.time() - start
        ### Add a tuple of keys to be popped as completed, and set return int based on this completion
        print(f"Finished {column_name} operations in {duration}s")
        return ( progressA, int( Utils.Vals.increment == numkeys  ) )

    def threaded_timeseries( self, args ):
        [ data_path, timeout ] = args
        Utils.Vals.increment += 1
        start = time.time()
        df = pd.DataFrame({"Timeseries":[]})
        fnD = os.path.join( data_path, "Date_full.dat" )
        dfD = Parser.read_pickle( fnD )
        dfD = Parser.clean_whitespace( dfD )
        
        fnT = os.path.join( data_path, "Time_ms_full.dat" ) 
        dfT = Parser.read_pickle( fnT )
        dfT = Parser.clean_whitespace( dfT )
            
        fullDF = pd.concat(
            [ dfD.reset_index( drop=True ),
            dfT.reset_index( drop=True ) ], axis=1 )
        
        estimate = int(fullDF.shape[0] * .000016123127)
        print( f"""Kicking off Timeseries string -> datetime object conversion.
This will take a long time.  Based on the size of the dataset,
it will take an estimated {estimate}s.  Thank you for your patience.""" )
        stamp = time.time()
        df['Timeseries'] = fullDF.apply(lambda x: Parser.datestamper(x.Date, x.Time_ms), axis=1 )
        duration = time.time() - stamp
        print(f"from ISO datetime conversion operation completed in {duration}s.")
        Parser.pickle_df( os.path.join( data_path, "Timeseries.dat"), df )
        progressA = int( np.round( ( Utils.Vals.increment + 1 ) / numkeys *100 ) )
        self.progress.setValue( progressA )
        return ( progressA, int( Utils.Vals.increment == numkeys  ) )

    def threaded_df_merge( self, args ):
        [ keynum, numkeys, data_dirs, column_name, newname, csvname] = args
        Utils.Vals.increment += 1
        progressA = int( np.round( ( Utils.Vals.increment + 1 ) / numkeys *100 ) )
        start = time.time()
        df_merged = pd.DataFrame({column_name:[]})
        data = Utils.Data()
        dirlen = len(data_dirs)
        for subdir in data_dirs:
            fname = os.path.join( Utils.Vals.dir_path, subdir, "combinedDF.dat" )
            try:
                df = Parser.read_pickle( fname, [column_name] )
            except Exception as e:
                print(f"Problem processing {fname}, skipping.")
                df = pd.DataFrame( { } )
            data.extend(df[ column_name ].to_list( ))
        df_merged[ column_name ] = pd.Series( data ) 
        df_merged.reset_index( drop=True, inplace=True )
        if self.states.CSV_output:
            df_merged.to_csv( newname.split(".dat")[ 0 ] + ".csv" )
        if not os.path.exists( newname ):
            Parser.pickle_df( newname, df_merged )
        duration = time.time() - start
        ### Add a tuple of keys to be popped as completed, and set return int based on this completion
        print(f"Finished {column_name} operations in {duration}s")
        return ( progressA, int( Utils.Vals.increment == numkeys  ) )
  

    def build_metric( self, data_path = None ):
        found = False
        try:
            subdirs = os.listdir( data_path )
            for subdir in subdirs:
                if "Folder_" in subdir:
                    found = True
                    break
            if not found:
                self.acknowledge_window( f"Folder_### directories cannot be found in provided directory, aborting." )
                Utils.Vals.dir_path = None
                self.filename_edit.setText("")
                return
        except:
            self.acknowledge_window( f"Folder_### directories cannot be found in provided directory, aborting." )
            Utils.Vals.dir_path = None
            self.filename_edit.setText("")
            return
            
        keys = self.keys
        data_dirs = [ f for f in subdirs if ( f.find( "Folder_") != -1 ) ]
        Utils.Vals.timeseries = [ key for key in keys if ( "date" in key.lower() or 
                                               "time" in key.lower() ) ]
        self.progress.setVisible( True )
        self.l.setVisible(True)
        if not keys:
            keys = Parser.key_peek( data_path, data_dirs )
        numkeys = len( keys )
        numdirs = len( data_dirs )
        
        print("\nHeads up: This operation takes a long time.  Expect ~2min per GB of raw data.")
        for keynum, column_name in enumerate( keys ):
            if ( column_name == ' ' ):  # We dont want to filter on timestamp, alternate criteria
                continue
            output_name = column_name.replace( " ", "" )  # Remove whitespace from column names to create a file name
            newname  = os.path.join( data_path, f"{output_name}_full.dat" )
            csvname = os.path.join( data_path, f"{output_name}_full.csv" )
            progressA = int( np.round( ( Utils.Vals.increment ) / numkeys *100 ) )
            if os.path.exists( newname ) and not self.states.CSV_output:
                print( f"{newname} exists, skipping overwrite." )
                Utils.Vals.increment += 1
                self.progress.setValue( progressA )
                continue
            elif os.path.exists( newname ) and (self.states.CSV_output and os.path.exists( csvname )):
                print( f"{newname} and {csvname} exists, skipping overwrite." )
                Utils.Vals.increment += 1
                self.progress.setValue( progressA )
                continue
            else:
                print( f"Kicking off {column_name} dataset merge and compression..." )
                self.setupThreadQuick( self.threaded_df_merge,
                                       ( keynum, numkeys, data_dirs, column_name, newname, csvname ) )

        ### Build timeseries dataset once so it doesnt have to be calculated on every plot ###
        if os.path.exists( os.path.join( data_path, "Timeseries.dat" ) ):
            print( "Timeseries.dat exists, skipping overwrite." )
            return 0
        timeout = 0
        while not ( os.path.exists( os.path.join( data_path, "Date_full.dat" ) )
                and os.path.exists( os.path.join( data_path, "Time_ms_full.dat" ) ) ) and \
                timeout < 15 :
            print("Date and Time_ms datasets not completed yet, waiting 20s")
            time.sleep(30)
            timeout += 1

        self.setupThreadQuick( self.threaded_timeseries, (data_path, numkeys) ) 
        return 0
            
    def normalOutputWritten(self, text):
        """Append text to the QTextEdit."""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()

    def setupThreadQuick(self,func, args):
        # Pass the function to execute
        self.worker = Utils.Worker(func, args) # Any other args, kwargs are passed to the run function
        self.worker.signals.result.connect( self.update_progress )        
        # Execute thread
        self.threadpool.start(self.worker)
        self.qapp.processEvents()
        return (0,0)

    def setupThread( self, func, args=None, result=True, logging = False ):
        # Pass the function to execute
        if args:
            self.worker = Utils.Worker( func, args ) # Any other args, kwargs are passed to the run function
        else:
            self.worker = Utils.Worker( func )
        if logging:
            if result:
                self.worker.signals.result.connect( self.update_progress )
            else:
                self.worker.signals.result.connect( self.print_output )
            self.worker.signals.finished.connect( self.finished )
        # Execute thread
        self.threadpool.start(self.worker)
        self.qapp.processEvents()
        return (0,0)

    def __del__( self ):
        sys.stdout = sys.__stdout__ 
           
    def eventLoop( self ):
        '''
        Runs every ms_delay milliseconds on main thread, and checks states of
        MainWindow attributes adjusted by worker threads.
        '''
        print("Running event loop")
        self.qapp.processEvents()
        if self.states.thread_running:
            print("Running thread")
            self.progress.setValue ( self.states.progress_barA )
            if self.states.multi_progress:
                self.subprogress.setValue ( self.states.progress_barB )
                
    def startTimer( self, ms_delay = Utils.Vals.event_delay ):
        self.timer.start( ms_delay ) # Cycle delay in millieseconds
        self.eventLoop( )
        
    def pauseTimer( self ):
        self.timer.stop( )
        self.startbtn.setEnabled( True )
        self.pausebtn.setEnabled( False )
        self.clearbtn.setEnabled( True )

    def doSomething(self):
        Utils.Msg.buffer = ""  # <-- temporary assignment, fill in this later.

    def open_dir_dialog(self):
        dirname = None
        while not dirname:
            dirname = str(QFileDialog.getExistingDirectory(self, 'Select parent directory holding "Folder_###" subdirectories'))
            if dirname == "":
                return 0
            Utils.Vals.dir_path = dirname
            self.filename_edit.setText(str(Utils.Vals.dir_path))
        return 1

    def save_file_dialog(self):
        filename = None 
        while not filename:
            filename, _ = QFileDialog.getSaveFileName(
                                self,
                                "Select a File",
                                "C:\\",
                                "Data Filess (*.dat *.txt)"
                                )
            if filename == "":
                return 0
        return filename

    def open_file_dialog(self):
        print("Select a file to plot between selected time bounds.")
        filename = None
        ok = True
        while (not filename and ok):
            filename, ok = QFileDialog.getOpenFileName(
                self,
                "Select a File", 
                "C:\\", 
                "Data Filess (*.dat *.txt)"
            )
            if filename:     
                Utils.Vals.file_path = os.path.abspath(filename)
                self.filename_edit.setText(str(Utils.Vals.file_path))         

    def CSVbtnstate( self,b):
        if b.isChecked():
            self.states.CSV_output = True
        else:
            self.states.CSV_output = False

    def trendbtnstate( self,b):
        if b.isChecked():
            self.states.trendline = True
        else:
            self.states.trendline = False
        if self.states.plotted:
            self.toggle_window( "Do you want to regenerate the plot with new options?" )
            
    def gridbtnstate( self,b):
        if b.isChecked():
            self.states.gridlines = True
        else:
            self.states.gridlines = False
        if self.states.plotted:
            self.toggle_window( "Do you want to regenerate the plot with new options?" )

    def acknowledge_window( self, msg ):
        widget = QWidget( )
        widget.setWindowTitle( "Warning" )
        qv = QVBoxLayout()
        l = QLabel( msg )
        l.setAlignment( Qt.AlignCenter | Qt.AlignVCenter )
        qv.addWidget( l )
        OK = QPushButton("OK")
        OK.setFixedWidth( int(Utils.Vals.h*0.075 ) )
        OK.setStyleSheet(Utils.Styles.bg)
        OK.clicked.connect(lambda: widget.close() )
        qv.addWidget( OK, alignment= Qt.AlignCenter )
        l = QLabel("")
        qv.addWidget( l )
        widget.setLayout( qv )
        widget.setStyleSheet( Utils.Styles.bg )
        widget.resize( int( Utils.Vals.h*0.15 ), int( Utils.Vals.v*0.10 ) )
        widget.show()
            
            
    def toggle_window( self, msg ):
        widget = QWidget( )
        widget.setWindowTitle( "Options" )
        qv = QVBoxLayout( )
        l = QLabel( msg )
        l.setAlignment( Qt.AlignCenter | Qt.AlignVCenter )
        qv.addWidget( l )
        qh = QHBoxLayout( )
        yes = QVBoxLayout( )
        no = QVBoxLayout( )
        ly = QPushButton( "Yes" )
        ly.clicked.connect( lambda: self.plot_toggle( widget ) )
        ly.setStyleSheet( Utils.Styles.bg )
        ln = QPushButton( "No" )
        ln.clicked.connect( lambda: widget.close( ) )
        ln.setStyleSheet( Utils.Styles.bg )
        qh.addWidget( ly )
        qh.addWidget( ln )
        qv.addLayout( qh )
        widget.setLayout( qv )
        widget.setStyleSheet( Utils.Styles.OPTlogobg )
        widget.resize( int( Utils.Vals.h*0.1 ), int( Utils.Vals.v*0.08 ) )
        widget.show( )
                        

    def unifyStartDate( self, dateObj, dateTimeEdit ):
        #import pdb; pdb.set_trace()
        oldTime = dateTimeEdit.dateTime( ).toString( "hh:mm:ss" )
        newDate = dateObj.toString( "yyyy-MM-dd" )
        composite = newDate + "-" + oldTime
        d = datetime.strptime( composite, "%Y-%m-%d-%H:%M:%S" )
        if d > self.states.endDate:
            revert = QDate(self.states.endDate.year,
                           self.states.endDate.month,
                           self.states.endDate.day)
            self.dateA.setSelectedDate( revert )
            self.acknowledge_window(f"""Invalid selection:
    "Date Start" selection must occur before or at selected "Data End".
    Please adjust selection to {composite} or earlier.""")
            
        else:
            self.states.startDate = d
            self.states.selectedDates = True
            self.dateEditA.setDate( dateObj )
            self.dateA.setSelectedDate( dateObj )
        #print("self.states: [startDate,endDate]:",self.states.startDate,self.states.endDate)

    def unifyEndDate( self, dateObj, dateTimeEdit ):
        #import pdb; pdb.set_trace()
        oldTime = dateTimeEdit.dateTime( ).toString( "hh:mm:ss" )
        newDate = dateObj.toString( "yyyy-MM-dd" )
        composite = newDate + "-" + oldTime
        d = datetime.strptime( composite, "%Y-%m-%d-%H:%M:%S" )
        if d < self.states.startDate:
            revert = QDate(self.states.startDate.year,
                           self.states.startDate.month,
                           self.states.startDate.day)
            self.dateB.setSelectedDate( revert )
            self.acknowledge_window(f"""Invalid selection:
    "Date End" selection must occur later than or at "Data Start".
    Please adjust selection to {composite} or later.""")
        else:
            self.states.endDate = d
            dateTimeEdit.setDate( dateObj )
            self.states.selectedDates = True
            self.dateEditB.setDate( dateObj )
            self.dateB.setSelectedDate( dateObj )

        #print("self.states: [startDate,endDate]:",self.states.startDate,self.states.endDate)

    def export_log(self):
        filename = self.save_file_dialog()
        if not filename:
            return
        with open(filename, 'w') as f:
            f.write(str(self.text_edit.toPlainText()))



    def plot_toggle( self, widget ):
        widget.close()
        self.build_plots()
            
    def calculate_power_gen(self):
        '''
        Outputs power production statistics across selected dates
        '''
        ### Open directory if no directory is already loaded. ###
        if not Utils.Vals.dir_path:
            if not self.open_dir_dialog( ):
                return
        base_path  = Utils.Vals.dir_path

        fullDF = pd.DataFrame({})
        once = False
        ### Get timeseries columns ###
        print("Building data vector.")
        for column in ["Date","Time_ms","ChgBusV","WindCrnt","SolarCrnt","ChgTo28VBusCrnt","ExtChgCrnt"] :
            ### If not Date_full.dat or Time_ms_full.dat exist in the base_path, abort
            if not os.path.exists( os.path.join( base_path, column + "_full.dat" )):
                self.acknowledge_window(f"{column} dataset cannot be found in provided directory, aborting.")
                Utils.Vals.dir_path = None
                return
            fname = os.path.join( base_path, column + "_full.dat" )
            df = Parser.read_pickle( fname )
            ### Pare dataset modulo is 
            if self.states.pareVal: 
                df = df.iloc[ ( df.index % self.states.pareVal == 0 ) ]
            df = Parser.clean_whitespace( df )
            if once:
                fullDF = pd.concat(
                [ fullDF.reset_index( drop=True ),
                 df.reset_index( drop=True ) ], axis=1 )
            else:
                once = True
                fullDF = df

        # Calculate custom columns
        print("Calculating composite columns")
        fullDF['WindChg'] = fullDF['ChgBusV']*fullDF['WindCrnt']
        fullDF['SolarChg'] = fullDF['ChgBusV']*fullDF['SolarCrnt']
         
    def dropdownChanged( self ):
        self.states.selected_pare = self.pare_control.currentText()
        i = self.pare_control.findText( self.states.selected_pare , Qt.MatchFixedString )
        self.states.pareVal = Utils.Vals.pareModulo[ i ] 
        
    def sliderMoved( self ):
        span = int(100.0 / len(Utils.Vals.assets)) #Max slider value
        ind = int(self.dial.value() / span)
        Utils.Vals.selectedAsset = Utils.Vals.assets[ ind % len(Utils.Vals.assets) ]
        self.pare_control.setCurrentText( Utils.Vals.selectedAsset )
        
    def onMyToolBarButtonClick(self, s):
        print("click", s)

    def setupThumbnail( self ):
        app_icon = QIcon()
        pwd = os.getcwd()
        imgpath = os.path.join(pwd, "Logger","icons","MDASicon.png")
        app_icon.addFile(imgpath, QSize(16,16))
        app_icon.addFile(imgpath, QSize(24,24))
        app_icon.addFile(imgpath, QSize(32,32))
        app_icon.addFile(imgpath, QSize(48,48))
        app_icon.addFile(imgpath, QSize(256,256))
        return app_icon

    def clear_plots( self ):
        self.sc.axes.cla()
        self.sc.axes.clear()
        for twin in self.twins:
            try:
                twin.cla()
                twin.clear()
                twin.set_yticks([])
                twin.set_yticklabels([])
                twin.remove()
            except:
                continues
        try:
            self.ax_image_PB3.remove()
            self.ax_image_TB.remove()
        except: pass
        try:
            for ax in self.lines:
                ax.remove()
        except: pass
        #import pdb; pdb.set_trace()
        self.sc.draw()
        self.states.plotted = False

    def progressRamp( self, target ):
        curr = self.progress.value()
        for i in range(target-curr):
            self.progress.setValue( curr + i + 1 )
            time.sleep(0.02)

    def build_plots( self, base_path = None ):
        '''
        Takes selected keys and appends them to timeseries data.
        Loads pickled data from <base_path>/<metric_name>_full.dat
        Pares data to selected sample rate.
        Plots and annotates
        '''
        if not self.key_select.texts:
            self.acknowledge_window( 'No data columns selected. Pick from dropdown menu.' )
            return
        
        ### Open directory if no directory is already loaded. ###
        if not Utils.Vals.dir_path:
            if not self.open_dir_dialog( ):
                return
        base_path  = Utils.Vals.dir_path

        self.progress.setVisible( True )
        self.l.setVisible( True)
        self.progress.setValue( 0 )
        df = None
        ### Grab indices first ###
        if not os.path.exists( os.path.join( base_path, "Timeseries.dat" ) ) :
            self.acknowledge_window( 'Timeseries.dat dataset cannot be found in provided directory. You may need to run "Process Data".' )
            Utils.Vals.dir_path = None
            self.filename_edit.setText("")
            return



        self.progressRamp( 5 ) 
        
        
        fname = os.path.join( base_path, "Timeseries.dat" )
        df = Parser.read_pickle( fname )
        df = Parser.clean_whitespace( df )

        self.progressRamp( 10 )

        # Search to all timestamps between QDateEdit / QCalendar selections, and ensure <= and >= cases are caught
        tmask = ((df[ 'Timeseries' ] >= self.states.startDate) & (df[ "Timeseries"] <= self.states.endDate))
        
        if self.states.pareVal:            
            paremask = ( df.index % self.states.pareVal == 0 )
            tmask = tmask & paremask
            #df = df.iloc[ ( df.index % self.states.pareVal == 0 ) ]
        ### Check that applied mask isn't empty ###   
        if not tmask.any():
            self.acknowledge_window( 'There is no available data matching your search dates. \n \
Please adjust dates or select "Expand Date Range"\n \
to find dataset start and end timestamps.' )
            self.progress.setValue( 100 )
            time.sleep(0.05)
            self.progress.setVisible( False )
            self.l.setVisible( False )
            return
        self.progressRamp( 40 )

        origDF = pd.DataFrame({})
        once = False
        ### Get timeseries columns and other requested data###
        print("Beginning plot processing.")
        for column in [ "Date","Time_ms" ] + self.key_select.texts:
            ### If not Date_full.dat or Time_ms_full.dat exist in the base_path, abort
            if not os.path.exists( os.path.join( base_path, column + "_full.dat" ) ):
                self.acknowledge_window( f"{column} dataset cannot be found in provided directory, aborting." )
                Utils.Vals.dir_path = None
                self.filename_edit.setText("")
                return
            fname = os.path.join( base_path, column + "_full.dat" )
            df = Parser.read_pickle( fname )
            df = Parser.clean_whitespace( df )
            if once:
                origDF = pd.concat(
                [ origDF.reset_index( drop=True ),
                 df.reset_index( drop=True ) ], axis=1 )
            else:
                once = True
                origDF = df
        self.progressRamp( 50 )
        fullDF = origDF.loc[np.where(tmask)]
        fullDF.reset_index(drop=True)
        print( "Rendering Plot" )
        self.clear_plots( )
        #self.sc.figure.subplots_adjust(left=0.075, bottom=0.15, right=0.925, top=0.92) # wspace=0, hspace=0.25)
        self.sc.axes.set_title(
            "SWPB-001: " + ", ".join(
                m for m in self.key_select.texts), size = 7.5, fontweight='bold')
        
        self.labels = []
        self.lines = []
        self.twins = []
        format_spec = ('r','b','m','k','g')
        
        for i,metric in enumerate(self.key_select.texts):
            mean = fullDF[metric ].mean()
            std = fullDF[metric].std()
            print( f"{metric} stats: mean={mean}, std={std}" )
            self.labels.extend([metric])
            clr = format_spec[ i % 5 ]
            if not i:
                self.lines.extend( self.sc.axes.plot(
                     fullDF[ metric ].values[:], format_spec[ i % 5 ], linewidth=0.65 ) )
                self.sc.axes.set_ylabel( metric, size = 4.5, color=clr )
                ### Stats ###
                if self.states.trendline:
                    self.sc.axes.annotate( "mean:"+str(mean), (0,mean), fontsize=4, ha='left' )
                    self.sc.axes.axhline( mean, color = clr, linewidth = 0.4, linestyle = ":", label="__nolegend__" )
                    self.sc.axes.axhline( mean+std, color = clr, linewidth=0.4, linestyle = "-.", label = "__nolegend__" )
                    self.sc.axes.axhline( mean+std, color = clr, linewidth=0.4, linestyle = "-.", label ="__nolegend__" )
            else:
                self.twins.append( self.sc.axes.twinx( ) )
                self.twins[-1].set_ylabel( metric, size = 4.5, color=clr, labelpad = 0, loc="top" )
                #self.twins[-1].yaxis.set_label_coords(-0.1,1.02)
                self.twins[-1].tick_params( axis='y', colors=clr, labelsize=4, pad=min(0,(i-1)*10) )
                self.twins[-1].spines['right'].set_position(('outward', (i-1)*15))
                self.twins[-1].spines['right'].set_color( clr )
                self.lines.extend( self.twins[-1].plot(
                    fullDF[ metric ].values[:], clr, linewidth=0.65 ) )
                ### Stats ###
                if self.states.trendline:
                    self.twins[-1].annotate( "mean:"+str(mean), (0,mean), fontsize=4, ha='left')
                    self.twins[-1].axhline( mean, color = clr, linewidth=0.4, linestyle = ":", label="__nolegend__")
                    self.twins[-1].axhline( mean + std, color = clr, linewidth = 0.4, linestyle = "-.", label = "__nolegend__")
                    self.twins[-1].axhline( mean + std, color = clr, linewidth = 0.4, linestyle = "-.", label ="__nolegend__")
            self.progressRamp( 50 + i*int(40 / len(self.key_select.texts)) )
                               
        ### Add margin to right side of plot depending on how many things are plotted 
        self.sc.figure.subplots_adjust(left=0.1, bottom=0.18, right=0.95-0.025*i, top=0.88)
        self.sc.axes.legend( self.lines, self.labels, ncols = max(1,len(self.lines)-1), fontsize = [4,4,3,3,2,2,1,1][i-1], loc='lower center',
                             bbox_to_anchor=(0.0, 1.0), facecolor="lightgrey",
                             fancybox=True, shadow=True, edgecolor='k', labelspacing = 0.1 )
        #self.sc.axes.set_xlabel("Date", size=8)
        ticks = np.linspace( 0, fullDF.shape[0], num = Utils.Vals.numticks + 1 )
        skipval = np.floor( fullDF['Date'].shape[0] / Utils.Vals.numticks)
        self.sc.axes.set_xticks( ticks )
        self.sc.axes.xaxis.labelpad = 5
        self.sc.axes.tick_params(axis='y', labelsize=4)
        self.sc.axes.set_xlabel( "Timestamp", size = 6 )
        try:
            self.sc.axes.set_xticklabels(
            [tick for i, tick in enumerate(fullDF['Date']) if (i % skipval == 0)],
            rotation=25,size=4, ha="right", va="top" )
        except ValueError as e:
            ticks = np.linspace( 0, fullDF.shape[0], num = Utils.Vals.numticks )
            self.sc.axes.set_xticks( ticks )
            self.sc.axes.set_xticklabels(
            [tick for i, tick in enumerate(fullDF['Date']) if (i % skipval == 0)],
            rotation=25, size=4, ha="right", va="top" )
        #self.sc.axes.set_ylabel("Watts", size=8)
        self.sc.axes.xaxis.grid(self.states.gridlines, which='major')
        self.sc.axes.yaxis.grid(self.states.gridlines, which='major')
        self.states.plotted = True
        self.sc.draw()
        self.progressRamp( 100 )
        time.sleep(0.15)
        self.progress.setVisible( False )
        self.l.setVisible( False )

    def save_cfg( self ):
        '''
        Saves current figure to png at specified output location
        '''
        if not Utils.Vals.dir_path:
            if not self.open_dir_dialog( ):
                return
        base_path  = Utils.Vals.dir_path
        plotdir = os.path.join( base_path, "plots" )
        if not os.path.exists( plotdir ):
            os.makedirs( plotdir )
        title = self.sc.axes.get_title()
        pname = os.path.join( plotdir, f"{title}.png" )
        plt.savefig( pname , dpi=500 )

    def build_report( self, base_path = None ):
        '''
        Takes all keys and appends them to timeseries data.
        Loads pickled data from <base_path>/<metric_name>_full.dat
        Pares data to selected sample rate.
        Creates all possible plots and saves as png files.
        '''
        ### Open directory if no directory is already loaded. ###
        if not Utils.Vals.dir_path:
            if not self.open_dir_dialog( ):
                return
        base_path  = Utils.Vals.dir_path
        

        print("Beginning plot processing.")
        plotdir = os.path.join( base_path, "plots" )
        if not os.path.exists( plotdir ):
            os.makedirs( plotdir )

        ### Grab indices first ###
        if self.states.selectedDates:
            print(df.shape," before date reduction.")
            df = df[ df[ "Date"] > self.states.startDate & df[ "Date"] < self.states.endDate ]
            print(df.shape," before date reduction.")
        if self.states.pareVal: 
            df = df.iloc[ ( df.index % self.states.pareVal == 0 ) ]
            
        fullDF = pd.DataFrame({})
        once = False
        ### Get timeseries columns and other requested data###
        for column in [ "Date", "Time_ms" ]: 
            ### If not Date_full.dat or Time_ms_full.dat exist in the base_path, abort
            if not os.path.exists( os.path.join( base_path, column + "_full.dat" )):
                self.acknowledge_window( f"{column} dataset cannot be found in provided directory, aborting." )
                Utils.Vals.dir_path = None
                self.filename_edit.setText("")
                return
            fname = os.path.join( base_path, column + "_full.dat" )
            df = Parser.read_pickle( fname )
            ### Pare dataset modulo is

            df = Parser.clean_whitespace( df )
            if once:
                fullDF = pd.concat(
                [ fullDF.reset_index( drop=True ),
                 df.reset_index( drop=True ) ], axis=1 )
            else:
                once = True
                fullDF = df

        newDF = pd.DataFrame({})
        ticks = np.linspace(0,fullDF['Date'].shape[0],num = Utils.Vals.numticks+1)
        skipval = np.floor(fullDF['Date'].shape[0] / Utils.Vals.numticks)
        tick_labels  = [tick for i, tick in enumerate(fullDF['Date']) if (i % skipval == 0)]
        
        ## keylib[1:] because we need to ignore the 'Clear all selections' value
        keylen = len(Utils.Vals.keylib) -1
        for i,column in enumerate( Utils.Vals.keylib[1:] ):
            ### If not Date_full.dat or Time_ms_full.dat exist in the base_path, abort
            if not os.path.exists( os.path.join( base_path, column + "_full.dat" )):
                print(f"{column} dataset cannot be found in provided directory, skipping.")
                continue
            fname = os.path.join( base_path, column + "_full.dat" )
            df = Parser.read_pickle( fname )
            ### Pare dataset modulo is 
            df = Parser.clean_whitespace( df ).reset_index( drop = True )

            fig = plt.figure( figsize=(11,8.5) )
            fig.subplots_adjust( left=0.075, bottom=0.15, right=0.925, top=0.92 )
            ax = fig.add_subplot( 111 )
            ax.plot( df[ column ], linewidth=0.65 )
            if self.states.trendline:
                mean = df[ metric ].mean( )
                std = df[ metric ].std( )
                ax.annotate( "mean:"+str(mean), (0,mean), fontsize=4, ha='left')
                ax.axhline( mean, color = clr, linewidth = 0.4, linestyle = ":", label="__nolegend__")
                ax.axhline( mean+std, color = clr, linewidth=0.4, linestyle = "-.", label = "__nolegend__")
                ax.axhline( mean+std, color = clr, linewidth=0.4, linestyle = "-.", label ="__nolegend__")
            ax.set_title( "SWPB-001: " + f"{column}", size = 7, fontweight = 'bold' )
            ax.set_xticks(ticks)
            ax.xaxis.labelpad = 5
            ax.set_xlabel("Timestamp",size = 9)
            plt.yticks(fontsize=5)
            ax.set_xticklabels(tick_labels,rotation=30,size=4, ha="right")
            fig.savefig( os.path.join( plotdir, f"SWPB-001_{column}_full" ), dpi=500)
            self.update_progress( [int( i + 1 / keylen * 100 ), 0] )
            plt.close(fig)
            print(f"{column} plot saved.")
        return




## MVP
if __name__ == "__main__":
    # Initialize application
    qapp = QApplication(sys.argv)
    sys._excepthook = sys.excepthook 
    sys.excepthook = exception_hook 
    w = MainWindow(qapp)
    sys.exit(qapp.exec_())



