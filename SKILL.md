---
name: auto-pool-openclaw
description: Analisa, ranqueia, simula e planeja automacao segura de pools DeFi em redes EVM e Solana, com APR ajustado por risco, TVL, liquidez, lateralizacao, drawdown, impermanent loss, plano de entrada/saida, guardrails e dry-run. Use para encontrar pools, simular alocacao, preparar add/remove liquidity e revisar riscos antes de qualquer execucao on-chain. Keywords: auto pool, DeFi, LP, EVM, Solana, liquidity pool, APR, TVL, yield, impermanent loss, drawdown, dry-run, planner, guardrails.
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

## Principio de Arquitetura

Esta skill nao e orquestradora. Ela nao chama outras skills como dependencia obrigatoria. As skills DeFi, trading, market data, portfolio, funding, squeeze, RSI e guardrails operacionais servem apenas como base conceitual.

A `auto-pools` implementa motor proprio de:

- coleta de pools;
- normalizacao de dados;
- scoring;
- risco;
- lateralizacao;
- dias estimados em lateralizacao/range;
- drawdown;
- impermanent loss;
- exposicao de carteira;
- dry-run;
- saida operacional em PT-BR.

## Modos

- `scan`: buscar pools candidatas e aplicar filtros basicos.
- `rank`: ranquear pools por perfil de risco.
- `wizard`: configurar e testar a analise guiada em PT-BR, uma pergunta por vez.
- `analyze`: analisar um par/pool especifico quando houver dados suficientes.
- `dry-run`: simular alocacao e impacto de carteira.
- `plan`: gerar plano operacional de entrada/saida/rebalance sem assinar transacao.
- `watch`: monitoramento futuro de shortlist/posicao.
- `execute`: reservado para versao futura; nunca execute transacao real nesta versao.

## Regras de Seguranca

- Responder sempre em portugues do Brasil.
- Nunca pedir seed phrase em chat.
- Nunca salvar seed phrase em arquivo.
- Nunca commitar secrets, tokens, cookies ou chaves privadas.
- Operar em `dry-run` por padrao.
- Gerar planos com `execution_enabled=false` por padrao.
- Bloquear cenarios com TVL baixo, APR suspeito, liquidez fraca ou drawdown acima do limite.
- Nunca sugerir alocar 100% da carteira.
- Sugerir limites conservadores por pool, protocolo, chain e ativo.
- Para execucao real futura, exigir `AUTO_POOLS_EXECUTION_ENABLE=true`, signer externo por `AUTO_POOLS_SIGNER_REF`, simulacao previa e confirmacao explicita.

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
python3 workspace/wizard.py
python3 workspace/wizard.py --headless --profile conservador --capital 1000 --allocation-pct 0.08 --limit 10
```

O script usa biblioteca padrao do Python e degrada com dados de exemplo quando APIs publicas nao responderem.

## Wizard

O wizard deve conduzir onboarding em portugues do Brasil, uma pergunta por vez e com emoji na pergunta. Ele pode pedir perfil, capital de referencia, percentual maximo por pool, quantidade de pools no ranking, endereco publico da carteira e modo de automacao.

O wizard nunca deve pedir seed phrase, chave privada, token ou cookie. A automacao real permanece desativada nesta versao; qualquer signer futuro deve vir de variavel de ambiente ou secret manager, nunca de texto colado no chat ou arquivo versionado.

## Automacao De Pools

Nesta versao a skill **monta o plano**, mas **nao monta/desmonta pool automaticamente on-chain**. O plano inclui:

- protocolo alvo e familia operacional: Uniswap V3/Aerodrome/Orca/Raydium quando identificavel;
- passos para approve, add liquidity, remove liquidity, collect fees e rebalance;
- limites de slippage, gas, deadline, drawdown e IL;
- status de seguranca: `dry_run_only`, `requires_confirmation` e `blocked_reasons`.

So trate execucao real como permitida quando uma versao futura implementar signer seguro, simulacao on-chain e confirmacao explicita.

## Plano Completo

O plano de implementacao fica em `references/implementation-plan.md`. Ele define analise mecanica de pools, rentabilidade, lateralizacao, APR, cenarios conservadores, ativos conservadores, drawdown do par, impermanent loss e roadmap ate execucao real.
