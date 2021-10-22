import os
import subprocess
import time
import pandas as pd
import glob


from columns import COLUMNS
from utils import latest, timestamp_to_datetime


URI = "https://mainnet.infura.io/v3/7aef3f0cd1f64408b163814b22cc643c"
DATA_DIR = "data"


def get_block_range_for_date(dt, uri=URI):

    command_str = f"ethereumetl get_block_range_for_date --provider-uri {uri} --date {dt}"
    p = subprocess.Popen(["exec " + command_str], stdout=subprocess.PIPE, shell=True)
    try:
        res = p.stdout.read().decode().replace("\n", "") # can only run this once
    except ValueError:
        print("Check ethereum-etl installation.")
    p.kill()

    start_block, end_block = tuple(res.split(","))

    return start_block, end_block


def get_block_range(start_date, end_date, uri=URI):

    start_block = get_block_range_for_date(start_date, uri=uri)[0]
    end_block = get_block_range_for_date(end_date, uri=uri)[1]

    return start_block, end_block


def output_file(file_name, start, end, data_dir=DATA_DIR, ending="csv"):
    res = f"{file_name}_{str(start)}_{str(end)}.{ending}"
    res = os.path.join(data_dir, res)
    return res


def run_and_kill(cmd, wait_time=5):

    p = subprocess.Popen(["exec " + cmd], stdout=subprocess.PIPE, shell=True)
    running = True
    while running:
        running = p.poll() is None
        time.sleep(wait_time)
    p.kill()


def export_blocks_and_transactions(
    start_block,
    end_block,
    blocks_output=None,
    transactions_output=None,
    uri=URI,
    data_dir=DATA_DIR
):

    if blocks_output is None:
        blocks_output = output_file(
            "blocks", start_block, end_block, data_dir=data_dir
        )

    if transactions_output is None:
        transactions_output = output_file(
            "transactions", start_block, end_block, data_dir=data_dir
        )

    command_str = f"ethereumetl export_blocks_and_transactions --start-block {start_block} " \
        f"--end-block {end_block} --blocks-output {blocks_output} --transactions-output " \
        f"{transactions_output} --provider-uri {uri}"

    print("Exporting blocks & transactions...")
    run_and_kill(command_str)


def export_receipts_and_logs(
    start_block,
    end_block,
    transactions_path=None,
    logs_output=None,
    receipts_output=None,
    uri=URI,
    data_dir=DATA_DIR
):

    if transactions_path is None:
        transactions_path = output_file(
            "transactions", start_block, end_block, data_dir=data_dir
        )

    if logs_output is None:
        logs_output = output_file(
            "logs", start_block, end_block, data_dir=data_dir
        )

    if receipts_output is None:
        receipts_output = output_file(
            "receipts", start_block, end_block, data_dir=data_dir
        )

    transaction_hashes_output = output_file(
        "transaction_hashes", start_block, end_block, data_dir=data_dir, ending="txt"
    )

    hashes_cmd = f"ethereumetl extract_csv_column --input {transactions_path} " \
                 f"--column hash --output {transaction_hashes_output}"

    print("Exporting transaction hashes...")
    run_and_kill(hashes_cmd)

    rl_cmd = f"ethereumetl export_receipts_and_logs --transaction-hashes " \
             f"{transaction_hashes_output} --provider-uri {uri} " \
             f"--receipts-output {receipts_output} --logs-output {logs_output}"

    print("Exporting receipts & logs...")
    run_and_kill(rl_cmd)


def extract_token_transfers(
    start_block,
    end_block,
    logs_path=None,
    token_transfers_output=None,
    data_dir=DATA_DIR
):
    if logs_path is None:
        logs_path = output_file(
            "logs", start_block, end_block, data_dir=data_dir
        )

    if token_transfers_output is None:
        token_transfers_output = output_file(
            "token_transfers", start_block, end_block, data_dir=data_dir
        )

    print("Extracting token transfers...")
    cmd = f"ethereumetl extract_token_transfers --logs {logs_path} " \
          f"--output {token_transfers_output}"

    run_and_kill(cmd)


