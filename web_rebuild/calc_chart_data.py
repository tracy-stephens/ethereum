import pandas as pd
from dashboard import (
    surge_index,
    get_bspg_by_minute,
    get_bspg_over_hour
)

def get_historical_data(path, tz):
    
    hist_df = pd.read_csv(path, index_col=0)
    hist_df.index = [pd.to_datetime(i) for i in hist_df.index]
    hist_df.index = [
        i.tz_localize("UTC").tz_convert(tz) if i.tzinfo is None 
        else i.tz_convert(tz) for i in hist_df.index
    ]
    return hist_df


if __name__ == "__main__":
    
    import os
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    tz = "US/Eastern"
    hist_path = os.path.join(dir_path, 'historical_data/blocks_updating.csv')
    
    minute_day_path = os.path.join(dir_path, 'chart_data/minute_day.csv')
    minute_hour_path = os.path.join(dir_path, 'chart_data/minute_hour.csv')

    hist = get_historical_data(hist_path, tz)
    hist_surge = surge_index(hist.sort_index())
    get_bspg_by_minute(hist_surge).to_csv(minute_day_path)
    get_bspg_over_hour(hist_surge).to_csv(minute_hour_path)
    
    
    
    




