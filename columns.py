COLUMNS = {
    "blocks": [
        'number',
        'miner',
        'difficulty',
        'total_difficulty',
        'size',
        'gas_limit',
        'gas_used',
        'timestamp',
        'transaction_count',
        'base_fee_per_gas'
    ],
    "transactions": [
        'hash',
        'block_number',
        'transaction_index',
        'from_address',
        'to_address',
        'value',
        'gas',
        'gas_price',
        'max_fee_per_gas',
        'max_priority_fee_per_gas',
        'transaction_type'
    ],
    "contracts": [
        'address',
        'function_sighashes',
        'is_erc20',
        'is_erc721',
        'block_number'
    ],
    "logs": [
        'log_index',
        'transaction_hash',
        'block_number',
        'address'
    ],
    "receipts": [
        'transaction_hash',
        'block_number',
        'cumulative_gas_used',
        'gas_used',
        'contract_address',
        'status',
        'effective_gas_price'
    ],
    "token_transfers": [
        'token_address',
        'from_address',
        'to_address',
        'value',
        'transaction_hash',
        'log_index',
        'block_number'
    ],
    "tokens": [
        'address',
        'symbol',
        'name',
        'decimals',
        'total_supply',
        'block_number'
    ]
}