def export_contracts(
    start_block,
    end_block,
    receipts_path=None,
    contract_addresses_output=None,
    contracts_output=None,
    uri=URI,
    data_dir=DATA_DIR
):
    if receipts_path is None:
        receipts_path = output_file(
            "receipts", start_block, end_block, data_dir=data_dir
        )

    if contract_addresses_output is None:
        contract_addresses_output = output_file(
            "contract_addresses", start_block, end_block, data_dir=data_dir, ending="txt"
        )

    if contracts_output is None:
        contracts_output = output_file(
            "contracts", start_block, end_block, data_dir=data_dir
        )

    addresses_cmd = f"ethereumetl extract_csv_column --input {receipts_path} " \
          f"--column contract_address --output {contract_addresses_output}"

    print("Extracting contract addresses...")
    run_and_kill(addresses_cmd)

    contracts_cmd = f"ethereumetl export_contracts --contract-addresses " \
                    f"{contract_addresses_output} --provider-uri {uri} " \
                    f"--output {contracts_output}"

    print("Exporting contracts...")
    run_and_kill(contracts_cmd)


def export_tokens(
    start_block,
    end_block,
    contracts_path=None,
    token_addresses_output=None,
    tokens_output=None,
    uri=URI,
    data_dir=DATA_DIR
):

    if contracts_path is None:
        contracts_path = output_file(
            "contracts", start_block, end_block, data_dir=data_dir
        )

    if token_addresses_output is None:
        token_addresses_output = output_file(
            "token_addresses", start_block, end_block, data_dir=data_dir, ending="txt"
        )

    if tokens_output is None:
        tokens_output = output_file(
            "tokens", start_block, end_block, data_dir=data_dir
        )

    filter = "\"" + "item['is_erc20'] or item['is_erc721']" + "\""
    token_cmd = f"ethereumetl filter_items -i {contracts_path} -p {filter} | " \
          f"ethereumetl extract_field -f address -o {token_addresses_output}"

    print("Extracting token addresses...")
    run_and_kill(token_cmd)

    export_cmd = f"ethereumetl export_tokens --token-addresses {token_addresses_output} " \
                 f"--provider-uri {uri} --output {tokens_output}"

    print("Exporting tokens...")
    run_and_kill(export_cmd)


