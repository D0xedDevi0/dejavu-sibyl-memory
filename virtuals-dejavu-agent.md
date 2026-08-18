# Virtuals ACP — dejavu agent (registered 2026-08-17, renamed echo→dejavu)

## Status: ✅ REGISTERED + SIGNER ACTIVE (transacting)

The `dejavu` agent is a fully registered, signer-enabled Virtuals Protocol agent.
(Registered as `echo`, **renamed to `dejavu` on the platform 2026-08-17** via
`acp agent update --name dejavu` — same agent ID / wallet / signer / ACP_ONLY
policy preserved.)
This is the Virtuals ACP stack for the Sibyl Memory Hackathon (x1.25 multiplier,
paired with Base). Satisfies: "a registered or transacting agent."

## Agent details
- **Name:** dejavu
- **Logo:** https://basednukem.github.io/NEURAL_MESH/assets/dejavu-logo.png (→ acpcdn `bde38abd...webp`)
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
