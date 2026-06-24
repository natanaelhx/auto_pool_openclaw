# Fontes de Dados

## DefiLlama

Usada para pools, TVL, APR, projeto e chain.

Endpoint inicial:

```text
https://yields.llama.fi/pools
```

Filtros portados das skills-base:

- chains suportadas: Ethereum, Arbitrum, Base, Optimism, Polygon e Solana;
- protocolos confiaveis: Uniswap V3, Curve, Balancer, Aerodrome, Velodrome, Orca, Raydium, Kamino e Meteora;
- ativos seguros: stables principais, BTC wrappers, ETH/LSTs e SOL/LSTs;
- TVL minimo;
- APR minimo e maximo;
- rejeicao de outliers da fonte;
- rejeicao de pools inativas;
- em Solana, rejeicao de entrada que nao seja exposicao LP/multi quando esse campo estiver disponivel.

APY/APR recebido em formato percentual deve ser normalizado para decimal antes do score.

## CoinGecko

Opcional para preco e historico. Quando `COINGECKO_API_KEY` estiver configurada, a skill pode usar endpoints autenticados via ambiente ou secret manager.

## Binance Public Market Data

Usada opcionalmente para candles publicos quando `--market-data` estiver ativo.

```text
https://api.binance.com/api/v3/klines
```

Uso atual:

- buscar OHLC diario de BTC/USDT, ETH/USDT e SOL/USDT;
- montar OHLC sintetico do ratio do par quando os dois ativos tem preco;
- medir range observado, volatilidade realizada e drawdown observado;
- calcular RSI14, ATR14, Bollinger width, ADX14 e regime;
- cair para heuristica quando o ativo nao tem candle publico confiavel.

## Dune

Opcional para analise onchain profunda quando `DUNE_API_KEY` estiver configurada.

## Fallback

Se uma API falhar, o CLI usa dados de exemplo para manter o fluxo de teste funcionando. O bot deve avisar quando estiver usando fallback.
