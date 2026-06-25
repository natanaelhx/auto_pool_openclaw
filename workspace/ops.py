from typing import List

from adapters.defillama import SAFE_TOKENS
from models.schemas import OperationPlan
from signer import signer_status


SUPPORTED_CHAINS = {"ethereum", "arbitrum", "base", "optimism", "polygon", "solana"}
EVM_CHAINS = {"ethereum", "arbitrum", "base", "optimism", "polygon"}
STABLE_BRIDGE_TOKENS = {"USDC", "USDT", "DAI"}


def _normalize_token(token: str) -> str:
    return (token or "").strip().upper()


def _normalize_chain(chain: str) -> str:
    return (chain or "").strip().lower()


def _amount_block(amount_usd: float) -> List[str]:
    if amount_usd <= 0:
        return ["invalid-amount-usd"]
    if amount_usd > 100_000:
        return ["amount-requires-manual-review"]
    return []


def _slippage_for_profile(profile: str, requested_bps: int) -> int:
    caps = {"conservador": 30, "moderado": 50, "agressivo": 100}
    cap = caps.get(profile, 50)
    if requested_bps <= 0:
        return cap
    return min(requested_bps, cap)


def _swap_adapter(chain: str) -> str:
    if chain == "solana":
        return "solana-jupiter-quote-only"
    if chain in EVM_CHAINS:
        return "evm-dex-aggregator-quote-only"
    return "unsupported"


def _bridge_adapter(from_chain: str, to_chain: str, token: str) -> str:
    if from_chain in EVM_CHAINS and to_chain in EVM_CHAINS:
        if token in STABLE_BRIDGE_TOKENS:
            return "evm-across-stargate-quote-only"
        return "evm-canonical-bridge-quote-only"
    if "solana" in {from_chain, to_chain}:
        return "wormhole-circle-cctp-quote-only"
    return "unsupported"


def build_swap_plan(chain: str, from_token: str, to_token: str, amount_usd: float, profile: str, slippage_bps: int = 0) -> OperationPlan:
    chain = _normalize_chain(chain)
    from_token = _normalize_token(from_token)
    to_token = _normalize_token(to_token)
    slippage = _slippage_for_profile(profile, slippage_bps)
    blocked = _amount_block(amount_usd)
    adapter = _swap_adapter(chain)
    signer = signer_status(chain)

    if chain not in SUPPORTED_CHAINS:
        blocked.append("unsupported-chain")
    if from_token == to_token:
        blocked.append("same-token-swap")
    if from_token not in SAFE_TOKENS or to_token not in SAFE_TOKENS:
        blocked.append("unsafe-token")
    if adapter == "unsupported":
        blocked.append("unsupported-swap-adapter")

    return OperationPlan(
        mode="swap",
        status="blocked" if blocked else "planned",
        profile=profile,
        from_chain=chain,
        to_chain=chain,
        from_token=from_token,
        to_token=to_token,
        amount_usd=round(amount_usd, 2),
        adapter_family=adapter,
        slippage_bps=slippage,
        dry_run_only=True,
        broadcasted=False,
        tx_hash=None,
        blocked_reasons=sorted(set(blocked)),
        steps=[
            "Validar endereco publico, saldo e allowance atual.",
            "Buscar quote em agregador/DEX sem assinar transacao.",
            "Checar impacto de preco, slippage maximo e rota.",
            "Montar plano de approve limitado quando necessario.",
            "Bloquear assinatura e broadcast nesta release.",
        ],
        notes=[
            "Plano de swap e quote-only; nao assina nem transmite transacao.",
            "Nunca informar seed phrase, chave privada, token ou cookie no chat.",
            "Private key local so pode vir de env/secret manager e nao e impressa.",
            "Broadcast real exige simulacao on-chain e confirmacao explicita.",
        ],
        signer_status=signer,
    )


def build_bridge_plan(from_chain: str, to_chain: str, token: str, amount_usd: float, profile: str, slippage_bps: int = 0) -> OperationPlan:
    from_chain = _normalize_chain(from_chain)
    to_chain = _normalize_chain(to_chain)
    token = _normalize_token(token)
    slippage = _slippage_for_profile(profile, slippage_bps)
    blocked = _amount_block(amount_usd)
    adapter = _bridge_adapter(from_chain, to_chain, token)
    signer = signer_status(from_chain)

    if from_chain not in SUPPORTED_CHAINS or to_chain not in SUPPORTED_CHAINS:
        blocked.append("unsupported-chain")
    if from_chain == to_chain:
        blocked.append("same-chain-bridge")
    if token not in SAFE_TOKENS:
        blocked.append("unsafe-token")
    if adapter == "unsupported":
        blocked.append("unsupported-bridge-adapter")

    return OperationPlan(
        mode="bridge",
        status="blocked" if blocked else "planned",
        profile=profile,
        from_chain=from_chain,
        to_chain=to_chain,
        from_token=token,
        to_token=token,
        amount_usd=round(amount_usd, 2),
        adapter_family=adapter,
        slippage_bps=slippage,
        dry_run_only=True,
        broadcasted=False,
        tx_hash=None,
        blocked_reasons=sorted(set(blocked)),
        steps=[
            "Validar endereco publico origem/destino e saldo disponivel.",
            "Buscar quote de bridge sem assinar transacao.",
            "Checar taxa, tempo estimado, slippage, finality e risco da rota.",
            "Montar plano de approve limitado quando necessario.",
            "Bloquear assinatura e broadcast nesta release.",
        ],
        notes=[
            "Plano de bridge e quote-only; nao assina nem transmite transacao.",
            "Preferir stables e blue chips; rotas com token inseguro sao bloqueadas.",
            "Private key local so pode vir de env/secret manager e nao e impressa.",
            "Broadcast real exige simulacao on-chain e confirmacao explicita.",
        ],
        signer_status=signer,
    )
