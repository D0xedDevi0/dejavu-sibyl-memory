"""Sovereign Memory — memory as an onchain, ownable, self-identifying asset.

This is the spine of the upgraded hackathon entry. It makes Sibyl's own framing
("the memory as a dynamic data layer") *literal and economic*:

  (1) CONTENT-ADDRESSED ROOT — the entire store (WARM + ARCH entities, COLD
      journal, and graph edges) folds into one deterministic SHA-256 root. Memory has a
      fingerprint; it can be compared, ported, and committed.

  (2) IDENTITY = MEMORY — an agent's identity hash is derived purely from its
      store's root. Spawn a fresh box, mount the same store, and it IS the same
      being. Wipe the store and the identity changes. "The agent isn't the code,
      it's the memory."

  (3) SOVEREIGN MINT / COMMIT — the memory root is committed onchain (Base) as a
      dust wallet op carrying the root in `data`. The memory becomes an *asset
      that is anchored to a chain and has an owner address*. Deleting the store
      does not just lose a decision — it orphan-destroys the committed asset.
      Memory-load-bearing, with an economic consequence.

  (4) QUERY ECONOMICS — the store is a *queryable, payable data layer*: a read
      endpoint that costs (x402) for anyone not the owner. Honest stub: the
      settlement path needs a funded USDC wallet (real x402 is optional); the
      price/ledger mechanics are real and tested.

All onchain paths default to dry-run for safety (DEJAVU_DRY_RUN=0 to broadcast),
mirroring base_action.py. Pure additions — existing fleet/dejavu behavior untouched.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from eth_account.datastructures import SignedTransaction

from . import base_action
from .config import BASE_EXPLORER, Config
from .graph_audit import _entity_id
from .memory import Memory, json_loads_any

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# (1) CONTENT-ADDRESSED ROOT  — the store's fingerprint
# ---------------------------------------------------------------------------

def _h(x: str) -> str:
    return hashlib.sha256(x.encode()).hexdigest()


def memory_root(memory: Memory, *, include_journal: bool = True) -> dict:
    """Deterministic SHA-256 root over the store's live content.

    Folds sorted entities + sorted journal events + sorted graph edges into one
    digest. Deterministic for a given store (ordering is canonicalized), so two
    identical stores produce identical roots and any single-row change flips it.
    """
    # WARM + ARCH entities, canonical order by (category, name). ARCH is a
    # recoverable storage tier, not content destruction, so moving an entity
    # between WARM and ARCH must preserve the sovereign full-store root.
    entities = memory.list_entities(limit=100000)
    archived = memory.list_archived()
    ent_parts = []
    for e in [*entities, *archived]:
        ent_parts.append(f"{e.get('category')}|{e.get('name')}|"
                         f"{json.dumps(e.get('body'), sort_keys=True, default=str)}")
    ent_digest = _h("\n".join(sorted(ent_parts)))

    # COLD journal, insertion order (id order is canonical for an append log).
    j_digest = "0" * 64
    events: list = []
    if include_journal:
        events = memory.read_events(limit=100000)
        for ev in events:
            payload = json.dumps({
                "id": ev.get("id"), "ts": ev.get("ts"),
                "evaluated": ev.get("evaluated"), "acted": ev.get("acted"),
                "forward": ev.get("forward"), "extra": ev.get("extra"),
            }, sort_keys=True, default=str)
            j_digest = _h(j_digest + payload)

    # REFERENCE tier (static knowledge + L7 sovereign anchor). Folding this in
    # means the store's fingerprint reflects its own onchain history — a memory
    # that knows it owns itself. Canonical order by doc_key.
    ref_parts = []
    for ref in memory.list_references():
        ref_parts.append(f"{ref.get('doc_key')}|"
                         f"{json.dumps(ref.get('body'), sort_keys=True, default=str)}|"
                         f"{json.dumps(ref.get('metadata'), sort_keys=True, default=str)}")
    ref_digest = _h("\n".join(sorted(ref_parts)))

    # Graph edges from the native entity_relations table.
    edge_parts = []
    tenant = memory.tenant_id
    try:
        with memory.client.storage.transaction() as conn:
            for from_id, to_id, rtype in conn.execute(
                "SELECT from_id, to_id, relation_type FROM entity_relations "
                "WHERE tenant_id=? ORDER BY from_id, to_id, relation_type",
                (tenant,),
            ):
                edge_parts.append(f"{from_id}->{rtype}->{to_id}")
    except Exception as e:  # pragma: no cover - table/tenant variance
        log.warning("[sovereign] graph edges unavailable (%s)", e)
    edge_digest = _h("\n".join(sorted(edge_parts)))

    root = _h(f"{tenant}|{ent_digest}|{j_digest}|{ref_digest}|{edge_digest}")
    return {
        "root": root,
        "tenant": tenant,
        "entities": len(entities),
        "archived_entities": len(archived),
        "journal_rows": (len(events) if include_journal else 0),
        "references": len(ref_parts),
        "edges": len(edge_parts),
    }


# ---------------------------------------------------------------------------
# (2) IDENTITY = MEMORY
# ---------------------------------------------------------------------------

def identity(memory: Memory, *, seed: str = "dejavu-sovereign") -> dict:
    """Derive the agent's identity hash purely from its store's root.

    Same store (same content) -> same identity, in ANY runtime. This is the
    "the agent IS its memory" claim: it is portable across boxes and a fresh
    spawn mounting the same store is the same being.
    """
    r = memory_root(memory)
    ident = _h(f"{seed}|{r['root']}")
    return {"id": ident[:16], "id_sha256": ident, "root": r["root"],
            "entities": r["entities"], "journal_rows": r["journal_rows"]}


def is_same_being(identity_a: dict, identity_b: dict) -> bool:
    """Two runtimes mounting the same store are the same being."""
    return identity_a["id_sha256"] == identity_b["id_sha256"]


# ---------------------------------------------------------------------------
# (3) SOVEREIGN MINT / COMMIT  — anchor the memory root onchain
# ---------------------------------------------------------------------------

DUST = 1000  # wei; symbolic — the point is the root in `data`, not the value


@dataclass
class MintReceipt:
    dry_run: bool
    root: str
    identity_id: str
    owner: str
    details: dict[str, Any] = field(default_factory=dict)
    tx_hash: str | None = None
    explorer_url: str | None = None

    def as_dict(self) -> dict:
        return {
            "dry_run": self.dry_run, "root": self.root,
            "identity_id": self.identity_id, "owner": self.owner,
            "details": self.details, "tx_hash": self.tx_hash,
            "explorer_url": self.explorer_url,
        }


def _commit_tx(config: Config, data_hex: str) -> SignedTransaction:
    """Sign a dust Base tx carrying the memory root in `data` (self-transfer)."""
    acct = base_action._load_account(config)
    chain_id = int(base_action._rpc(config.rpc_url, "eth_chainId", []), 16)
    nonce = int(base_action._rpc(config.rpc_url, "eth_getTransactionCount",
                                 [acct.address, "latest"]), 16)
    gas_price = int(base_action._rpc(config.rpc_url, "eth_gasPrice", []), 16)
    tx = {
        "to": acct.address,
        "value": DUST,
        "data": data_hex,
        "gas": 60000,
        "gasPrice": gas_price,
        "nonce": nonce,
        "chainId": chain_id,
    }
    return acct.sign_transaction(tx)


def sovereign_mint(memory: Memory, config: Config, *,
                   owner: str | None = None) -> MintReceipt:
    """Commit the memory root onchain as a sovereign memory asset.

    Dry-run by default (no broadcast). With DEJAVU_DRY_RUN=0 it signs + broadcasts
    a dust Base tx whose `data` field carries the memory root hash — an immutable,
    owner-anchored record that the store existed at this fingerprint.

    The deletion gate becomes economic: delete the store, the onchain record
    points to a root that no longer resolves in the store — the asset is
    orphaned/destroyed. Memory isn't decoration; it's a committed asset.
    """
    r = memory_root(memory)
    ident = identity(memory)
    data_hex = "0x" + bytes.fromhex(r["root"]).hex()  # 32-byte root in calldata

    if config.dry_run:
        return MintReceipt(
            dry_run=True, root=r["root"], identity_id=ident["id"],
            owner=owner or "unbound-dry-run",
            details={"chain_id_hint": "8453 (Base)",
                     "data_hex_len": len(data_hex)},
        )

    acct = base_action._load_account(config)
    owner_addr = owner or acct.address
    signed = _commit_tx(config, data_hex)
    tx_hash = base_action._broadcast(config.rpc_url, signed)
    return MintReceipt(
        dry_run=False, root=r["root"], identity_id=ident["id"],
        owner=owner_addr,
        details={"from": acct.address, "value_wei": DUST,
                 "data_hex_len": len(data_hex)},
        tx_hash=tx_hash,
        explorer_url=BASE_EXPLORER.rstrip("/") + "/" + tx_hash,
    )


def asset_orphaned(memory: Memory, mint: MintReceipt) -> bool:
    """After a mint, does the store still resolve to the committed root?

    True = the committed asset is orphaned (store deleted/changed past the
    committed fingerprint). This is the economic deletion-gate proof.
    """
    return memory_root(memory)["root"] != mint.root


# ---------------------------------------------------------------------------
# (5) SELF-REFERENTIAL SOVEREIGN LOOP — memory that knows it owns itself
# ---------------------------------------------------------------------------

ANCHOR_KEY = "sovereign/anchor"


def anchor_self(memory: Memory, mint: MintReceipt) -> dict:
    """Write the onchain mint receipt BACK INTO the store (REFERENCE tier).

    This closes the sovereign loop. The memory doesn't just get anchored — it
    *remembers its own anchor*. Because REFERENCE is folded into the
    content-addressed root, the store's fingerprint now reflects the onchain
    transaction that committed it. A fresh box mounting the same store recalls
    "I was committed onchain at block/root R" as part of its own content.

    Deterministic, network-free, reversible (a re-mint simply updates it).
    """
    body = {
        "root": mint.root,
        "identity_id": mint.identity_id,
        "owner": mint.owner,
        "dry_run": mint.dry_run,
        "details": mint.details,
        "tx_hash": mint.tx_hash,
        "explorer_url": mint.explorer_url,
    }
    metadata = {"chain": "base", "network": "eip155:8453",
                "self": True, "layer": "L7"}
    memory.set_reference(ANCHOR_KEY, body, metadata=metadata)
    return {"anchored": True, "doc_key": ANCHOR_KEY, "body": body}


def resolve_anchor(memory: Memory) -> dict | None:
    """Read the memory's self-recorded onchain anchor (REFERENCE tier)."""
    ref = memory.get_reference(ANCHOR_KEY)
    if not ref:
        return None
    body = ref.get("body")
    if isinstance(body, str):
        body = json_loads_any(body)
    return {
        "root": body.get("root"),
        "tx_hash": body.get("tx_hash"),
        "owner": body.get("owner"),
        "identity_id": body.get("identity_id"),
        "explorer_url": body.get("explorer_url"),
        "dry_run": body.get("dry_run"),
    }


