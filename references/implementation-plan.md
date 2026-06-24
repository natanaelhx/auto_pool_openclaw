# Plano Completo da Auto Pool OpenClaw

## Objetivo

Criar uma skill standalone chamada `auto-pool-openclaw` para fazer analise mecanica de melhores pools, rentabilidade, tempo de lateralizacao, APR, drawdown do par, impermanent loss, cenarios conservadores e plano de automacao EVM/Solana.

## Regras centrais

- A skill nao depende das outras skills em runtime.
- As skills ja criadas servem como base de engenharia e referencia de produto.
- Tudo deve responder em portugues do Brasil.
- O MVP deve ser seguro e operar em dry-run.
- Execucao real fica para roadmap futuro.

## Fluxo operacional

### 1. Scan

Coletar pools por fontes publicas/API:

- DefiLlama para TVL, APR, protocolo e chain.
- Filtros APR EVM/Solana baseados em chain suportada, protocolo confiavel, token seguro, TVL, APR minimo/maximo, outlier e exposicao LP.
- CoinGecko opcional para preco/historico.
- Dune opcional para analise onchain.
- Fallback local para testes quando API falhar.

### 2. Analise mecanica

Para cada pool:

- validar chain;
- validar protocolo;
- calcular TVL;
- calcular volume 24h;
- calcular APR bruto;
- separar APR base e APR de rewards quando disponivel;
- estimar liquidez de saida;
- estimar qualidade do par;
- aplicar guardrails.

### 3. Lateralizacao

Calcular:

- score de lateralizacao;
- dias estimados em range;
- volatilidade esperada;
- risco de rompimento.

No MVP, a lateralizacao usa heuristica por tipo de par. No roadmap, entra historico real com ATR, RSI, Bollinger width e ADX.

Na versao atual, a skill ja pode usar `--market-data` para medir lateralizacao com candles publicos quando disponiveis:

- range observado do ratio do par;
- volatilidade realizada;
- drawdown observado;
- fallback heuristico quando nao houver candle confiavel.

### 4. Cenarios conservadores

Ativos permitidos no conservador:

- stable/stable;
- ETH/stable;
- BTC/stable;
- BTC/ETH com liquidez forte e lateralizacao clara.
- SOL/stable com liquidez forte, drawdown e IL dentro dos limites.

Bloqueios conservadores:

- alt/stable de maior risco;
- volatil/volatil;
- TVL baixo;
- APR suspeito;
- drawdown acima de 10%;
- IL acima de 3%.

### 5. Drawdown do par

Calcular possivel drawdown com base em:

- volatilidade estimada;
- tipo de par;
- liquidez;
- perfil de risco;
- historico real em versao futura.

### 6. Impermanent loss

Estimar IL com base no movimento relativo esperado do par.

### 7. Ranking

Score final:

```text
score_final =
  0.20 * score_liquidez +
  0.20 * score_apr_ajustado +
  0.15 * score_lateralizacao +
  0.15 * score_risco_ativo +
  0.10 * score_il +
  0.10 * score_drawdown +
  0.10 * score_exposicao_carteira
```

### 8. Dry-run

Simular:

- capital alocado;
- yield anual esperado;
- perda estimada por drawdown;
- perda estimada por IL;
- divisao do par;
- decisao final.

### 9. Plano operacional

Gerar `PoolExecutionPlan` sem assinatura:

- EVM: wallet publica, saldos ERC-20, contratos do protocolo, approve limitado, quote, add liquidity, remove liquidity e collect fees.
- Solana: wallet publica, saldos SPL, ATAs, vaults, tick/bin arrays, add liquidity, remove liquidity e collect fees.
- Guardrails: slippage, gas, deadline, drawdown, IL, `dry_run_only`, `requires_confirmation` e `blocked_reasons`.
- Rebalance: sempre duas fases, sair/coletar primeiro e entrar de novo depois de nova simulacao.

Nesta etapa nao ha signer, assinatura nem broadcast.

## Roadmap

### 0.1.0

- Estrutura da skill.
- Scan, rank e dry-run.
- Score inicial.
- Cenarios conservadores.
- Drawdown/IL estimados.
- Plano operacional EVM/Solana sem execucao on-chain.

### 0.2.0

- Executor guardado para `open`, `close`, `collect` e `rebalance`.
- Recibo auditavel com `broadcasted=false`, `tx_hash=null`, bloqueios e passos simulados.
- Estado persistente local de posicoes simuladas.
- CLI `--mode execute --action ... --confirm`.

### 0.3.0

- Historico OHLC publico via Binance quando `--market-data` estiver ativo.
- RSI14, ATR14, Bollinger width e ADX14.
- Lateralizacao por dados reais do ratio do par, com fallback heuristico.

### 0.4.0

- Historico CoinGecko opcional para ativos sem Binance.
- Range dinamico sugerido para pools concentradas.
- Gatilho de rebalance e confianca do range.

### 0.5.0

- Carteira multichain por endereco.
- Exposicao por ativo, chain e protocolo.

### 0.6.0

- Watcher e alertas.
- Estado persistente.

### 1.0.0

- Execucao real com secrets por ambiente/secret manager, simulacao, confirmacao e rollback.
