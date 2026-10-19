# Crypto Automation Bots — Knowledge Bank (2025-2026)

Compiled from Flashbots research, EigenPhi, DeFi Llama, GitHub trending, and domain expertise. Last updated: 2026-07-25 (added AI Trading Agents, Telegram Bot Services, Hyperliquid Bots categories; expanded Solana + Polymarket repos).

## Quick Reference Table

| Bot Type | Monthly ROI | Min Capital | Skill | Competition | Best Chains/Platforms |
|----------|------------|-------------|-------|-------------|----------------------|
| MEV (ETH L1) | 2-15% | $5K-50K | ⭐⭐⭐⭐⭐ | 🔴 Extreme | Ethereum (BuilderNet) |
| MEV (L2s) | 5-25% | $1K-10K | ⭐⭐⭐⭐ | 🟠 High | Base, Arbitrum, Solana (Jito) |
| Solana Sniper/Copy | $1K-50K | $500 | ⭐⭐⭐⭐ | 🟡 High | Pump.fun, Raydium, Jito bundles |
| AI Trading Agent | TBD (experimental) | $0-5K | ⭐⭐⭐⭐ | 🟢 Low | Multi-platform (all chains) |
| Telegram Bot Service | $15K-$500K/mo | $5K-50K | ⭐⭐⭐⭐⭐ | 🔴 Extreme | Solana (Telegram native) |
| Polymarket Bot | 5-20% | $1K-10K | ⭐⭐⭐ | 🟡 Moderate | Polymarket CLOB API |
| Hyperliquid Copy Bot | 3-15% | $1K-10K | ⭐⭐⭐ | 🟢 Low | Hyperliquid DEX |
| DEX-DEX Arb | 3-10% | $2K-20K | ⭐⭐⭐⭐ | 🟠 High | Uniswap v3, Curve, Raydium |
| CEX-DEX Arb | 1-5% | $10K-100K | ⭐⭐⭐⭐ | 🟡 Medium | Binance↔ETH DEXes |
| Cross-Chain Arb | 5-20% | $5K-50K | ⭐⭐⭐⭐⭐ | 🟢 Moderate | ETH↔L2s (LayerZero, Wormhole) |
| Grid Trading | 2-8% | $500-10K | ⭐⭐ | 🟢 Low | Pionex, Binance built-in |
| DCA Bot | Market avg | $100-5K | ⭐ | 🟢 Low | 3Commas, Shrimpy |
| Momentum | -20% to +30% | $1K-50K | ⭐⭐⭐ | 🟡 Medium | Custom Python (ccxt+TA-Lib) |
| Yield Automation | 3-15% APR | $1K-50K | ⭐⭐⭐-⭐⭐⭐⭐ | 🟡 Medium | EigenLayer, Pendle, Aave, Convex |

## Solana Sniper & Copy Trading Bots (NEW — 2026-07)

### Overview
Pump.fun ecosystem explosion created a new category. Copy trading follows whale wallets; sniper bots buy tokens within milliseconds of launch.

### Top Open-Source Repos (by stars)
- AV1080p/Solana-Sniper-Bot ⭐1,951 — Top Solana sniper (Rust, updated 2026-07)
- x89/Solana-Arbitrage-Bot ⭐1,177 — Cross-DEX arbitrage (Rust)
- chainstacklabs/pumpfun-bonkfun-bot ⭐971 — Pump.fun/letsbonk.fun sniper, Python, no 3rd-party APIs (updated 2026-07-24)
- WSOL12/Solana-Arbitrage-Bot ⭐511 — Pump.fun/Meteora/Raydium/Orca arbitrage using Jito bundling (TypeScript)
- coffellas-cto/Solana-Copy-Trading-Bot ⭐410 — Copy trading with Shred stream + MEV-aware (Rust, updated 2026-07-19)
- ChainBuff/open-sol-bot ⭐401 — Open-source Solana bot, copy + auto trading (Chinese docs)
- adams322111233221/solana-mev-bot ⭐389 — Solana MEV bot (Rust)
- 0xfnzero/sol-trade-sdk ⭐327 — Rust SDK for low-latency DEX trading (PumpFun, PumpSwap, Raydium, Meteora, Jito, SWQoS)
- ChangeYourself0613/Solana-Arbitrage-Bot ⭐292 — Cross-DEX arbitrage with Anchor framework (Rust)
- web3batman/Solana_Memecoin_Sniper_Bot ⭐274 — Proven in competition with modern snipers (TypeScript)
- cutupdev/Solana-Copytrading-bot ⭐277 — Copy trade target wallets (Rust)
- henrytirla/Solana-Trading-Bot ⭐286 — Buy/sell SPL tokens on Raydium + Pump.fun via Solana-Py + Jito SDK (Python)
- TreeCityWes/Pump-Fun-Trading-Bot-Solana ⭐211 — Pump.fun sniper (JavaScript, updated 2026-07-23)
- cutupdev/Solana-Raydium-Sniper-Bot ⭐204 — LaunchLab/AMM/CLMM/CPMM snipe (Rust)
- hexnome/pumpfun-raydium-cli-tools ⭐175 — Bundler + volume bot + sniper combo (JavaScript)
- cutupdev/Solana-Pumpfun-Sniper-Bot ⭐192 — Pump.fun sniper (Rust)
- hanshaze/solana-sniper-copy-mev-trading-bot ⭐167 — Multi-strategy: sniper, copy, MEV, sandwich, volume

