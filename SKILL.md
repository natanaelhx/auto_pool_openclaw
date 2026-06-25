---
name: auto-pool-openclaw
description: Analisa, ranqueia, simula, planeja, audita e executa simulacao guardada de pools DeFi, swap e bridge em redes EVM e Solana, com signer privado via ENV, APR ajustado por risco, TVL, liquidez, RSI, ATR, Bollinger width, ADX, lateralizacao, range dinamico, exposicao de carteira, watcher, drawdown, impermanent loss, recibos auditaveis, guardrails e dry-run. Use para encontrar pools, simular LP, preparar add/remove liquidity, collect fees, rebalance, swap, bridge, validar private key em secret manager e revisar riscos antes de qualquer execucao on-chain. Keywords: auto pool, DeFi, LP, EVM, Solana, liquidity pool, private key, signer, swap, bridge, wallet, watcher, audit, APR, TVL, RSI, ATR, ADX, Bollinger, dynamic range, yield, impermanent loss, drawdown, dry-run, planner, guarded execution, guardrails.
---

# Auto Pool OpenClaw

Skill standalone para analise, ranking, simulacao e planejamento operacional de pools DeFi. Ela usa as skills DeFi/trading existentes apenas como referencia de engenharia e produto; nao depende delas em runtime.

## Quando Usar

- O usuario quer encontrar melhores pools DeFi por APR, TVL, liquidez e risco.
- O usuario quer simular alocacao em LP sem executar transacao real.
- O usuario quer avaliar drawdown, impermanent loss, lateralizacao e risco do par.
- O usuario quer comparar cenarios conservador, moderado ou agressivo.
- O usuario quer preparar automacao DeFi com guardrails operacionais.
- O usuario quer um plano de add/remove liquidity para EVM ou Solana antes de assinar qualquer transacao.
- O usuario quer revisar exposicao simulada por carteira publica, chain, protocolo e ativo.
- O usuario quer watcher/alertas locais ou auditoria de seguranca do repo.
- O usuario quer preparar swap ou bridge com quote/plano seguro antes de assinar qualquer transacao.
- O usuario quer validar automacao com private key guardada em ENV/secret manager, sem expor segredo no chat.

## Principio de Arquitetura

Esta skill nao e orquestradora. Ela nao chama outras skills como dependencia obrigatoria. As skills DeFi, trading, market data, portfolio, funding, squeeze, RSI e guardrails operacionais servem apenas como base conceitual.

A `auto-pools` implementa motor proprio de:

- coleta de pools;
- normalizacao de dados;
- scoring;
- risco;
- lateralizacao;
- dias estimados em lateralizacao/range;
- RSI14, ATR14, Bollinger width, ADX14 e regime do par quando `--market-data` estiver ativo;
- sugestao de range dinamico e gatilho de rebalance para pools concentradas;
- drawdown;
- impermanent loss;
- exposicao de carteira;
- watcher e auditoria local;
- plano quote-only de swap e bridge;
- auditoria de signer local/private key EVM via ENV;
- dry-run;
- saida operacional em PT-BR.

## Modos

- `scan`: buscar pools candidatas e aplicar filtros basicos.
- `rank`: ranquear pools por perfil de risco.
- `wizard`: configurar e testar a analise guiada em PT-BR, uma pergunta por vez.
- `dry-run`: simular alocacao e impacto de carteira.
- `plan`: gerar plano operacional de entrada/saida/rebalance sem assinar transacao.
- `swap`: gerar plano quote-only de swap com slippage limitado pelo perfil.
- `bridge`: gerar plano quote-only de bridge entre chains suportadas.
- `wallet`: revisar endereco publico e exposicao simulada por ativo, chain e protocolo.
- `watch`: revisar posicoes simuladas abertas e alertar por bloqueios, drawdown, IL ou baixa confianca de range.
- `audit`: varrer seguranca local, secrets e artefatos runtime ignorados.
- `execute`: simulacao guardada de `open`, `close`, `collect` e `rebalance`; nunca faz broadcast nesta versao.

## Regras de Seguranca

