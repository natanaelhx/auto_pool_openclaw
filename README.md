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
| AUTO_POOLS_EXECUTION_ENABLE | Futuro, deve ficar ausente/false nesta versao |
| AUTO_POOLS_SIGNER_REF | Futuro, referencia de signer externo via secret manager |

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

Esta versao nao executa transacao real. Seed phrase e chave privada nao sao solicitadas, nao sao aceitas e nao devem ser salvas no repositorio. Para uma versao futura com execucao, usar apenas signer externo via secret manager/ENV.

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
- se `AUTO_POOLS_EXECUTION_ENABLE=true` for definido sem `AUTO_POOLS_SIGNER_REF`, o recibo marca `missing-signer-ref`, mas ainda nao transmite transacao.

## Carteira, watcher e auditoria

O modo `wallet` aceita apenas endereco publico EVM ou Solana. Ele nao consulta seed, chave privada, token ou cookie. A exposicao exibida vem do estado simulado local criado por `execute open`.

O modo `watch` revisa posicoes simuladas abertas e gera alertas como `guardrails-blocked`, `low-range-confidence`, `drawdown-watch` e `impermanent-loss-watch`. Ele nao usa signer e nao faz broadcast.

O modo `audit` roda checagens locais para secrets, artefatos runtime ignorados e status de seguranca de execucao. Use antes de tag/release.

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
- Execucao real de transacao esta fora da versao `0.5.0`.
- Qualquer execucao futura deve usar ENV/secret manager, simulacao previa e confirmacao explicita.

## Licenca

Proprietary. Ver LICENSE.
