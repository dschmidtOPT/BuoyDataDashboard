from datetime import datetime
import dateutil.parser
import datetime
import pandas as pd
import pickle
import blosc
import os


### Column / key naming operations ###

def clean_whitespace( df ):
    rename_vect = {key: key.replace(" ","") for key in df.keys().to_list()}
    df.rename(columns = rename_vect, inplace=True)
    return df

def grab_keys( df ):
    return [ key for key in df.keys() ]

def key_peek(data_path, data_dirs):
    if isinstance(data_dirs,list):
        try:
            files = os.listdir( os.path.join( data_path, data_dirs[0] ))
        except:
            print(f"Inside grab_keys(): {data_dirs}")
            print(data_dirs)
            files = os.listdir( os.path.join( data_path, data_dirs ))
        
    else:
        files = os.listdir( os.path.join( data_path, data_dirs ))
    while files[0].find(".txt") == -1:
        files.pop(0)
    df = pd.read_csv(os.path.join(data_path,data_dirs[0],files[0]), sep ="\t") 
    return grab_keys( df )

### Dataset append operations ###

def soft_merge( big_df, new_df, index=True, axis=0):
    try:
        if index:
            big_df = pd.concat([big_df, new_df], axis=axis, ignore_index=False)
        else:
            new_df.reset_index(drop=True, inplace=True)
            big_df = pd.concat([big_df, new_df], axis = axis)
    except Exception as e:
        print(e)
        pass
    return big_df

### Compression and decompression operations ###

def pickle_df( fpath, data ):
    pickled_data = pickle.dumps(data)  # returns data as a bytes object
    compressed_pickle = blosc.compress(pickled_data)
    with open(fpath, "wb") as f:
        f.write(compressed_pickle)
        
def read_pickle( fpath, keyfilter = None):
    with open( fpath, "rb") as f:
        compressed_pickle = f.read()
        depressed_pickle = blosc.decompress(compressed_pickle)
        data = pickle.loads(depressed_pickle)  # turn bytes object back into data
        if keyfilter:
            output = pd.DataFrame( data )[ keyfilter ]
        else:
            output = pd.DataFrame( data ) 
    return output

### Rowwise data manipulation operations

def datestamper( date, time ):
        ### Need to omit milliseconds at first because datetime sucks ###
        return datetime.datetime.fromisoformat( date[-4:] + "-" + date[0:2] + "-" + date[3:5] +"T"+ time)