### Key Technologies
- **Jito bundles** — Priority transaction submission to Solana validators
- **Shred stream** — gRPC-based real-time transaction feed (faster than standard RPC)
- **Geyser gRPC** — Validator plugin for real-time account/transaction streaming
- **Jito Block Engine** — Bundle submission for MEV extraction

### Stack
- Rust (preferred for latency) or TypeScript
- Solana web3.js / @solana/web3.js
- Jito SDK (bundle submission)
- gRPC clients for Shred/Geyser streams

### Reality Check
- High variance: $0 on bad days, $5K+ on hyped launches
- Pump.fun memecoins are 99% rugs — sniper profits come from being FIRST in/out
- Copy trading requires identifying profitable wallets (on-chain analytics)
- Competition increasing rapidly as tools become more accessible

## AI Trading Agents (NEW — 2026-07)

### Overview
The fastest-growing category in 2025-2026. AI-powered autonomous trading agents that interpret natural language strategies, analyze markets, and execute trades across multiple platforms simultaneously. HKUDS/AI-Trader hit 21K stars in 9 months — unprecedented growth for a trading repo.

### Top Open-Source Repos (by stars)
- HKUDS/AI-Trader ⭐21,023 — "100% Fully-Automated Agent-Native Trading" (Python, created 2025-10)
- NoFxAiOS/nofx ⭐12,633 — AI trading terminal for US stocks, commodities, forex, crypto
- OpenByteInc/QuantDinger ⭐9,972 — AI quant platform for crypto/stocks/forex with backtesting + live trading
- TraderAlice/OpenAlice ⭐6,234 — "Your one-person Wall Street" AI trading agent
- The-Swarm-Corporation/AutoHedge ⭐4,010 — Swarm intelligence + AI agents for autonomous hedge fund (created 2024-12)
- Polymarket/agents ⭐3,751 — Official Polymarket AI Agents for autonomous trading (created 2024-07)
- ygwyg/MAHORAGA ⭐856 — Autonomous agent with social sentiment analysis (TypeScript)
- alsk1992/CloddsBot ⭐545 — AI agent across 1000+ markets (Polymarket, Kalshi, Binance, Hyperliquid)
- moss-site/moss-trade-bot-skills ⭐381 — LLM-powered agents: natural language → 5-pillar strategy
- Senpi-ai/senpi-skills ⭐108 — 80+ AI agent strategy templates for Hyperliquid
- chain-ml/alphaswarm ⭐96 — LLM-powered agents interpreting natural language trading strategies

### Key Technologies
- LLM-based strategy interpretation (GPT-4, Claude)
- Multi-agent swarm architectures
- Natural language → executable strategy pipelines
- Cross-platform execution (CEX + DEX + prediction markets)

### Stack
- Python + LangChain/CrewAI for agent orchestration
- OpenAI/Anthropic APIs for strategy reasoning
- ccxt for exchange connectivity
- Custom market data pipelines

### Reality Check
- Most are research projects, not proven profitable
- LLM latency (1-3s) is too slow for high-frequency strategies
- Backtesting results ≠ live performance (survivorship bias)
- Agent-autonomous trading is the direction but still early
- Commercial AI trading bots charge $99-$499/month SaaS subscriptions

## Telegram Trading Bot Services (NEW — 2026-07)

### Overview
The most profitable bot business model in crypto 2024-2026. Telegram-native trading bots that charge 0.5-1% per trade. At scale ($10M+ daily volume), this generates $50K-$100K/day in fees.

### Major Commercial Players (not open-source)
- **BonkBot** — Solana trading via Telegram, early Pump.fun integration
- **Trojan** (previously Unibot) — Solana trading bot, reportedly **$50M+ in fees** during 2024
- **Photon** — Web + Telegram Solana trading interface
- **GMGN** — Solana sniper + trading bot with Telegram interface
- **Maestro Bot** — Multi-chain Telegram trading bot, millions in fees
- **Banana Gun** — Telegram sniper, token $BANANA hit $200M+ market cap

### Revenue Model
- 0.5-1% fee per trade executed through the bot
- Token launches (native tokens for the bot platforms)
- Premium tiers with lower fees or advanced features
- Referral programs (share of referred user fees)

