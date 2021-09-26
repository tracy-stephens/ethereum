from ethereum import EthereumData

if __name__ == "__main__":
    sample_dt = "2021-09-01"

    sample = EthereumData(
        start_date=sample_dt, end_date=sample_dt, save_path=f"data/{sample_dt}"
    )

    sample.update()