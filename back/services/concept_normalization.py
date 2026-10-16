"""Canonical graph identifiers shared by queries and seed ingestion."""
import re
import unicodedata

ALIASES = {
    "인플레이션": "inflation", "물가 상승": "inflation",
    "디플레이션": "deflation", "기회비용": "opportunity cost", "기회 비용": "opportunity cost",
    "환율": "exchange rate", "이자율": "interest rate", "금리": "interest rate",
    "기준금리": "base interest rate", "소비자물가지수": "consumer price index",
    "cpi": "consumer price index", "gdp": "gross domestic product",
    "gross domestic product (gdp)": "gross domestic product",
}

def normalize_concept(value: str) -> str:
    normalized = re.sub(r"[\s_-]+", " ", unicodedata.normalize("NFKC", value).strip().casefold())
    return ALIASES.get(normalized, normalized)
