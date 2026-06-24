# Guardrails de Risco

## Regras obrigatorias

- Nunca pedir seed phrase em chat.
- Nunca salvar seed phrase em arquivo.
- Nunca commitar secrets.
- MVP sempre em dry-run.
- Bloquear TVL baixo.
- Bloquear APR anormal sem explicacao.
- Bloquear liquidez de saida ruim.
- Bloquear drawdown acima do perfil.
- Bloquear IL acima do perfil.
- Nunca sugerir 100% da carteira.

## Limites iniciais

| Perfil | TVL minimo | Drawdown maximo | IL maximo |
|--------|------------|-----------------|-----------|
| conservador | US$ 20M | 10% | 3% |
| moderado | US$ 8M | 18% | 7% |
| agressivo | US$ 3M | 30% | 12% |

## Limites de carteira sugeridos

- Conservador: 5% a 10% por pool.
- Moderado: ate 15% por pool.
- Agressivo: ate 20% por pool, com alerta.
- Maximo por protocolo: 25%.
- Maximo por chain: 40%.

## Universo conservador

O perfil conservador nao deve buscar apenas stablecoin. Ele pode aceitar:

- stable/stable;
- ETH/stable;
- BTC/stable;
- SOL/stable, de forma condicional;
- BTC/ETH, de forma condicional;
- ETH/LST, BTC wrappers e SOL/LST, de forma condicional.

Pares alt/stable e volatil/volatil seguem bloqueados no conservador ate passarem por uma camada tecnica mais forte de lateralizacao, volatilidade realizada, drawdown historico e risco de IL.
