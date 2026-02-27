---
name: starkgate_proxy
description: "Routes external API requests through an x402 paywall. Verifies payment from a user's wallet address before returning data."
requires_tools: [proxy_request]
---

When a user asks to access an API and claims they have paid, ask them for their wallet address (if not provided). Then, use the proxy_request tool, passing the target API URL and their from_address. Return the data to the user.