class EthereumData():

    def __init__(
        self,
        start_date=None,
        end_date=None,
        start_block=None,
        end_block=None,
        save_path=r'data/test'
    ):

        if (start_block or start_block == 0) and end_block:

            self.start_block = start_block
            self.end_block = end_block
            self.start_date = None
            self.end_date = None

        elif start_date and end_date:

            self.start_date = start_date
            self.end_date = end_date
            self.start_block = None
            self.end_block = None

        else:
            raise ValueError('No start & end dates or blocks')

        self.save_path = save_path

    @property
    def file_paths(self):
        files = [
            "blocks",
            "transactions",
            "contracts",
            "logs",
            "receipts",
            "token_transfers",
            "tokens"
        ]
        ending = f"_{self.start_block}_{self.end_block}.csv"
        return {k : os.path.join(self.save_path, k + ending) for k in files}

    def load_from_files(self, skip=[]):
        for k, v in self.file_paths.items():
            if k not in skip:
                print(f"Loading {k}...")
                df = pd.read_csv(v)
                setattr(self, k, df)

    def update(self, skip=[]):

        exists = os.path.exists(self.save_path)

        if not exists:
            os.makedirs(self.save_path)
        if not self.end_block:
            self.start_block, self.end_block = get_block_range(
                self.start_date, self.end_date
            )

        st = self.start_block
        ed = self.end_block

        export_blocks_and_transactions(st, ed, data_dir=self.save_path)
        time.sleep(5)
        export_receipts_and_logs(st, ed, data_dir=self.save_path)
        time.sleep(5)
        extract_token_transfers(st, ed, data_dir=self.save_path)
        time.sleep(5)
        export_contracts(st, ed, data_dir=self.save_path)
        time.sleep(5)
        export_tokens(st, ed, data_dir=self.save_path)
        time.sleep(5)

        self.load_from_files(skip=skip)

    def load(self, skip=[]):

        exists = os.path.exists(self.save_path)

        if not exists:
            os.makedirs(self.save_path)
            self.update()
        elif not self.end_block:
            try:
                blocks_file = glob.glob(f'{self.save_path}/blocks_*.csv')[0]
                blocks = pd.read_csv(blocks_file)
                self.start_block = blocks['number'].min()
                self.end_block = blocks['number'].max()
            except FileNotFoundError:
                pass

        self.load_from_files(skip=skip)

    def clean(self):

        data = {
            'blocks': self.blocks[COLUMNS['blocks']],
            'transactions': self.transactions[COLUMNS['transactions']],
            'contracts': self.contracts[COLUMNS['contracts']],
            'logs': self.logs[COLUMNS['logs']],
            'receipts': self.receipts[COLUMNS['receipts']],
            'token_transfers': self.token_transfers[COLUMNS['token_transfers']],
            'tokens': self.tokens[COLUMNS['tokens']]
        }

        # readible date column for blocks
        data['blocks'] = timestamp_to_datetime(data['blocks'])

        clean_transactions = data['transactions']
        # merge with receipts
        clean_transactions = pd.merge(
            left=clean_transactions,
            right=data['receipts'],
            left_on=[
                'hash',
                'block_number'
            ],
            right_on=[
                'transaction_hash',
                'block_number'
            ]
        )

        # merge with transfers
        clean_transactions = pd.merge(
            left=clean_transactions,
            right=data['token_transfers'],
            how='left',
            left_on='hash',
            right_on='transaction_hash',
            suffixes=("", "_transfer")
        )

        # merge with contracts
        clean_transactions = pd.merge(
            left=clean_transactions,
            right=data["contracts"],
            how='left',
            left_on='to_address',
            right_on='address',
            suffixes=('', '_to_contract')
        )
        clean_transactions = pd.merge(
            left=clean_transactions,
            right=data["contracts"],
            how='left',
            left_on='from_address',
            right_on='address',
            suffixes=('', '_from_contract')
        )

        # merge with blocks
        clean_transactions = pd.merge(
            left=clean_transactions,
            right=data['blocks'],
            how='left',
            left_on='block_number',
            right_on='number',
            suffixes=('', '_block')
        )

        return clean_transactions

    def point_in_time_blocks(self, lag=60):

        df = timestamp_to_datetime(self.blocks).sort_values(by='number')
        df['lag_cutoff'] = df['datetime'] - pd.offsets.DateOffset(seconds=lag)
        df['latest_avail_block'] = latest(df, 'number', 'datetime', 'lag_cutoff')
        df = df[[
            'number', 'datetime', 'lag_cutoff', 'latest_avail_block'
        ]].set_index('number').sort_index()

        return df


if __name__ == "__main__":

    dt = "2021-09-01"
    # test = EthereumData(
    #     start_block=11578165, end_block=11584640, save_path=r'data/2021-01-03'
    # )
    test = EthereumData(
        start_date=dt, end_date=dt, save_path=f'data/{dt}'
    )
    test.load()
    test.clean()
    #test.update()

    # st, ed = get_block_range("2021-01-03", "2021-01-03")
    # # st = 100000
    # # ed = 100200
    #
    # # export_blocks_and_transactions(st, ed)
    # # export_receipts_and_logs(st, ed)
    # # extract_token_transfers(st, ed)
    # # export_contracts(st, ed)
    # export_tokens(st, ed)
