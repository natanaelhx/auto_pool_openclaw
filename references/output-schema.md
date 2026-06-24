# Schema de Saida

## Resumo em texto

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
- ...
```

## JSON

O CLI aceita `--json` para integracao futura.

Campos principais:

- `mode`
- `profile`
- `results`
- `pool`
- `score`
- `risk_adjusted_apr`
- `lateralization_score`
- `lateralization_days_estimate`
- `estimated_drawdown`
- `estimated_il`
- `decision`
- `blocks`
