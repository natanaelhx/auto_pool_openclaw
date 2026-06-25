import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional


STATE_DIR = os.path.dirname(os.path.abspath(__file__))
POSITIONS_PATH = os.path.join(STATE_DIR, "auto_pools_positions.json")
DECISIONS_PATH = os.path.join(STATE_DIR, "auto_pools_decisions.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_positions(path: str = POSITIONS_PATH) -> Dict:
    if not os.path.exists(path):
        return {"version": 1, "positions": []}
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if "positions" not in data:
        data["positions"] = []
    return data


def save_positions(data: Dict, path: str = POSITIONS_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp_path, path)


def upsert_position(position: Dict, path: str = POSITIONS_PATH) -> Dict:
    data = load_positions(path)
    positions: List[Dict] = data["positions"]
    position["updated_at"] = _now_iso()
    for index, existing in enumerate(positions):
        if existing["position_id"] == position["position_id"]:
            position.setdefault("created_at", existing.get("created_at", _now_iso()))
            positions[index] = position
            save_positions(data, path)
            return position
    position.setdefault("created_at", _now_iso())
    positions.append(position)
    save_positions(data, path)
    return position


def find_position(position_id: str, path: str = POSITIONS_PATH) -> Optional[Dict]:
    data = load_positions(path)
    for position in data["positions"]:
        if position.get("position_id") == position_id:
            return position
    return None


def load_decisions(path: str = DECISIONS_PATH) -> Dict:
    if not os.path.exists(path):
        return {"version": 1, "decisions": []}
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if "decisions" not in data:
        data["decisions"] = []
    return data


def save_decisions(data: Dict, path: str = DECISIONS_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(tmp_path, path)


def append_decision(decision: Dict, path: str = DECISIONS_PATH) -> Dict:
    data = load_decisions(path)
    decision["created_at"] = _now_iso()
    data["decisions"].append(decision)
    save_decisions(data, path)
    return decision
