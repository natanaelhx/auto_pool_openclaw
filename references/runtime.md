# Runtime

## Compatibilidade

- Python 3 disponivel.
- Nao assumir `pip3`, `ensurepip` ou `python3-venv`.
- Nao usar `sudo`, `apt`, Docker ou raw sockets.
- Usar HTTP/HTTPS com timeout.
- Evitar dependencias externas no MVP.

## Credenciais

Credenciais devem vir de variaveis de ambiente ou secret manager:

- `COINGECKO_API_KEY`
- `DEFILLAMA_API_KEY`
- `DUNE_API_KEY`
- `AUTO_POOLS_WALLET_ADDRESS`
- `AUTO_POOLS_DEFAULT_PROFILE`
- `AUTO_POOLS_USE_SAMPLE`
- `AUTO_POOLS_EXECUTION_ENABLE`
- `AUTO_POOLS_SIGNER_REF`

Nunca colocar secrets no Git.
