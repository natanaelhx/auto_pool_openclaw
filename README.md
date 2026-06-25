# auto-pool-openclaw

> Skill standalone para analisar, ranquear, simular e planejar automacao segura de pools DeFi EVM/Solana com APR ajustado por risco.

## O que faz

- Busca pools candidatas em fontes publicas compativeis com ambientes conteinerizados.
- Filtra pools EVM e Solana por chain suportada, protocolo confiavel, token seguro, TVL, APR minimo/maximo, outlier e exposicao LP.
- Calcula score por APR, TVL, volume, liquidez, lateralizacao, drawdown e impermanent loss.
- Usa candles publicos para lateralizacao quando `--market-data` estiver ativo, com fallback heuristico.
- Calcula RSI14, ATR14, Bollinger width, ADX14 e regime do par quando ha OHLC historico suficiente.
- Usa CoinGecko como fallback opcional para ativos sem candles Binance suficientes.
- Gera `range_suggestion` com largura dinamica, limites percentuais, gatilho de rebalance e confianca.
- Gera ranking por perfil conservador, moderado ou agressivo.
- Aplica cenarios conservadores por tipo de par: stable/stable, ETH/stable, BTC/stable, SOL/stable, BTC/ETH, ETH/LST, BTC wrappers e SOL/LST.
- Estima tempo de lateralizacao/range.
- Simula alocacao em modo dry-run sem executar transacao real.
- Gera plano operacional de entrada, saida, collect fees e rebalance para EVM/Solana sem assinar transacao.
- Simula execucao guardada de `open`, `close`, `collect` e `rebalance`, com recibo auditavel e sem broadcast.
- Revisa carteira publica e exposicao simulada por ativo, chain e protocolo.
- Roda watcher local de posicoes simuladas abertas com alertas de guardrail/range/risco.
- Roda auditoria local de secrets e artefatos runtime antes de release.
- Gera plano quote-only de swap e bridge com slippage limitado por perfil, sem assinatura e sem broadcast.
- Audita signer local com private key EVM vinda somente de ENV/secret manager, sem imprimir ou salvar o segredo.
- Inclui wizard em PT-BR para configurar perfil, capital, limite por pool e dry-run inicial.
- Aplica guardrails de seguranca para bloquear cenarios ruins.
- Responde e documenta tudo em portugues do Brasil.

## Pre-requisitos

| Requisito | Como configurar |
|-----------|-----------------|
| Python 3 | Necessario no runtime/container |
| COINGECKO_API_KEY | Opcional, Dashboard -> Chaves e Segredos |
| DEFILLAMA_API_KEY | Opcional, Dashboard -> Chaves e Segredos |
| DUNE_API_KEY | Opcional, Dashboard -> Chaves e Segredos |
| AUTO_POOLS_WALLET_ADDRESS | Opcional, endereco publico para analise de carteira |
| AUTO_POOLS_DEFAULT_PROFILE | Opcional: conservador, moderado ou agressivo |
| AUTO_POOLS_EXECUTION_ENABLE | Opcional; habilita auditoria de signer, mas broadcast continua bloqueado |
| AUTO_POOLS_SIGNER_REF | Opcional; referencia de signer externo via secret manager |
| AUTO_POOLS_PRIVATE_KEY | Opcional para auditoria local de signer EVM; nunca usar em chat ou Git |
| AUTO_POOLS_EVM_PRIVATE_KEY / EVM_PRIVATE_KEY | Aliases legados opcionais |
| AUTO_POOLS_ALLOW_PRIVATE_KEY_SIGNER | Opcional; `true` permite preparar signer local em ambiente controlado |

## Exemplos de Uso

### Buscar pools conservadoras

**Usuario:** "auto-pools, encontre pools conservadoras com bom APR ajustado por risco"

**Bot:** retorna ranking em PT-BR com APR, TVL, drawdown, IL, motivos e bloqueios.

### Simular alocacao

**Usuario:** "simule 8% da carteira na melhor pool conservadora"

**Bot:** roda dry-run, calcula impacto de carteira, drawdown estimado e invalidacao.

## CLI local

