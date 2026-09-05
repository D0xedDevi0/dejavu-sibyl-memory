# Virtuals ACP — dejavu agent (registered 2026-08-17, renamed echo→dejavu)

## Status: ✅ REGISTERED + SIGNER ACTIVE + LIVE ACP JOB EXERCISED

The `dejavu` agent is a fully registered, signer-enabled Virtuals Protocol agent.
(Registered as `echo`, **renamed to `dejavu` on the platform 2026-08-17** via
`acp agent update --name dejavu` — same agent ID / wallet / signer / ACP_ONLY
policy preserved.)
This is the Virtuals ACP stack for the Sibyl Memory Hackathon (x1.25 multiplier,
paired with Base). Satisfies: "a registered or transacting agent."

## Agent details
- **Name:** dejavu
- **Logo:** https://d0xeddevi0.github.io/NEURAL_MESH/assets/dejavu-logo.png (→ acpcdn `bde38abd...webp`)
- **Agent ID:** `01a01184-784b-7989-9d10-526fcb708ebd`
- **EVM wallet (Base):** `0xef25e2144f7ca887a9dc59e732c9e23e6a5847bb`
- **Solana wallet:** `8oaYbfWCzFxqnrEN3yFGGcVwX6hKFBCQkkzEqRU4fjWa`
- **Email:** `echo_h9ge@agents.world`
- **Builder code:** `bc_6z9u9grp`
- **Role:** HYBRID · wallet provider: PRIVY
- **Signer:** active, policy `ACP_ONLY` (restricted — authorizes ACP transactions)
- **Signer ID:** `r3b15vepxkhqo14g7bwmk8sf`

## Critical: keyring backend fix (REQUIRED for all acp commands)
The ACP CLI stores auth tokens + signer keys in `cross-keychain`. On this headless
container the default `native-linux` (DBus Secret Service) backend returns
"not found" WITHOUT throwing, so the CLI's file-backend fallback never triggers
and every command fails with `NOT_AUTHENTICATED`.

**Fix:** force the file backend via env var on every invocation:
```bash
export TS_KEYRING_BACKEND=file
export ACP_CONFIG_DIR=/opt/data/.acp
export PATH="/opt/data/acp-cli/node_modules/.bin:$PATH"
```
(acp-cli installed locally at /opt/data/acp-cli — global install needs root.)

## Owner (human) wallet
- `0xf9050811da2811c50d8af213f543f5e9197ccab6` (the ACP auth owner / signer-approver)

## State files
- CLI config: `/opt/data/.acp/config.json` (ownerWallet only; tokens live in the file-backend keyring at `~/.local/share/keyring/secrets.json` encrypted with `~/.config/keyring/file.key`)
- Keyring file backend forced via `TS_KEYRING_BACKEND=file`

## Verify commands
```bash
acp agent list --json              # echo is registered
acp agent signer-policy --agent-id 01a01184-784b-7989-9d10-526fcb708ebd --json  # ACP_ONLY
acp wallet balance --json          # multi-chain balances
```

## Live ACP job exercised (2026-09-04) — job 76304, Base mainnet

Real onchain ACP v2 job fired through the dejavu agent's client wallet:

- **Job ID:** `76304` (v2 protocol, Base mainnet 8453)
- **Client (dejavu):** `0xef25E2144f7Ca887A9Dc59e732c9E23e6a5847BB`
- **Provider:** LUMI `0x4cdB0d2Fd8755a7c3924B025CD953d665D023c2B` (live: lastActive
  2026-09-05T00:26Z)
- **Offering:** `forecast_calibration` ($0.01, requiredFunds:false) — hired for a
  5-round calibration score
- **Requirement posted:** `{"offering":"forecast_calibration","limit":5}`
- **Verified onchain:** `acp job history --job-id 76304 --chain-id 8453` →
  status `open`, entries `job.created` (client/provider/evaluator) + the posted
  requirement. This is a real onchain job, not a stub.

This satisfies the Virtuals stack requirement as a **visibly exercised ACP job** —
the discipline gate in `docs/judge.md` §7 is now cleared.
