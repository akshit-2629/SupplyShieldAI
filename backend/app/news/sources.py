"""
News Sources Configuration — Phase 3: News Intelligence Agent

Defines:
  • RSS feed URLs for supply-chain-relevant news sources
  • SEVERITY_KEYWORDS: weighted keyword tiers for severity scoring
  • EVENT_TYPE_KEYWORDS: category → keywords for event classification
  • INDUSTRY_KEYWORDS: 9 industry categories → detection keywords
  • COUNTRY_KEYWORDS: country name → ISO-3166 alpha-2 code
  • TAVILY_SEARCH_QUERIES: targeted search queries for Tavily API
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


# ─────────────────────────────────────────────────────────────────────────────
# RSS Source definitions
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class NewsSource:
    name: str
    rss_url: str
    base_url: str
    credibility_score: float   # 1–10; used in severity weighting
    category: str


SUPPLY_CHAIN_RSS_SOURCES: List[NewsSource] = [
    # ── Tier 1: Global wire services ─────────────────────────────────────────
    NewsSource(
        name="Reuters Business",
        rss_url="https://feeds.reuters.com/reuters/businessNews",
        base_url="https://reuters.com",
        credibility_score=10.0,
        category="business",
    ),
    NewsSource(
        name="Reuters World",
        rss_url="https://feeds.reuters.com/reuters/worldNews",
        base_url="https://reuters.com",
        credibility_score=10.0,
        category="world",
    ),
    # ── Tier 2: Major broadcast ───────────────────────────────────────────────
    NewsSource(
        name="BBC Business",
        rss_url="http://feeds.bbci.co.uk/news/business/rss.xml",
        base_url="https://bbc.com",
        credibility_score=9.0,
        category="business",
    ),
    NewsSource(
        name="BBC World",
        rss_url="http://feeds.bbci.co.uk/news/world/rss.xml",
        base_url="https://bbc.com",
        credibility_score=9.0,
        category="world",
    ),
    # ── Tier 3: Google News targeted queries ──────────────────────────────────
    NewsSource(
        name="Google News – Supply Chain",
        rss_url="https://news.google.com/rss/search?q=supply+chain+disruption&hl=en-US&gl=US&ceid=US:en",
        base_url="https://news.google.com",
        credibility_score=7.0,
        category="supply_chain",
    ),
    NewsSource(
        name="Google News – Port Disruption",
        rss_url="https://news.google.com/rss/search?q=port+disruption+shipping+delay&hl=en-US&gl=US&ceid=US:en",
        base_url="https://news.google.com",
        credibility_score=7.0,
        category="logistics",
    ),
    NewsSource(
        name="Google News – Trade & Tariffs",
        rss_url="https://news.google.com/rss/search?q=trade+war+tariff+sanctions+supply&hl=en-US&gl=US&ceid=US:en",
        base_url="https://news.google.com",
        credibility_score=7.0,
        category="geopolitical",
    ),
    NewsSource(
        name="Google News – Semiconductor",
        rss_url="https://news.google.com/rss/search?q=semiconductor+chip+shortage+supply+chain&hl=en-US&gl=US&ceid=US:en",
        base_url="https://news.google.com",
        credibility_score=7.0,
        category="semiconductor",
    ),
    NewsSource(
        name="Google News – Manufacturing",
        rss_url="https://news.google.com/rss/search?q=factory+shutdown+manufacturing+disruption&hl=en-US&gl=US&ceid=US:en",
        base_url="https://news.google.com",
        credibility_score=7.0,
        category="manufacturing",
    ),
    NewsSource(
        name="Google News – Commodities",
        rss_url="https://news.google.com/rss/search?q=commodity+raw+material+shortage+supply&hl=en-US&gl=US&ceid=US:en",
        base_url="https://news.google.com",
        credibility_score=7.0,
        category="commodities",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Tavily targeted search queries
# ─────────────────────────────────────────────────────────────────────────────

TAVILY_SEARCH_QUERIES: List[str] = [
    "supply chain disruption 2024",
    "port congestion shipping delay containers",
    "semiconductor chip shortage impact",
    "factory shutdown manufacturing halt",
    "trade sanctions embargo supply chain",
    "natural disaster supply chain disruption",
    "labor strike factory workers supply",
    "commodity shortage raw material supply chain",
]


# ─────────────────────────────────────────────────────────────────────────────
# Severity keyword tiers — used in weighted scoring
# ─────────────────────────────────────────────────────────────────────────────

SEVERITY_KEYWORDS: Dict[str, Dict] = {
    "CRITICAL": {
        "score": 10,
        "keywords": [
            "war", "invasion", "sanctions", "collapse", "shutdown",
            "force majeure", "ban", "blockade", "embargo", "catastrophe",
            "crisis", "emergency", "halt", "seized", "explosion",
            "nuclear", "conflict", "attack", "destroyed", "devastating",
        ],
    },
    "HIGH": {
        "score": 7,
        "keywords": [
            "disruption", "shortage", "strike", "disaster", "earthquake",
            "flood", "fire", "typhoon", "hurricane", "tsunami", "wildfire",
            "protest", "walkout", "riot", "accident", "incident", "failure",
            "outage", "closure", "suspended", "shutdown", "critical",
        ],
    },
    "MEDIUM": {
        "score": 4,
        "keywords": [
            "delay", "slowdown", "congestion", "increase", "risk",
            "concern", "volatility", "uncertainty", "challenge", "pressure",
            "bottleneck", "constraint", "disrupted", "affected", "warning",
            "shortage", "shortage", "elevated", "tension",
        ],
    },
    "LOW": {
        "score": 2,
        "keywords": [
            "monitoring", "potential", "possible", "slight", "minor",
            "caution", "watch", "attention", "modest", "limited", "may",
            "could", "expected", "anticipated", "planning",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Event type classification keywords
# ─────────────────────────────────────────────────────────────────────────────

EVENT_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "GEOPOLITICAL": [
        "war", "sanctions", "tariff", "trade", "embargo", "diplomatic",
        "government", "military", "invasion", "conflict", "treaty", "ban",
        "geopolitical", "tension", "espionage", "legislation",
    ],
    "NATURAL_DISASTER": [
        "earthquake", "flood", "hurricane", "typhoon", "tsunami", "wildfire",
        "storm", "cyclone", "drought", "fire", "volcano", "landslide",
        "blizzard", "heatwave", "tornado", "freezing",
    ],
    "LABOR": [
        "strike", "protest", "walkout", "union", "workers", "employees",
        "labor", "labour", "dispute", "lockout", "demonstration",
        "picket", "bargaining", "wage", "lay off", "layoff",
    ],
    "REGULATORY": [
        "regulation", "compliance", "law", "legislation", "fine", "penalty",
        "ban", "restriction", "tariff", "quota", "standard", "audit",
        "export control", "import ban", "inspection", "recall",
    ],
    "LOGISTICS": [
        "port", "shipping", "cargo", "container", "vessel", "freight",
        "congestion", "delay", "transit", "customs", "warehouse", "transport",
        "intermodal", "backlog", "queue", "throughput",
    ],
    "ECONOMIC": [
        "bankruptcy", "inflation", "recession", "demand", "supply",
        "price", "cost", "currency", "exchange", "financial", "credit",
        "insolvency", "debt", "liquidity", "market",
    ],
    "PANDEMIC": [
        "covid", "pandemic", "virus", "lockdown", "quarantine", "outbreak",
        "epidemic", "health", "disease", "infection", "public health",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Industry detection keywords (9 categories)
# ─────────────────────────────────────────────────────────────────────────────

INDUSTRY_KEYWORDS: Dict[str, List[str]] = {
    "semiconductor": [
        "chip", "semiconductor", "wafer", "fab", "TSMC", "Intel", "Samsung",
        "Nvidia", "AMD", "GPU", "CPU", "microprocessor", "foundry", "silicon",
        "memory", "DRAM", "NAND", "integrated circuit",
    ],
    "automotive": [
        "car", "vehicle", "automotive", "Ford", "Toyota", "GM", "Tesla",
        "EV", "electric vehicle", "auto", "assembly", "Volkswagen", "BMW",
        "Honda", "Hyundai", "OEM", "tier supplier",
    ],
    "pharmaceutical": [
        "pharma", "drug", "medicine", "API", "generic", "FDA", "clinical",
        "vaccine", "healthcare", "biotech", "hospital", "medical device",
        "biologics", "active pharmaceutical ingredient",
    ],
    "energy": [
        "oil", "gas", "energy", "LNG", "petroleum", "OPEC", "fuel", "pipeline",
        "renewable", "solar", "wind", "coal", "electricity", "power",
        "refinery", "crude", "barrel",
    ],
    "shipping_logistics": [
        "port", "container", "shipping", "cargo", "freight", "vessel",
        "logistics", "warehouse", "supply chain", "DHL", "FedEx", "UPS",
        "Maersk", "CMA CGM", "MSC", "Ever Given",
    ],
    "agriculture": [
        "grain", "wheat", "crop", "harvest", "food", "corn", "soybean",
        "rice", "agriculture", "farming", "cattle", "livestock", "feed",
        "fertilizer", "drought", "harvest",
    ],
    "metals_mining": [
        "steel", "aluminum", "copper", "lithium", "cobalt", "nickel",
        "iron ore", "mining", "mineral", "metal", "rare earth",
        "manganese", "chromium", "bauxite",
    ],
    "technology": [
        "software", "cloud", "data center", "AI", "technology", "tech",
        "server", "network", "cyber", "digital", "computing", "IT",
        "telecommunications", "5G", "infrastructure",
    ],
    "retail_consumer": [
        "retail", "consumer", "store", "shopping", "e-commerce", "inventory",
        "product", "goods", "merchandise", "brand", "amazon", "walmart",
        "restocking", "out of stock",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Country name → ISO 3166-1 alpha-2 code
# ─────────────────────────────────────────────────────────────────────────────

COUNTRY_KEYWORDS: Dict[str, str] = {
    "China": "CN", "Chinese": "CN", "Beijing": "CN", "Shanghai": "CN",
    "Taiwan": "TW", "Taipei": "TW",
    "Japan": "JP", "Tokyo": "JP",
    "South Korea": "KR", "Korea": "KR", "Seoul": "KR",
    "United States": "US", "USA": "US", "America": "US", "Washington": "US",
    "Germany": "DE", "Berlin": "DE", "Frankfurt": "DE",
    "France": "FR", "Paris": "FR",
    "United Kingdom": "GB", "UK": "GB", "Britain": "GB", "England": "GB",
    "India": "IN", "New Delhi": "IN", "Mumbai": "IN",
    "Vietnam": "VN", "Ho Chi Minh": "VN", "Hanoi": "VN",
    "Thailand": "TH", "Bangkok": "TH",
    "Malaysia": "MY", "Kuala Lumpur": "MY",
    "Indonesia": "ID", "Jakarta": "ID",
    "Philippines": "PH", "Manila": "PH",
    "Singapore": "SG",
    "Mexico": "MX", "Mexico City": "MX",
    "Brazil": "BR", "São Paulo": "BR",
    "Canada": "CA", "Ottawa": "CA", "Toronto": "CA",
    "Russia": "RU", "Moscow": "RU",
    "Ukraine": "UA", "Kyiv": "UA", "Kiev": "UA",
    "Saudi Arabia": "SA", "Riyadh": "SA",
    "UAE": "AE", "Dubai": "AE", "Abu Dhabi": "AE",
    "Iran": "IR", "Tehran": "IR",
    "Netherlands": "NL", "Rotterdam": "NL", "Amsterdam": "NL",
    "Belgium": "BE", "Antwerp": "BE", "Brussels": "BE",
    "Italy": "IT", "Rome": "IT", "Milan": "IT",
    "Spain": "ES", "Madrid": "ES", "Barcelona": "ES",
    "Australia": "AU", "Sydney": "AU", "Melbourne": "AU",
    "Egypt": "EG", "Cairo": "EG", "Suez": "EG",
    "Turkey": "TR", "Istanbul": "TR", "Ankara": "TR",
    "Israel": "IL", "Tel Aviv": "IL",
    "Pakistan": "PK", "Karachi": "PK",
    "Bangladesh": "BD", "Dhaka": "BD",
    "Sri Lanka": "LK", "Colombo": "LK",
    "Hong Kong": "HK",
    "Poland": "PL", "Warsaw": "PL",
    "Chile": "CL", "Santiago": "CL",
    "Peru": "PE", "Lima": "PE",
    "South Africa": "ZA", "Johannesburg": "ZA",
    "Nigeria": "NG", "Lagos": "NG",
    "Kazakhstan": "KZ", "Almaty": "KZ",
}