```bash
python3 workspace/auto_pools.py --mode scan --profile conservador --limit 10
python3 workspace/auto_pools.py --mode scan --chain solana --profile conservador --limit 10
python3 workspace/auto_pools.py --mode rank --profile moderado --limit 10 --market-data
python3 workspace/auto_pools.py --mode dry-run --profile conservador --capital 1000 --allocation-pct 0.08
python3 workspace/auto_pools.py --mode plan --chain base --profile conservador --capital 1000 --allocation-pct 0.08 --json
python3 workspace/auto_pools.py --mode plan --chain solana --profile moderado --capital 1000 --allocation-pct 0.05 --json
python3 workspace/auto_pools.py --mode execute --action open --chain base --profile conservador --capital 1000 --allocation-pct 0.08 --confirm --json
python3 workspace/auto_pools.py --mode execute --action open --chain solana --profile moderado --capital 1000 --allocation-pct 0.05 --confirm --json
python3 workspace/auto_pools.py --mode swap --from-chain base --from-token USDC --to-token ETH --amount-usd 500 --profile conservador --json
python3 workspace/auto_pools.py --mode bridge --from-chain base --to-chain arbitrum --token USDC --amount-usd 250 --profile moderado --json
python3 workspace/auto_pools.py --mode wallet --wallet-address 0x0000000000000000000000000000000000000000 --json
python3 workspace/auto_pools.py --mode watch --json
python3 workspace/auto_pools.py --mode audit --json
python3 workspace/wizard.py
python3 workspace/wizard.py --headless --profile conservador --capital 1000 --allocation-pct 0.08 --limit 10
```

## Wizard

O wizard faz uma pergunta por vez, em portugues, e salva apenas configuracoes operacionais em `workspace/state/auto_pools_config.json` quando usado de modo interativo. Esse arquivo fica ignorado pelo Git.

Campos configurados:

- perfil de risco: conservador, moderado ou agressivo;
- capital de referencia em USD;
- percentual maximo por pool;
- quantidade de pools no ranking;
- endereco publico da carteira, opcional;
- modo de automacao: `dry-run` ou `guarded`.

Esta versao nao executa broadcast on-chain. Seed phrase nao e solicitada nem aceita. Chave privada local so pode ser lida de ENV/secret manager para auditoria/preparacao de signer EVM, nunca por argumento CLI, chat ou arquivo versionado.

## Plano de automacao

O modo `plan` gera um `PoolExecutionPlan` com:

- `adapter_family`: familia de integracao, como `evm-uniswap-v3`, `evm-slipstream`, `solana-orca-whirlpools` ou `solana-raydium`;
- `entry_steps`: approve/add liquidity ou instrucoes SPL/Whirlpool/Raydium;
- `exit_steps`: remove liquidity e collect fees;
- `rebalance_steps`: saida em duas fases e nova entrada;
- `guardrails`: slippage, gas, deadline, drawdown, IL, confirmacao obrigatoria e bloqueios.

O campo `guardrails.execution_enabled` fica `false` nesta versao mesmo que `AUTO_POOLS_EXECUTION_ENABLE` exista. Isso e intencional: o repo entrega automacao planejada e testavel, nao assinatura on-chain.

## Market data e indicadores

Quando `--market-data` esta ativo, a skill usa candles publicos para montar o ratio do par e medir:

- range observado;
- volatilidade realizada;
- drawdown observado;
- RSI14;
- ATR14 em percentual;
- Bollinger width;
- ADX14;
- regime: `lateral`, `tendencia`, `impulso` ou `misto`.

Esses indicadores afetam a lateralizacao e a volatilidade usada em drawdown/IL. Pares com ADX alto, RSI extremo, ATR alto ou Bollinger width largo perdem score e podem ser bloqueados pelo perfil conservador.

A fonte primaria e Binance. Se a Binance nao tiver candle suficiente para um ativo mapeado, a skill tenta CoinGecko OHLC. `COINGECKO_API_KEY` e opcional e deve ficar no ambiente/secret manager quando usada.

## Range dinamico

O score e o plano incluem `range_suggestion`:

- `lower_pct` e `upper_pct`: limites percentuais em torno do ratio spot;
- `width_pct`: largura total sugerida;
- `rebalance_trigger_pct`: deslocamento que deve acionar nova avaliacao;
- `confidence`: `alta`, `media` ou `baixa`;
- `notes`: contexto operacional.