### Earnings Benchmarks (from on-chain data + public reports)
- Top bots: $50K-$500K/day in fee revenue during peak memecoin seasons
- Mid-tier bots: $5K-$50K/day
- New entrants: $500-$5K/day if they gain traction

### Open-Source Telegram Bots for Building Similar Services
- DracoR22/handi-cat_wallet-tracker ⭐204 — Solana wallet tracker Telegram bot
- fabston/TradingView-Webhook-Bot ⭐1,818 — TradingView alerts → Telegram/Discord/Slack

### Reality Check
- Market is consolidating — top 5 bots capture 80%+ of volume
- Requires significant marketing/community building
- Smart contract security is critical (hacks have occurred)
- Regulatory risk increasing (some bots have faced legal action)

## Hyperliquid Bots (NEW — 2026-07)

### Overview
Hyperliquid is the hottest perps DEX (no KYC, low fees, fast execution). Bot ecosystem emerging rapidly in 2025-2026.

### Top Open-Source Repos
- enarjord/passivbot ⭐2,039 — Multi-exchange (Bybit, Bitget, OKX, Binance, Hyperliquid)
- MarilynClarke/Hyperliquid-Copy-Trading-Bot ⭐324 — Copy trading on Hyperliquid
- origamidottech/hyperliquid-trading-bot ⭐136 — Copy trading bot
- Senpi-ai/senpi-skills ⭐108 — 80+ AI strategy templates
- chainstacklabs/hyperliquid-trading-bot ⭐77 — Chainstack's official bot
- xlev-v/Hyperliquid-Trading-Bot ⭐79 — 3 independent strategies, production-grade TypeScript

### Key Technologies
- Hyperliquid WebSocket API for real-time data
- HIP-3 (Hyperliquid Improvement Proposal) for token standards
- Copy trading via wallet tracking + order mirroring

### Reality Check
- Still less competition than Solana bot ecosystem
- Passivbot author accepts donations + sells config optimizations
- Copy trading is the most accessible entry point

## Polymarket Trading Bots (NEW — 2026-07)

### Overview
Prediction market bots for Polymarket (elections, sports, crypto prices, world events). Two strategies: market making (provide liquidity) and ML prediction (bet on outcomes).

### Top Open-Source Repos (by stars)
- warproxxx/poly-maker ⭐1,419 — Automated market making on Polymarket
- hubert20/polymarket-NO-farming-trading-bot ⭐570 — "No" farming bot
- aulekator/Polymarket-BTC-15-Minute-Trading-Bot ⭐552 — Production-grade 7-phase algo for 15-min BTC markets
- alsk1992/CloddsBot ⭐545 — AI trading agent across 1000+ markets (Polymarket, Kalshi, Binance, Hyperliquid)
- suislanchez/polymarket-kalshi-weather-bot ⭐535 — Weather temperature arbitrage across Kalshi + Polymarket (Python)
- dev-polymarket/clob-client-v2 ⭐563 — Official Polymarket CLOB client
- casatrick/polymarket-arbitrage-bot-python ⭐450 — 5 strategies with merge/redeem (Python)
- sterlingcrispin/nothing-ever-happens ⭐978 — Meme bot that buys "No" on all non-sports markets
- radioman/polymarket-arbitrage-trading-bot ⭐485 — BTC/ETH 5-min prediction markets (C++)
- HarrierOnChain/Prediction-Markets-Trading-Bot-Toolkits ⭐367 — Production-grade Rust, 10 strategies for Polymarket/Kalshi/Limitless
- frecodecasti/polymarket-weather-trading-bot ⭐463 — Weather trading bot (TypeScript)

### Key Technologies
- **Polymarket CLOB API** — Central Limit Order Book for direct order placement
- **Market Making** — Place orders on both sides, earn spread
- **ML Prediction** — Train models on event data, place directional bets
- **Multi-market scanning** — Monitor all active markets for arbitrage/discrepancies

### Stack
- Python + Polymarket CLOB client
- ML frameworks (scikit-learn, PyTorch) for prediction
- FastAPI for bot management

### Reality Check
- Market making profits depend on spread capture vs adverse selection
- ML prediction edge degrades as more participants enter
- Polymarket has geographic restrictions (US users face limitations)
- Still an emerging market with less competition than crypto trading

## MEV Bots

### Strategies
- **Sandwich attacks:** Front-run + back-run user trades. Increasingly blocked by protected RPCs (Flashbots Protect, MEV-Share).
- **Liquidation bots:** Liquidate undercollateralized DeFi positions. Lower risk, consistent.
- **Backrunning/Arbitrage:** Profit from price discrepancies after large trades. Least controversial.
- **JIT liquidity:** Add & remove liquidity in same block to capture fees on Uniswap v3.
- **Cross-domain MEV:** Exploit across L1/L2 or between L2s. Highest complexity, emerging opportunity.

