import os

pwd = r'D:\\SWPB Buoy Data\\'

files = [f for f in os.listdir(pwd) if f.find("Folder_") != -1]

for f in files:
    fullpath = os.path.join(pwd, f, "combinedDF.dat")
    if os.path.exists(fullpath):
        os.remove( fullpath )
        print(f"{fullpath} removed")
