# -*- coding: utf-8 -*-
"""
Purpose: Compress buoy data files and filter for plotting
Method: Blosc binary file pickling combines and reduces filesize 90%

@author: dschmidt
"""

import os
import blosc
import pickle
import numpy as np
import pandas as pd
from PyQt5.QtCore import *
#from tqdm import tqdm
from matplotlib import pyplot as plt

class Parser(QObject):

    progressSignal = pyqtSignal()

    def __init__(self, parent = None):
        super(Parser, self).__init__(parent)
        self.instance = None
        self.numdir = None
        
    
    
    def read_pickle( self, fpath, keyfilter = None):
        with open( fpath, "rb") as f:
            compressed_pickle = f.read()
            depressed_pickle = blosc.decompress(compressed_pickle)
            data = pickle.loads(depressed_pickle)  # turn bytes object back into data
            if keyfilter:
                output = pd.DataFrame( data )[ keyfilter ]
            else:
                output = pd.DataFrame( data ) 
        return output

    def pickle_df( self, fpath, data ):
        pickled_data = pickle.dumps(data)  # returns data as a bytes object
        compressed_pickle = blosc.compress(pickled_data)
        with open(fpath, "wb") as f:
            f.write(compressed_pickle)
        return 0


    def soft_merge( big_df, new_df, axis=0):
        try:
            big_df = pd.concat([big_df, new_df], axis=axis, ignore_index=False)
        except Exception as e:
            print(e)
            pass
        return big_df


    def grab_keys( df ):
        return [ key for key in df.keys() ]
        
    def soft_key_filter( df, kvalues ):
        allkeys = df.keys().to_list()
        for key in allkeys:
            for kvalue in kvalues:
                if kvalue in key:
                    allkeys.remove(key)
        return allkeys

    def clean_whitespace( df ):
        rename_vect = {key: key.replace(" ","") for key in df.keys().to_list()}
        df.rename(columns = rename_vect, inplace=True)
        return df

    def timestamper( row ):
        new = "/".join(row['Date'].split("/")[:-1]) + "|" + row['Time_ms']
        return new
                    
    #@pyqtSlot(tuple)
    def compress_dataset( self, data_path ):
        self.progressSignal.connect( self.progress_trigger )
        print("Compressing dataset and grabbing table keys...")
        data_dirs = [f for f in os.listdir( data_path ) if
                     ( f.find( "Folder_") != -1 ) ] #and os.path.isdir( f ) ]
        print( data_dirs )
        problematic = []
        keys = []
        self.numdirs = len(data_dirs)
        print(f'There are {self.numdirs} directories for processing')
        for i,subdir in enumerate(data_dirs):
            self.instance = i
            self.progressSignal.emit()
            df_merged = pd.DataFrame({})
            files = os.listdir( os.path.join( data_path, subdir ) )
            if "combinedDF.dat" in files:
                if keys:
                    continue  # Dont compress and overwrite a file if it already exists
            for dat_file in files:
                fname = os.path.join( data_path, subdir, dat_file )
                try: 
                    df = pd.read_csv(fname, sep ="\t")
                    if not keys: keys = grab_keys( df )
                except Exception as e:
                    print(f"Something went wrong with {fname}: {e}.")
                    problematic.append(fname)
                    continue
                df_merged = soft_merge( df_merged, df)
            #For each data directory, create one compressed binary pickle file
            pickle_df( os.path.join( data_path, subdir, "combinedDF.dat" ), df_merged )
        self.keys = keys

            
    def build_metric( data_path, keys ):
        data_dirs = [f for f in os.listdir( data_path ) if
                     ( f.find( "Folder_") != -1 ) ]
        timeseries = [ key for key in keys if ( "date" in key.lower() or 
                                               "time" in key.lower() ) ]
        for column_name in keys:
            df_merged = pd.DataFrame({})
            if column_name in timeseries:  # We dont want to filter on timestamp
                continue
            column_name = column_name.replace(" ","")
            newname  = os.path.join( data_path, f"{column_name}_full.dat" )
            if os.path.exists( newname ):
                continue
            print(f"Building {column_name} dataset...")
            problematic= []
            for subdir in data_dirs:
                fname = os.path.join( data_path, subdir, "combinedDF.dat" )    
                keyfilter = timeseries + [column_name]
                try:
                    df = read_pickle( fname, keyfilter )
                except:
                    problematic.append( fname )
                    df = pd.DataFrame({})
                df = read_pickle( fname, keyfilter )
                df_merged = soft_merge( df_merged, df)
            pickle_df( newname, df_merged )
        if problematic:
            print("There were issues processing the following files:")
            for problem in problematic:
                print(problem)
            
    def build_plots( data_path ):
        print("Beginning data load and plot process.")
        data_dirs = os.listdir(data_path)
        once = True
        for metric in data_dirs:
            fname = os.path.join( data_path, metric )
            df = read_pickle( fname )
            df = clean_whitespace( df )
            if once:
                parent = df
                once = False
            else:
                df = df.drop('Date', axis=1)
                df = df.drop('Time_ms', axis=1)
                parent = pd.concat([parent.reset_index(drop=True), 
                         df.reset_index(drop=True)], axis=1)

        # Calculate custom columns
        print("Calculating composite columns")
        parent['WindChg'] = parent['ChgBusV']*parent['WindCrnt']
        parent['SolarChg'] = parent['ChgBusV']*parent['SolarCrnt']
        parent['Timeseries'] = parent.apply(timestamper, axis=1) 
                
        print("Plotting")
        numticks = 20
        fig1, ax1 = plt.subplots()
        fig1.suptitle("SWPB-001",fontweight='bold')
        ticks = np.linspace(0,parent['Timeseries'].shape[0],num = numticks+1)
        skipval = np.floor(parent['Timeseries'].shape[0] / numticks)
        #ax1.plot( parent['Timeseries'], parent['WindChg'] )
        ax1.plot( parent['WindChg'] )
        ax1.set_title("Wind Charge")
        ax1.set_xlabel("Date", size=8)
        ax1.set_xticks(ticks)
        ax1.set_xticklabels([tick for i, tick in enumerate(parent['Timeseries']) if (i % skipval == 0)],rotation=90,size=6)
        ax1.set_ylabel("Watts", size=8)
        ax1.xaxis.grid(True, which='major')

    ##    fig2, ax2 = plt.subplots()
    ##    fig2.suptitle("SWPB-001",fontweight='bold')
    ##    ax2.plot( parent['Timeseries'], parent['SolarChg'] )
    ##    ax2.set_title("Solar Charge")
    ##    ax2.set_xlabel("Date",size=8, rotation=90)
    ##    ax2.set_ylabel("Watts", size=8)
    ##    ax2.xaxis.grid(True, which='major')
        plt.show()

    def progress_trigger( self ):
        emission = ( self.instance, self.numdir )
        
        
              
            
    
##if __name__ == "__main__":
##    data_path = "D:\SWPB Buoy Data"
##    #data_path = r"C:\Users\dschmidt.OCEANPOWERTECH\Desktop\SWPB-0001"
##    
##    keys = compress_dataset( data_path )
##    #build_metric( data_path, keys )
##    #build_plots( data_path )
##    
        