### Key Infrastructure
- **Flashbots BuilderNet** (Dec 2024): Decentralized block building on Ethereum. Centralized builders deprecated.
- **Jito Labs** (Solana): MEV auction system on Solana. Lower barrier to entry than ETH.
- **MEV-Share:** Users get refunds from MEV extracted on their transactions.

### Reality Check
- ETH mainnet dominated by PhD-level teams with $10M+ capital
- L2s (Base, Arbitrum) still have opportunities, especially cross-domain MEV
- Most beginner MEV bots on ETH mainnet lose money after gas costs

### Top Open-Source Repos
- paradigmxyz/artemis ⭐2,951 — MEV framework (Rust)
- jito-labs/mev-bot ⭐1,196 — Solana MEV bot
- fuzzland/sui-mev ⭐775 — Sui blockchain MEV
- solidquant/mev-templates ⭐576 — MEV templates (Python/JS/Rust)
- flashbots/simple-arbitrage ⭐2,111 — Example arbitrage bot
- MIgHTy-alIeN/MEV-Arbitrage-Bot ⭐1,441 — Smart contract + automation script

## Arbitrage

### DEX-DEX
- Flash loans are key enabler (no upfront capital, only gas + fee)
- Uniswap v3 concentrated liquidity creates more opportunities but more complexity
- Triangular arbitrage (A→B→C→A) still profitable on chains with many DEXes

### CEX-DEX
- Requires capital on both CEX and on-chain (counterparty risk)
- CEX withdrawal delays can eat profits
- Binance API rate limits are bottleneck

### Cross-Chain (most promising for new entrants)
- Bridge risk is main concern (bridge hacks remain common)
- LayerZero, Wormhole, Axelar for cross-chain messaging
- Stargate, Across Protocol for cross-chain swaps
- Execution latency is key challenge (bridges take seconds to minutes)

## Trading Bots

### Grid Trading (most accessible)
- Works best on BTC, ETH large-cap pairs with high volume
- Risk: trending markets destroy grid bots
- Spot grid safer than futures grid
- Pionex offers free built-in grid bots

### Momentum/Trend
- Works excellently in trending markets, poorly in choppy markets
- Custom bots with unique signal combinations outperform generic ones
- Backtesting essential but overfitting is #1 pitfall
- Python + ccxt is standard stack

## Yield Farming Automation

### Current Opportunities (2025-2026)
- **EigenLayer Restaking:** Restake ETH/LSTs for additional yield across AVSs
- **Pendle Finance:** Yield tokenization (PT=fixed, YT=leveraged)
- **Morpho/Aave V3:** Automated lending/borrowing optimization
- **Uniswap V3 LP management:** Automated rebalancing (Arrakis, Gamma Strategies)

## Essential Tool Stack

| Category | Tools |
|----------|-------|
| Node access | Alchemy, QuickNode, Infura |
| DEX data | The Graph, Dune Analytics, DeFi Llama |
| MEV monitoring | EigenPhi, Flashbots Explorer, MEV Blocker |
| Trading framework | ccxt (Python/JS), Hummingbot, Jesse |
| Backtesting | Backtrader, VectorBT, Jesse Trade |
| Smart contracts | Foundry (Rust), Hardhat (JS) |
| Execution | Flashbots Protect, Jito (Solana) |

## Infrastructure Costs

| Component | Monthly Cost |
|-----------|-------------|
| VPS (near node) | $20-100 |
| RPC provider | $50-200 |
| Gas (L2s) | $10-100 |
| Monitoring | $0-20 |
| **Total** | **$80-420** |

## Critical Warnings

1. Most bots lose money — start small
2. Gas costs kill many strategies — always factor in fees
3. Smart contract risk is real — flash loan bugs can drain funds
4. MEV on ETH mainnet is an arms race against $10M+ teams
5. "MEV bot tutorials" on YouTube are often **scams** that deploy contracts stealing your funds
6. Regulatory gray area — sandwich attacks face increasing scrutiny
7. Overfitting is #1 killer of trading strategies — backtest extensively

## Phased Learning Path

1. **Month 1-2:** Grid bot (Pionex) + stablecoin yield on Aave — $500-5K — learn ccxt + Python
2. **Month 3-6:** Custom DEX-DEX arb on Base/Arbitrum with flash loans — testnet→mainnet small capital
3. **Month 6-12:** Cross-chain arb + yield automation + LP management
4. **Year 2+:** Full MEV searcher on BuilderNet, CEX-DEX arb, custom ML momentum

## Key Sources
- Flashbots: flashbots.net / writings.flashbots.net
- EigenPhi: eigenphi.io
- Jito: jito.network
- Dune: dune.com
- Foundry: book.getfoundry.sh
- Pump.fun ecosystem: pump.fun, letsbonk.fun
