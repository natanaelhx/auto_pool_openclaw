## v0.6.0 — 2026-06-24

> Bump: MINOR
> Compatibilidade: retrocompativel com v0.5.0

### Added
- Modo `swap` para gerar plano quote-only de swap sem assinatura e sem broadcast.
- Modo `bridge` para gerar plano quote-only de bridge entre chains suportadas.
- Modulo `workspace/ops.py` com guardrails de chain, token, valor, slippage e adaptador.
- `OperationPlan` para representar planos seguros de swap/bridge.
- Testes unitarios para swap planejado, token inseguro, bridge planejado e bridge na mesma chain.

### Changed
- CLI `workspace/auto_pools.py` agora aceita `--mode swap` e `--mode bridge`.
- Novos argumentos: `--from-chain`, `--to-chain`, `--from-token`, `--to-token`, `--token`, `--amount-usd` e `--slippage-bps`.
- Docs atualizados com exemplos e invariantes de bridge/swap.

### Security
- Swap/bridge sao quote-only: nao fazem approve real, assinatura ou broadcast.
- Slippage e limitado por perfil: conservador 30 bps, moderado 50 bps, agressivo 100 bps.
- Tokens fora da allowlist segura sao bloqueados.
- Recibos/planos continuam com `broadcasted=false` e `tx_hash=null`.

### Migration Notes
- Usuarios da v0.5.0 podem continuar usando todos os modos sem mudanca.
- Para planejar swap: `python3 workspace/auto_pools.py --mode swap --from-chain base --from-token USDC --to-token ETH --amount-usd 500 --json`.
- Para planejar bridge: `python3 workspace/auto_pools.py --mode bridge --from-chain base --to-chain arbitrum --token USDC --amount-usd 250 --json`.

### Validation
- [x] `skill.json.version` atualizado para `0.6.0`.
- [x] `python3 -m py_compile workspace/*.py workspace/adapters/*.py workspace/engines/*.py workspace/models/*.py workspace/state/*.py`.
- [x] `AUTO_POOLS_USE_SAMPLE=1 python3 -m unittest -v`.
- [x] Smoke `swap --json` retorna plano `dry_run_only=true`.
- [x] Smoke `bridge --json` retorna plano `dry_run_only=true`.
- [x] Smoke `audit --json` retorna status pass.
- [x] Sem secrets, sem `.env`, sem artefatos de runtime versionados.

### Rollback
- Tag anterior estavel: `v0.5.0`.
- Procedimento: instalar `v0.5.0` ou publicar patch corretivo sem deletar release publicada.

## v0.5.0 — 2026-06-24

> Bump: MINOR
> Compatibilidade: retrocompativel com v0.4.0

### Added
- Modo `wallet` para validar endereco publico EVM/Solana e consolidar exposicao simulada por ativo, chain e protocolo.
- Modo `watch` para revisar posicoes simuladas abertas e alertar sobre bloqueios, baixa confianca de range, drawdown e IL.
- Modo `audit` para checar secrets, artefatos runtime ignorados e status de seguranca antes de release.
- Modulos `workspace/wallet.py`, `workspace/watcher.py` e `workspace/audit.py`.
- Relatorio `AUDIT.md` com escopo, invariantes e validacao da release.
- `tests/__init__.py` para `python3 -m unittest` descobrir a suite padrao.
- Testes unitarios para carteira, watcher e auditoria.

### Changed
- CLI `workspace/auto_pools.py` agora aceita `--mode wallet`, `--mode watch`, `--mode audit` e `--wallet-address`.
- Roadmap seguro consolidado: carteira/watch/auditoria ficam entregues sem signer e sem broadcast.
- Docs atualizados com os novos modos e schemas.

### Security
- `wallet` aceita somente endereco publico e rejeita formato invalido.
- `watch` opera apenas sobre estado local simulado.
- `audit` varre padroes de segredo sem imprimir valores sensiveis.
- Execucao real continua bloqueada; `broadcasted=false` e `tx_hash=null` permanecem invariantes do executor.

### Migration Notes
- Usuarios da v0.4.0 podem continuar usando todos os modos sem mudanca.
- Para revisar exposicao simulada, primeiro gere uma posicao com `execute open --confirm`.
- Para auditoria local, usar `python3 workspace/auto_pools.py --mode audit --json`.

### Validation
- [x] `skill.json.version` atualizado para `0.5.0`.
- [x] `python3 -m py_compile workspace/*.py workspace/adapters/*.py workspace/engines/*.py workspace/models/*.py workspace/state/*.py`.
- [x] `AUTO_POOLS_USE_SAMPLE=1 python3 -m unittest -v`.
- [x] Smoke `wallet --json` rejeita formato invalido e aceita endereco publico.
- [x] Smoke `watch --json` retorna `broadcasted=false`.
- [x] Smoke `audit --json` retorna status pass.
- [x] Sem secrets, sem `.env`, sem artefatos de runtime versionados.

### Rollback
- Tag anterior estavel: `v0.4.0`.
- Procedimento: instalar `v0.4.0` ou publicar patch corretivo sem deletar release publicada.

## v0.4.0 — 2026-06-24

> Bump: MINOR
> Compatibilidade: retrocompativel com v0.3.0

### Added
- Fallback CoinGecko OHLC para ativos sem candles Binance suficientes.
- Mapeamento conservador de symbols para CoinGecko IDs.
- `RangeSuggestion` com `lower_pct`, `upper_pct`, `width_pct`, `rebalance_trigger_pct`, `confidence` e notas.
- `range_suggestion` em `PoolScore` e `PoolExecutionPlan`.
- Motor `workspace/engines/range_suggestion.py`.
- Teste unitario para fallback CoinGecko via monkeypatch local.

### Changed
- `--market-data` agora tenta Binance primeiro e CoinGecko depois.
- Planos `plan` e ranking expõem range dinamico para pools concentradas.
- Docs de API/scoring/roadmap atualizados.

### Security
- Execucao real continua bloqueada.
- `COINGECKO_API_KEY` permanece opcional e deve ficar somente em env/secret manager.
- Nenhuma seed/private key e solicitada.

### Migration Notes
- Usuarios da v0.3.0 podem continuar usando todos os modos sem mudanca.
- Para usar fallback CoinGecko autenticado, configurar `COINGECKO_API_KEY` no ambiente.
- Sem CoinGecko ou sem candles confiaveis, o fallback heuristico permanece ativo.

### Validation
- [x] `skill.json.version` atualizado para `0.4.0`.
- [x] `python3 -m py_compile workspace/*.py workspace/adapters/*.py workspace/engines/*.py workspace/models/*.py workspace/state/*.py`.
- [x] `AUTO_POOLS_USE_SAMPLE=1 python3 -m unittest discover -s tests -v`.
- [x] Smoke `plan --market-data --json` retorna `range_suggestion`.
- [x] Smoke `execute open` continua `broadcasted=false` e `tx_hash=null`.
- [x] Sem secrets, sem `.env`, sem artefatos de runtime versionados.

### Rollback
- Tag anterior estavel: `v0.3.0`.
- Procedimento: instalar `v0.3.0` ou publicar patch corretivo sem deletar release publicada.

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
