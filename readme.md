# ⚡ Flash Loan Arbitrage & Sniper Bot

A full-stack DeFi trading suite capable of **sniping new token launches** and executing **Flash Loan Arbitrage** between decentralized exchanges (Uniswap & SushiSwap).

This project includes a **Mainnet Fork Simulation Engine** that allows you to safely test arbitrage strategies by impersonating "Whales" and manipulating market prices locally before deploying capital.

## 🚀 Features

### 1. 🏹 Token Sniper

- **Mempool Monitoring:** Detects `PairCreated` events on Uniswap V2 instantly.
- **Honeypot Detection:** Simulates buy/sell transactions to ensure tokens are not scams.
- **Auto-Buy:** Executes buy transactions immediately upon liquidity addition.

### 2. ⚡ Flash Loan Arbitrage

- **Cross-Exchange Monitoring:** Tracks price differences between Uniswap and SushiSwap.
- **Flash Swaps:** Uses `UniswapV2Pair.swap` to borrow assets without collateral.
- **Profit Logic:** Borrows from the cheaper exchange (e.g., SushiSwap), sells on the expensive exchange (e.g., Uniswap), and repays the loan from profits.
- **Gas Optimized:** Smart contract calculates repayment math on-chain to prevent reverts.

### 3. 🧪 Simulation Engine

- **Ganache Mainnet Fork:** Clones the real Ethereum blockchain state to `localhost`.
- **Whale Impersonation:** Unlocks massive holder accounts (e.g., MakerDAO, Bridges) to manipulate prices.
- **Market Manipulation Script:** Programmatically buys millions in assets to force price gaps for testing.

### 4. 📊 Dashboard

- **Streamlit UI:** Live visualization of price spreads and bot balances.
- **Manual Execution:** Trigger Flash Loans with a single click.

---

## 🛠 Prerequisites

- **Python 3.10+**
- **Node.js & NPM** (For Ganache)
- **Alchemy API Key** (Free tier is sufficient)

### Install Ganache CLI

```bash
npm install -g ganache

```

### Install Python Dependencies

```bash
pip install -r requirements.txt

```

---

## ⚙️ Configuration

1. **Environment Variables:** Create a `.env` file (optional, or hardcode in scripts for testing):

```env
RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
PRIVATE_KEY=YOUR_WALLET_PRIVATE_KEY

```

2. **Target Whales (For Simulation):**

- **USDC Whale:** `0x46340b20830761efd32832A74d7169B29FEB9758` (Arbitrum Bridge)
- **MakerDAO PSM:** `0x0A59649758aa4d66E25f08Dd01dacb9202FB4700`

---

## 🏃 Quick Start (The "Golden Loop")

Follow this exact sequence to test the Arbitrage Bot end-to-end locally.

### 1. Start the Blockchain (Terminal 1)

Fork Ethereum Mainnet and unlock the rich Whale account.
_(Replace `YOUR_API_KEY` with your actual Alchemy key)_

```bash
ganache --fork https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY --unlock 0x46340b20830761efd32832A74d7169B29FEB9758 -p 8545

```

_Keep this terminal open._

### 2. Deploy the Bot (Terminal 2)

Compiles `ArbSniper.sol` and deploys it to your local fork.

```bash
python scripts/deploy_arb.py

```

> **Output:** `✅ ArbSniper Deployed at: 0x...`

### 3. Manipulate the Market (Terminal 2)

Runs the Whale script to buy **$10M WETH** on Uniswap, driving the price up to ~$9,000 while SushiSwap stays at ~$2,300.

```bash
python scripts/simulate_arb_opp.py

```

> **Output:** `✅ GAP CREATED: $7100.00 difference per ETH`

### 4. Execute Arbitrage (Terminal 2)

Triggers the Flash Loan: Borrow from Sushi -> Sell on Uniswap -> Repay Loan -> Keep Profit.

```bash
python scripts/manual_execute.py

```

> **Output:** `🎉 SUCCESS!` and `💰 NEW CONTRACT BALANCE: 180,000+ USDC`

---

## 📂 Project Structure

```
├── contracts/
│   └── ArbSniper.sol       # Solidity Smart Contract (Flash Swap Logic)
├── scripts/
│   ├── deploy_arb.py       # Deploys contract to Ganache
│   ├── simulate_arb_opp.py # The "Whale" script (Market Maker)
│   ├── manual_execute.py   # Triggers the Flash Loan transaction
│   ├── dashboard_arb.py    # Streamlit Dashboard source code
│   └── analyze_tx.py       # Forensics tool to debug transaction logs
├── arb_deployment.json     # Stores latest contract address
└── README.md

```

---

## 🧠 Smart Contract Logic (`ArbSniper.sol`)

The bot uses a **Flash Swap** mechanism rather than a standard Flash Loan to bypass Reentrancy Locks.

1. **Borrow:** Call `swap()` on the **Cheap Exchange** (SushiSwap). Ask for WETH but send 0 payment.
2. **Callback:** SushiSwap sends WETH and calls `uniswapV2Call` on our contract.
3. **Arbitrage:** Contract sells the WETH on the **Expensive Exchange** (Uniswap) for USDC.
4. **Math:** Calculates exactly how much USDC is required to repay the SushiSwap loan (`k = x * y` formula).
5. **Repay:** Sends the required USDC back to SushiSwap.
6. **Profit:** The remaining USDC is kept in the contract.

---

## ⚠️ Disclaimer

**For Educational Purposes Only.**
Deploying this to Mainnet without modification puts your funds at risk.

- **MEV Bots:** Public arbitrage transactions are easily front-run by MEV bots on Mainnet.
- **Gas Fees:** Ensure potential profit > gas costs.
- **Honeypots:** The sniper module simulation is not 100% foolproof against advanced scam tokens.
