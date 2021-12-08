import pandas as pd
import glob
import csv 
import tailer


def read_streaming(path):
    blocks_streaming = pd.read_csv(path, index_col=0).sort_index(ascending=True)
    return blocks_streaming 

def read_history_tail(updating_path, n_rows=1000):
    
    cols = ['block_timestamp', 'base_fee_per_gas', 'gas_used']
    
    with open(updating_path, 'r') as f:
        blocks_tail_ls = tailer.tail(f, 1000)
    
    blocks_tail = pd.DataFrame([
        i.split(",") for i in blocks_tail_ls
    ], columns=cols).set_index('block_timestamp')
    
    return blocks_tail

def reformat_streaming(streaming_df, history_tail_df):

    new_data_idx = [
        i for i in streaming_df.index if i + " UTC" not in history_tail_df.index
    ]
    new_data = streaming_df.loc[new_data_idx]
    new_rows = new_data.reset_index().values.tolist()
    new_rows = [[i[0] + ' UTC'] + i[1:]  for i in new_rows]
    return new_rows

def update_history(updating_path, rows):
    with open(updating_path, 'a') as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)
        
if __name__ == "__main__":
    
    import os
    import time
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    # file paths
    blocks_updating_path = os.path.join(dir_path, 'historical_data/blocks_updating.csv')
    blocks_streaming_path = os.path.join(dir_path, 'blocks.csv')
    
    # number of rows of history to check for duplicates
    tail_rows = 1000
    
    try:
        streaming = read_streaming(blocks_streaming_path)
    except Exception as e:
        time.sleep(5)
        streaming = read_streaming(blocks_streaming_path)
          
    history_tail = read_history_tail(blocks_updating_path, n_rows=tail_rows)
    rows_to_add = reformat_streaming(streaming, history_tail)
    
    update_history(blocks_updating_path, rows_to_add)
    
    print("Done.")

    

