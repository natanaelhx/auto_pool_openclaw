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
