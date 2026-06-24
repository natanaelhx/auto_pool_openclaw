## v0.3.0 — 2026-06-24

> Bump: MINOR
> Compatibilidade: retrocompativel com v0.2.0

### Added
- OHLC historico publico via Binance para `--market-data`.
- Indicadores RSI14, ATR14 percentual, Bollinger width e ADX14 sobre o ratio do par.
- Campo `trend_regime` com valores `lateral`, `tendencia`, `impulso` ou `misto`.
- Novos campos no `PoolScore`: `rsi_14`, `atr_pct_14`, `bollinger_width_pct`, `adx_14` e `trend_regime`.
- Testes para indicadores heurísticos e penalizacao de mercado em tendencia.

### Changed
- Lateralizacao agora considera range, volatilidade realizada, drawdown, ATR, Bollinger width, ADX e RSI quando market data existe.
- Volatilidade usada em drawdown/IL passa a considerar ATR, Bollinger width e tendencia por ADX.
- Resumo CLI exibe indicadores quando disponiveis.
- Roadmap atualizado: v0.4.0 fica para CoinGecko/range dinamico, v0.5.0 carteira, v0.6.0 watcher.

### Security
- Execucao real continua bloqueada.
- Nenhuma dependencia nova foi adicionada; os indicadores usam apenas biblioteca padrao Python.
- Nenhum segredo novo e necessario.

### Migration Notes
- Usuarios da v0.2.0 podem continuar usando todos os modos sem mudanca.
- Para ativar os indicadores, usar `--market-data`.
- Sem `--market-data` ou sem candles suficientes, a skill usa fallback heuristico.

### Validation
- [x] `skill.json.version` atualizado para `0.3.0`.
- [x] `python3 -m py_compile workspace/*.py workspace/adapters/*.py workspace/engines/*.py workspace/models/*.py workspace/state/*.py`.
- [x] `AUTO_POOLS_USE_SAMPLE=1 python3 -m unittest discover -s tests -v`.
- [x] Smoke `rank --market-data --json` retorna RSI/ATR/Bollinger/ADX.
- [x] Sem secrets, sem `.env`, sem artefatos de runtime versionados.

### Rollback
- Tag anterior estavel: `v0.2.0`.
- Procedimento: instalar `v0.2.0` ou publicar patch corretivo sem deletar release publicada.

## v0.2.0 — 2026-06-24

> Bump: MINOR
> Compatibilidade: retrocompativel com v0.1.0

### Added
- Modo `execute` com acoes `open`, `close`, `collect` e `rebalance`.
- Executor guardado em `workspace/executor.py`, sempre sem assinatura e sem broadcast nesta release.
- `ExecutionReceipt` com status, `position_id`, passos simulados, bloqueios, `broadcasted=false` e `tx_hash=null`.
- Store local de posicoes simuladas em `workspace/state/auto_pools_positions.json`.
- Testes unitarios cobrindo execucao guardada e exigencia de confirmacao explicita.

### Changed
- CLI `workspace/auto_pools.py` agora aceita `--action`, `--position-id` e `--confirm`.
- Roadmap atualizado para separar executor guardado, dados historicos, carteira, watcher e execucao real.
- `.gitignore` agora ignora corretamente `workspace/state/*.json`.

### Security
- Execucao real continua bloqueada.
- `execute` exige `--confirm` para simular acao operacional.
- Seed phrase, private key, token e cookie continuam proibidos no fluxo e fora do Git.
- O recibo nao expoe caminho absoluto do host.

### Migration Notes
- Usuarios da v0.1.0 podem continuar usando `scan`, `rank`, `dry-run`, `plan` e `wizard` sem mudanca.
- Para testar o novo fluxo, usar `--mode execute --action open --confirm --json`.

### Validation
- [x] `skill.json.version` atualizado para `0.2.0`.
- [x] `python3 -m py_compile workspace/*.py workspace/adapters/*.py workspace/engines/*.py workspace/models/*.py workspace/state/*.py`.
- [x] `AUTO_POOLS_USE_SAMPLE=1 python3 -m unittest discover -s tests -v`.
- [x] Smoke EVM `execute open` com `broadcasted=false`.
- [x] Smoke Solana `execute open` com `broadcasted=false`.
- [x] Sem secrets, sem `.env`, sem artefatos de runtime versionados.

### Rollback
- Tag anterior estavel: `v0.1.0`.
- Procedimento: instalar `v0.1.0` ou publicar patch corretivo sem deletar release publicada.

## v0.1.0 — 2026-06-24

> Bump: MINOR
> Compatibilidade: release inicial, nenhuma quebra

### Added
- Skill `auto-pool-openclaw` para scan, ranking, dry-run e plano operacional de pools EVM/Solana.
- CLI `workspace/auto_pools.py` com modos `scan`, `rank`, `dry-run`, `plan` e `wizard`.
- Planner seguro `PoolExecutionPlan` com entrada, saida, collect/rebalance e guardrails.
- Suporte de planejamento para familias EVM Uniswap V3/Aerodrome/Curve/Balancer e Solana Orca/Raydium.
- Testes locais com py_compile, unittest e smoke de plano EVM/Solana.

### Security
- Execucao on-chain real bloqueada nesta versao.
- `guardrails.execution_enabled` retorna `false` mesmo quando existe env de execucao.
- Seed phrase, private key, token e cookie nao sao solicitados nem versionados.

### Migration Notes
- Release inicial do repo `natanaelhx/auto_pool_openclaw`.

### Validation
- [x] SKILL.md frontmatter validado.
- [x] skill.json.version atualizado e bate com a tag planejada `v0.1.0`.
- [x] Smoke test/scripts compilam com `python3 -m py_compile`.
- [x] Sem secrets, sem `.env`, sem artefatos de runtime versionados.
- [x] README/SKILL.md sem paths absolutos do host.
- [x] Release manual necessaria porque o token atual nao possui escopo `workflow` para versionar GitHub Actions.

### Rollback
- Tag anterior estavel: nenhuma.
- Procedimento: remover instalacao da skill ou publicar patch corretivo.
