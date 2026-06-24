STABLES = {"USDC", "USDT", "DAI", "FRAX", "USDS", "LUSD", "PYUSD"}
ETH_ASSETS = {"ETH", "WETH", "STETH", "WSTETH", "RETH"}
BTC_ASSETS = {"BTC", "WBTC", "TBTC", "CBBTC"}
SOL_ASSETS = {"SOL", "MSOL", "JITOSOL"}


def classify_pair(assets):
    upper = [asset.upper() for asset in assets]
    stable_count = sum(1 for asset in upper if asset in STABLES)
    eth_count = sum(1 for asset in upper if asset in ETH_ASSETS)
    btc_count = sum(1 for asset in upper if asset in BTC_ASSETS)
    sol_count = sum(1 for asset in upper if asset in SOL_ASSETS)

    if stable_count >= 2:
        return "stable/stable"
    if stable_count == 1 and eth_count == 1:
        return "eth/stable"
    if stable_count == 1 and btc_count == 1:
        return "btc/stable"
    if btc_count >= 1 and eth_count >= 1:
        return "btc/eth"
    if stable_count == 1 and sol_count == 1:
        return "sol/stable"
    if eth_count >= 2:
        return "eth/lst"
    if btc_count >= 2:
        return "btc/wrapper"
    if sol_count >= 2:
        return "sol/lst"
    if stable_count == 1:
        return "alt/stable"
    return "volatil/volatil"


def conservative_blocks(assets):
    pair_type = classify_pair(assets)
    allowed = {"stable/stable", "eth/stable", "btc/stable", "btc/eth", "sol/stable", "eth/lst", "btc/wrapper", "sol/lst"}
    if pair_type not in allowed:
        return [f"Par {pair_type} fora da lista conservadora."]
    return []


def scenario_for_profile(profile, assets):
    pair_type = classify_pair(assets)
    if profile == "conservador":
        if pair_type == "stable/stable":
            return "Conservador defensivo: foco em estabilidade, baixo IL e liquidez."
        if pair_type in {"eth/stable", "btc/stable"}:
            return "Conservador balanceado: blue chip contra stable com limite de posicao."
        if pair_type == "sol/stable":
            return "Conservador condicional: SOL contra stable somente com TVL, drawdown e IL dentro dos limites."
        if pair_type == "btc/eth":
            return "Conservador condicional: apenas se lateralizacao e liquidez forem fortes."
        if pair_type in {"eth/lst", "btc/wrapper", "sol/lst"}:
            return "Conservador condicional: ativo blue chip correlacionado, exige TVL, drawdown e IL dentro dos limites."
        return "Bloqueio conservador: par fora do universo permitido."
    if profile == "moderado":
        return "Moderado: aceita volatilidade controlada com TVL e volume fortes."
    return "Agressivo: busca APR maior com tamanho reduzido e risco explicito."