- Responder sempre em portugues do Brasil.
- Nunca pedir seed phrase em chat.
- Nunca salvar seed phrase em arquivo.
- Nunca pedir private key em chat, argumento CLI ou arquivo.
- Nunca commitar secrets, tokens, cookies ou chaves privadas.
- Quando private key for necessaria para teste local, usar apenas `AUTO_POOLS_PRIVATE_KEY` em ENV/secret manager.
- Operar em `dry-run` por padrao.
- Gerar planos com `execution_enabled=false` por padrao.
- Bloquear cenarios com TVL baixo, APR suspeito, liquidez fraca ou drawdown acima do limite.
- Nunca sugerir alocar 100% da carteira.
- Sugerir limites conservadores por pool, protocolo, chain e ativo.
- Para automacao com private key, validar apenas via ENV/secret manager: `AUTO_POOLS_PRIVATE_KEY`, opcionalmente `AUTO_POOLS_ALLOW_PRIVATE_KEY_SIGNER=true` em ambiente controlado. O output deve mostrar somente `signer_status` e fingerprint curta, nunca a chave.
- Para broadcast real futuro, exigir `AUTO_POOLS_EXECUTION_ENABLE=true`, signer seguro, simulacao on-chain previa e confirmacao explicita.

## Como Responder

Use uma estrutura curta, objetiva e em PT-BR:

```text
Resumo
- Decisao:
- Perfil:
- Melhor pool:
- APR esperado:
- APR ajustado por risco:
- Lateralizacao:
- Dias estimados em range:
- Drawdown estimado:
- IL estimado:

Motivos
- ...

Riscos
- ...

Acao sugerida
- scan / rank / dry-run / aguardar / bloquear
```

## Ferramenta Local

Quando precisar calcular ranking ou dry-run, use o script:

```bash
python3 workspace/auto_pools.py --mode rank --profile conservador --limit 10
python3 workspace/auto_pools.py --mode rank --chain solana --profile conservador --limit 10 --market-data
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

O script usa biblioteca padrao do Python e degrada com dados de exemplo quando APIs publicas nao responderem.

Com `--market-data`, o score usa candles publicos quando disponiveis para calcular range observado, volatilidade realizada, drawdown observado, RSI14, ATR14, Bollinger width, ADX14 e regime (`lateral`, `tendencia`, `impulso` ou `misto`). A fonte primaria e Binance; se nao houver candle suficiente, a skill tenta CoinGecko para ativos mapeados. Quando candles nao existem, a skill volta para heuristicas conservadoras.

O score e o plano incluem `range_suggestion` com centro, largura, limite inferior/superior percentual, gatilho de rebalance e confianca. Isso orienta pools concentradas, mas nao substitui simulacao on-chain.

## Wizard

O wizard deve conduzir onboarding em portugues do Brasil, uma pergunta por vez e com emoji na pergunta. Ele pode pedir perfil, capital de referencia, percentual maximo por pool, quantidade de pools no ranking, endereco publico da carteira e modo de automacao.

O wizard nunca deve pedir seed phrase, chave privada, token ou cookie. Private key so pode ser configurada fora do chat, no ambiente/secret manager do MQC. Broadcast real permanece desativado nesta versao.

## Automacao De Pools

Nesta versao a skill **monta o plano**, mas **nao monta/desmonta pool automaticamente on-chain**. O plano inclui:

- protocolo alvo e familia operacional: Uniswap V3/Aerodrome/Orca/Raydium quando identificavel;
- passos para approve, add liquidity, remove liquidity, collect fees e rebalance;
- limites de slippage, gas, deadline, drawdown e IL;
- status de seguranca: `dry_run_only`, `requires_confirmation` e `blocked_reasons`.

O modo `execute` apenas simula a execucao guardada e gera recibo com `broadcasted=false`, `tx_hash=null`, passos executados, bloqueios e `position_id`. Ele pode persistir estado local simulado em `workspace/state/auto_pools_positions.json`, que fica fora do Git.

O modo `wallet` aceita somente endereco publico e calcula exposicao a partir de posicoes simuladas locais. O modo `watch` revisa essas posicoes sem RPC assinado, sem signer e sem broadcast. O modo `audit` roda uma checagem local de secrets/artefatos antes de release.

Os modos `swap` e `bridge` sao quote-only/planner: validam chain, token, valor, slippage e adaptador sugerido, mas retornam `dry_run_only=true`, `broadcasted=false` e `tx_hash=null`.

So trate broadcast real como permitido quando uma versao futura implementar simulacao on-chain, adaptador transacional e confirmacao explicita. A v0.7.0 apenas audita readiness de signer/private key e mantem `broadcasted=false`.

## Plano Completo

O plano de implementacao fica em `references/implementation-plan.md`. Ele define analise mecanica de pools, rentabilidade, lateralizacao, APR, cenarios conservadores, ativos conservadores, drawdown do par, impermanent loss e roadmap ate execucao real.