def is_self_anchored(memory: Memory, mint: MintReceipt | None = None) -> bool:
    """Is the store self-anchored? Optionally, does its anchor match `mint`?

    `mint is None`: true if ANY anchor is recorded.
    `mint given`: true only if the recorded anchor matches that exact mint
    (root + identity). This is the "the memory knows it owns THIS committed
    root" check — a fresh box that mounts the same store returns True; a wiped
    or divergent store returns False.
    """
    anchor = resolve_anchor(memory)
    if anchor is None:
        return False
    if mint is None:
        return True
    return (anchor.get("root") == mint.root
            and anchor.get("identity_id") == mint.identity_id)


# ---------------------------------------------------------------------------
# (4) QUERY ECONOMICS  — the store as a payable data layer
# ---------------------------------------------------------------------------

@dataclass
class QueryQuote:
    category: str
    name: str
    price_wei: int
    owner_only: bool
    details: dict[str, Any] = field(default_factory=dict)


def quote_query(memory: Memory, category: str, name: str, *,
                price_wei: int = 1_000_000_000) -> QueryQuote:
    """Price a read from the shared store.

    Anyone can read the owner's memory — for a price (settled via x402). The
    store is a queryable, payable data layer, not a private notebook. Honest
    note: real x402 settlement needs a funded USDC wallet (optional); the
    pricing/ledger mechanics here are real and tested.
    """
    return QueryQuote(category=category, name=name, price_wei=price_wei,
                      owner_only=False,
                      details={"note": "settles via x402 when USDC wallet funded"})


def ledger_balance(memory: Memory) -> dict:
    """Sum of query payments the store has earned (ledger in the HOT state tier)."""
    st = memory.get_state("sovereign/query-ledger")
    st = st.get("body") if isinstance(st, dict) else st
    if not st:
        return {"paid_queries": 0, "earned_wei": 0}
    return {"paid_queries": st.get("paid_queries", 0),
            "earned_wei": st.get("earned_wei", 0)}


def record_payment(memory: Memory, category: str, name: str,
                   price_wei: int) -> dict:
    """Record a paid query on the store's earnings ledger (HOT tier)."""
    cur = ledger_balance(memory)
    ledger = {"paid_queries": cur["paid_queries"] + 1,
              "earned_wei": cur["earned_wei"] + price_wei,
              "last_query": {"category": category, "name": name}}
    memory.set_state("sovereign/query-ledger", ledger)
    return ledger
