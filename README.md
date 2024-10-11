# BuoyDataPanel
Data Visualization and processing tool for collecting data from OPT Buoys in current tab delimited format.

#Data access
-To access buoy data, you must either access a drive with copied buoy data, or access the buoy HMI computer itself.
-BuoyPanel is extensible to live updates if VPN or dropbox data backbone is reestablished.

#Raw Buoy Data Format
-On the Buoy, recorded data carries a specific naming scheme:
-->Data:
	|
	----> Folder_111
			|
			----> SWPB-XX_NJHMI_24111_00020.txt  (fmt: <AssetName>_<HMItag>_<Date>_<Timestamp>.txt  
			----> SWPB-XX_NJHMI_24111_00769.txt
			----> SWPB-XX_NJHMI_24111_01518.txt
			----> ...
	
	----> Folder_112
			|
			----> SWPB-XX_NJHMI_24112_00495.txt
			----> SWPB-XX_NJHMI_24112_01244.txt
			----> SWPB-XX_NJHMI_24112_01993.txt
			----> ...
	----> ...

	
#Compression Operation
-In order to compress many text files, each folder is first collapsed into a .dat file with pickle compression.
-The compression ratio of combinedDF.dat files is approximately 1:10 combined file size.

-After initial compression the compressed .dat files in every subfolder (File_###) are merged by metric in the parent directory.
-A metric is any original column header/label as received from HMI text files with whitespace removed.  Ex: SolarBusChg, Batt2SoC ...
-To build the metric files across the full timeseries, the function opens each .dat file and filters specific metric names 
-The .dat files are combined in order by date and time
-The .dat files are saved in compressed binary format using Python blosc and pickle libraries

#Data Load Operation
-To load buoy data, an entire timeseries dataset <metric>_full.dat is opened.
-Data is decimated by default, but can be further reduced or presented in raw form depending upon UI data reduction selection