from datetime import date, timedelta
from tqdm import tqdm

from ethereum import *


def collect_all(st, ed, save_path):

    export_blocks_and_transactions(st, ed, data_dir=save_path)
    export_receipts_and_logs(st, ed, data_dir=save_path)
    extract_token_transfers(st, ed, data_dir=save_path)
    export_contracts(st, ed, data_dir=save_path)
    export_tokens(st, ed, data_dir=save_path)


if __name__ == "__main__":

    start_dt = "2021-08-05"
    end_dt = "2021-11-02"
    data_dir = "/Volumes/SSD/data/aug5Nov2"
    uri = "https://mainnet.infura.io/v3/7d8037f6ecb94386b43e4ddb81c809a5"

    dt_rng = [
        i.strftime('%Y-%m-%d') for i in pd.date_range(
            pd.Timestamp(start_dt), pd.Timestamp(end_dt)
        )
    ]

    for dt in tqdm(dt_rng):

        print(dt)
        start_block, end_block = get_block_range_for_date(dt)

        save_path = os.path.join(data_dir, dt)
        exists = os.path.exists(save_path)
        if not exists:
            os.makedirs(save_path)

        collect_all(start_block, end_block, save_path)

