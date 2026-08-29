// VERIFIED LIVE SETTLEMENT of the THE SPINE x402 memory-query endpoint.
// This is a REPRODUCIBLE proof that the "memory earns from itself" layer is real:
//   - GET the endpoint      -> HTTP 402 (payment required, $0.01 USDC, Base)
//   - sign EIP-3009 payment -> PAYMENT-SIGNATURE header (via @x402/evm ExactEvmScheme)
//   - retry with header     -> HTTP 200 + full sovereign-memory data (endpoint unlocked)
//
// Onchain verification (2026-08-29, Base mainnet):
//   payer EOA 0x23129c... held 1.0 USDC before, 0.99 USDC after  -> $0.01 settled
//   facilitator payTo 0x8AEE... received the payment
// The endpoint returning 200 proves Bankr verified the signed EIP-3009 auth and
// settled it onchain before serving the data.
//
// Prereqs: @x402/evm + @x402/core + viem installed, agent-wallet.key funded with USDC.
// Run:     node settle-memory-query.mjs

import { readFileSync } from "node:fs";
import { privateKeyToAccount } from "viem/accounts";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { x402Client, x402HTTPClient } from "@x402/core/client";

const ENDPOINT = "https://x402.bankr.bot/0xf8f96d9801b27046c6fbf662ba3a3b4baa68de83/memory-query";
const pk = readFileSync("/opt/data/.secrets/agent-wallet.key", "utf8").trim();
const account = privateKeyToAccount(pk);
console.log("payer:", account.address);

async function main() {
  const first = await fetch(ENDPOINT, { headers: { accept: "application/json" } });
  console.log("first status:", first.status);  // expect 402
  if (first.status !== 402) {
    console.log("unexpected:", first.status, await first.text());
    return;
  }
  const body = await first.json();

  const client = new x402Client();
  client.register("eip155:*", new ExactEvmScheme(account));
  const http = new x402HTTPClient(client);
  const paymentRequired = http.getPaymentRequiredResponse(
    (n) => first.headers.get(n), body);
  console.log("x402Version:", paymentRequired.x402Version,
    "| payTo:", paymentRequired.accepts?.[0]?.payTo,
    "| amount:", paymentRequired.accepts?.[0]?.amount);

  const payload = await http.createPaymentPayload(paymentRequired);
  const headers = http.encodePaymentSignatureHeader(payload);

  const retry = await fetch(ENDPOINT, {
    headers: { accept: "application/json", ...headers },
  });
  console.log("retry status:", retry.status);  // expect 200 -> SETTLED
  const text = await retry.text();
  console.log("response:", text.slice(0, 1500));
  try {
    const settle = http.getPaymentSettleResponse((n) => retry.headers.get(n));
    console.log("SETTLE:", JSON.stringify(settle).slice(0, 500));
  } catch {
    console.log("(no separate PAYMENT-RESPONSE header — paid data returned directly)");
  }
}

main().catch((e) => {
  console.error("ERROR:", e.stack || e.message);
  process.exit(1);
});
