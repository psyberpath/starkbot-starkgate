# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fastapi",
#     "httpx",
#     "pydantic",
#     "uvicorn",
# ]
# ///
import os
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="StarkGate Universal x402 Paywall Proxy")

processed_txs = set()
# TODO: Hackathon demo compromise: using in-memory set() for anti-replay. Will migrate to SQLite for production persistence to survive service restarts.

class ProxyRequest(BaseModel):
    target_url: str
    from_address: str

@app.get("/rpc/status")
async def rpc_status():
    return {"success": True, "data": {"status": "ok"}}

@app.post("/rpc/proxy")
async def rpc_proxy(req: ProxyRequest):
    agent_wallet = os.getenv("AGENT_WALLET")
    if not agent_wallet:
        return {"success": False, "error": "AGENT_WALLET environment variable not set."}

    api_url = "https://api-sepolia.basescan.org/api"
    basescan_api_key = os.getenv("BASESCAN_API_KEY", "")
    
    params = {
        "module": "account",
        "action": "txlist",
        "address": req.from_address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 10,
        "sort": "desc"
    }
    if basescan_api_key:
        params["apikey"] = basescan_api_key

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(api_url, params=params)
            resp.raise_for_status()
            tx_data = resp.json()
    except Exception as e:
        return {"success": False, "error": f"Failed to fetch transactions from BaseScan: {str(e)}"}

    if tx_data.get("status") != "1" or not isinstance(tx_data.get("result"), list):
        return {"success": False, "error": "No valid payment found from this address."}

    transactions = tx_data["result"]
    valid_payment_found = False

    for tx in transactions:
        tx_hash = tx.get("hash")
        to_address = tx.get("to", "").lower()
        value = int(tx.get("value", 0))
        is_error = tx.get("isError")

        # 0.001 ETH = 1,000,000,000,000,000 wei
        if (
            to_address == agent_wallet.lower() and
            value >= 1_000_000_000_000_000 and
            is_error == "0"
        ):
            if tx_hash in processed_txs:
                continue
            
            processed_txs.add(tx_hash)
            valid_payment_found = True
            break
            
    if not valid_payment_found:
        return {"success": False, "error": "No valid payment found from this address."}

    # Execute proxy request
    try:
        async with httpx.AsyncClient() as client:
            target_resp = await client.get(req.target_url)
            target_resp.raise_for_status()
            try:
                data = target_resp.json()
            except ValueError:
                data = target_resp.text
                
            return {"success": True, "data": data}
            
    except Exception as e:
        return {"success": False, "error": f"Failed to fetch target URL: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9102)