O range usa range observado, ATR14, Bollinger width, ADX14, regime e perfil de risco. Em tendencia forte ou impulso, a confianca cai e a skill recomenda menor alocacao, range mais largo ou aguardar.

## Execucao guardada

O modo `execute` cria um recibo de simulacao para o ciclo completo de pool:

- `open`: simula preparar approve/add liquidity ou instrucoes SPL/Whirlpool/Raydium;
- `close`: simula remove liquidity;
- `collect`: simula coleta de fees;
- `rebalance`: simula saida em duas fases e nova entrada planejada.

Regras importantes:

- exige `--confirm` para sair de bloqueio por falta de confirmacao;
- nunca faz broadcast nesta release;
- sempre retorna `broadcasted=false` e `tx_hash=null`;
- persiste somente estado simulado em `workspace/state/auto_pools_positions.json`;
- o estado local fica fora do Git por `.gitignore`;
- se `AUTO_POOLS_EXECUTION_ENABLE=true` for definido sem `AUTO_POOLS_SIGNER_REF` ou `AUTO_POOLS_PRIVATE_KEY`, o recibo marca signer ausente, mas ainda nao transmite transacao;
- se `AUTO_POOLS_PRIVATE_KEY` existir, o recibo mostra apenas status/fingerprint curta, nunca o valor da chave.

## Private key e signer local

Fluxo seguro para automacao com chave privada:

1. Salvar a chave em secret manager/ENV como `AUTO_POOLS_PRIVATE_KEY`.
2. Opcionalmente habilitar teste local com `AUTO_POOLS_ALLOW_PRIVATE_KEY_SIGNER=true`.
3. Rodar `python3 workspace/auto_pools.py --mode audit --json` para validar formato e readiness.
4. Rodar `execute --confirm --json` para obter recibo auditavel com `signer_status`.

Invariantes:

- a chave nao pode ser passada por argumento CLI;
- a chave nao e impressa em JSON, logs ou docs;
- Solana private key local segue bloqueada nesta release;
- broadcast real continua bloqueado ate existir simulacao on-chain e adaptador transacional explicito.

## Carteira, watcher e auditoria

O modo `wallet` aceita apenas endereco publico EVM ou Solana. Ele nao consulta seed, chave privada, token ou cookie. A exposicao exibida vem do estado simulado local criado por `execute open`.

O modo `watch` revisa posicoes simuladas abertas e gera alertas como `guardrails-blocked`, `low-range-confidence`, `drawdown-watch` e `impermanent-loss-watch`. Ele nao usa signer e nao faz broadcast.

O modo `audit` roda checagens locais para secrets, artefatos runtime ignorados e status de seguranca de execucao. Use antes de tag/release.

## Bridge e swap

Os modos `swap` e `bridge` geram plano operacional e quote-only:

- validam chain suportada, token seguro, valor em USD e slippage;
- limitam slippage pelo perfil: conservador 30 bps, moderado 50 bps, agressivo 100 bps;
- sugerem familia de adaptador, como `evm-dex-aggregator-quote-only`, `solana-jupiter-quote-only`, `evm-across-stargate-quote-only` ou `wormhole-circle-cctp-quote-only`;
- sempre retornam `dry_run_only=true`, `broadcasted=false` e `tx_hash=null`.

Esta release nao monta transacao real, nao faz approve real e nao assina nada.

## Estrutura

```text
auto_pool_openclaw/
├── SKILL.md
├── skill.json
├── README.md
├── RELEASE_NOTES.md
├── AUDIT.md
├── LICENSE
├── workspace/
│   ├── auto_pools.py
│   ├── adapters/
│   ├── engines/
│   ├── models/
│   └── state/
└── references/
    ├── implementation-plan.md
    ├── scoring-model.md
    └── risk-guardrails.md
```

## Segurança

- Nunca coloque seed phrase, chave privada, token ou cookie no Git.
- O MVP e dry-run por padrao.
- Broadcast real de transacao esta fora da versao `0.7.0`.
- Qualquer execucao futura deve usar ENV/secret manager, simulacao previa e confirmacao explicita.

## Licenca

Proprietary. Ver LICENSE.
