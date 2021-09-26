import os
import subprocess
import time

URI = "https://mainnet.infura.io/v3/7aef3f0cd1f64408b163814b22cc643c"
DATA_DIR = "data"


def get_block_range_for_date(dt, uri=URI):

    command_str = f"ethereumetl get_block_range_for_date --provider-uri {uri} --date {dt}"
    p = subprocess.Popen(["exec " + command_str], stdout=subprocess.PIPE, shell=True)
    res = p.stdout.read().decode().replace("\n", "")
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

    def __init__(self, start_date, end_date, data_dir=DATA_DIR):

        self.start_date = start_date
        self.end_date = end_date
        self.data_dir = DATA_DIR

    def update(self):

        self.start_block, self.end_block = get_block_range(
            self.start_block, self.end_block
        )

        st = self.start_block
        ed = self.end_block

        export_blocks_and_transactions(st, ed)
        export_receipts_and_logs(st, ed)
        extract_token_transfers(st, ed)
        export_contracts(st, ed)
        export_tokens(st, ed)



if __name__ == "__main__":

    st, ed = get_block_range("2021-01-03", "2021-01-03")
    # st = 100000
    # ed = 100200

    export_blocks_and_transactions(st, ed)
    export_receipts_and_logs(st, ed)
    extract_token_transfers(st, ed)
    export_contracts(st, ed)
    export_tokens(st, ed)

    # os.system(test)

    #res = subprocess.run(["echo " + test], stdout=subprocess.PIPE, shell=True)
    #print(res.stdout)