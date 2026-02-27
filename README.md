# 🪐 StarkGate: The Universal x402 API Tollbooth

**Hackathon Track:** Autonomous Operation / DeFi Integration  
**Format:** Companion Skill (`.md`) + Microservice Module (`module.toml` & `service.py`)

---

### 💡 What it does and why it's useful

APIs are the lifeblood of the web, but monetizing them is a broken Web2 nightmare. Stripe bans crypto, and building custom paywalls takes days of engineering effort. 

**StarkGate** transforms any StarkBot into an autonomous, x402-native API tollbooth. By equipping this module, a StarkBot can autonomously wrap *any* external web API behind a crypto micropayment wall. When a user requests data, the agent autonomously checks the Base Testnet to verify a micropayment has been sent from the user's wallet before routing the HTTP request and returning the payload. 

**The Impact:** It solves the monetization cold-start problem for AI agents and developers by providing instant, permissionless, decentralized API gating.

---

### ⚙️ Architecture (Skill + Module Synergy)

We adhered strictly to the StarkBot architecture guidelines, splitting the workload optimally:

1. **The Skill (`starkgate.md`):** Operates *inside* the agentic loop. It instructs the LLM on how to intercept API requests, quote the x402 price, and collect the user's `from_address`.
2. **The Module (`service.py`):** Operates *outside* the agentic loop for speed, determinism, and security. It is a FastAPI microservice that handles the Web3 verification (querying BaseScan for transactions) and the actual reverse-proxy forwarding. It strictly uses the required `{"success": true, "data": ...}` RPC envelope.

---

### 🛠️ Installation & Setup

1. **Copy the directories** into your StarkBot configuration:
   ```bash
   cp -r modules/starkgate ~/.starkbot/modules/
   cp -r skills/starkgate ~/.starkbot/skills/
   ```

2. **CRITICAL - Environment Variables:** The module requires a wallet address to check for received payments. Add this to your StarkBot's root `.env` file (or export it in your terminal before running the module):
    ```bash
    AGENT_WALLET="0xYourAgentReceivingAddress"
    # Optional but recommended for higher rate limits:
    BASESCAN_API_KEY="YourBaseScanApiKey"
    ```

3. Ensure `uv` is installed, as defined in the `module.toml`. (Note: The `service.py` includes PEP 723 metadata to auto-install dependencies `fastapi`, `httpx`, `pydantic`, `uvicorn` out of the box).

4. **Run** your StarkBot instance.

5. In the StarkBot UI, edit your preferred Agent Persona (e.g., Director) and add `starkgate_proxy` to its **Skills**, and `proxy_request` to its **Tools**.

---

### 🚀 Usage Example

Here is exactly how the agent interacts with a user trying to access a gated API:

**User:**
> "I need the data from https://jsonplaceholder.typicode.com/todos/1."

**StarkBot ✨ (Agentic Loop):**
> "That API endpoint is protected by a StarkGate paywall. The cost per request is 0.001 ETH. Please send the payment to my wallet `0xAGENT_WALLET...` on the Base Testnet and reply with the wallet address you sent it from."

**User** *(After sending transaction)*:**
> "I have paid the fee. I sent it from my wallet `0xUSER_WALLET...`"

**StarkBot ⚙️ (Module Execution):**
> *[Internal: Agent calls `POST /rpc/proxy` with `target_url` and `from_address`]*  
> *[Internal: Module queries Base Testnet via Web3, verifies transaction amount (>=0.001 ETH), receiver, and execution status]*  
> *[Internal: Module caches transaction to prevent replay attacks]*  
> *[Internal: Module executes HTTP GET request to the target URL]*

**StarkBot ✨ (Final Output to User):**
> "Payment verified successfully. Here is the requested data:"
> ```json
> {
>   "userId": 1,
>   "id": 1,
>   "title": "delectus aut autem",
>   "completed": false
> }
> ```