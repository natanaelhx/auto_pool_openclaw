# Modelo de Score

O score final vai de 0 a 100.

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

## Decisoes

- `aprovado`: score >= 75 e sem bloqueios.
- `aprovado_com_limite`: score >= 60 e sem bloqueios.
- `aguardar`: score abaixo de 60 sem bloqueio critico.
- `bloqueado`: qualquer guardrail critico acionado.

## Perfis

- Conservador: prioriza TVL, liquidez, estabilidade e baixo IL.
- Moderado: aceita volatilidade media com TVL forte.
- Agressivo: aceita APR maior, mas com tamanho menor e risco explicito.

## Lateralizacao

A lateralizacao nao deve ser tratada como sinonimo de stablecoin. Stable/stable recebe nota alta por baixa variacao relativa, mas pares BTC/stable, ETH/stable, SOL/stable, BTC/ETH, ETH/LST, BTC wrappers e SOL/LST tambem podem entrar quando a liquidez, o drawdown estimado e o IL ficam dentro dos limites do perfil.

No MVP, quando nao ha serie historica de candles configurada, a lateralizacao usa uma heuristica conservadora por classe de ativo. A evolucao correta e usar market data real para medir range, ATR, volatilidade realizada e correlacao entre os dois ativos.
