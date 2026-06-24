# Auditoria v0.5.0

Data: 2026-06-24

## Escopo

- Revisao de pendencias do roadmap seguro.
- Validacao de CLI, testes e artefatos runtime.
- Checagem local de padroes de segredo.
- Confirmacao de que execucao real segue bloqueada.

## Resultado

Status: aprovado.

## Entregas Fechadas

- `wallet`: valida endereco publico EVM/Solana e consolida exposicao simulada.
- `watch`: revisa posicoes simuladas abertas e gera alertas locais.
- `audit`: verifica secrets, artefatos runtime ignorados e invariantes de seguranca.
- `python3 -m unittest` agora descobre a suite padrao.

## Invariantes De Seguranca

- Seed phrase e chave privada nao sao solicitadas.
- Secrets devem ficar somente em env/secret manager.
- `execute` nao assina transacao.
- `execute` nao faz broadcast.
- Recibos continuam com `broadcasted=false` e `tx_hash=null`.
- Estado local fica em `workspace/state/*.json`, ignorado pelo Git.

## Validacao Executada

- `python3 -m py_compile workspace/*.py workspace/adapters/*.py workspace/engines/*.py workspace/models/*.py workspace/state/*.py`
- `AUTO_POOLS_USE_SAMPLE=1 python3 -m unittest -v`
- `AUTO_POOLS_USE_SAMPLE=1 python3 workspace/auto_pools.py --mode wallet --wallet-address 0x0000000000000000000000000000000000000000 --json`
- `AUTO_POOLS_USE_SAMPLE=1 python3 workspace/auto_pools.py --mode execute --action open --chain solana --profile moderado --capital 1000 --allocation-pct 0.05 --confirm --json`
- `AUTO_POOLS_USE_SAMPLE=1 python3 workspace/auto_pools.py --mode watch --json`
- `AUTO_POOLS_USE_SAMPLE=1 python3 workspace/auto_pools.py --mode audit --json`

## Pendencias Intencionais

- Execucao on-chain real fica fora da v0.5.0.
- Alertas externos/agendados devem pedir confirmacao antes de enviar mensagens.
- Signer seguro, simulacao on-chain e rollback ficam para release futura explicita.
