import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from tools import create_fit_card, search_listings, suggest_outfit


def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_suggest_outfit_empty_wardrobe_returns_string():
    new_item = {"title": "Vintage Jacket", "price": 40.0, "platform": "Depop", "condition": "good"}
    wardrobe = {"items": []}
    result = suggest_outfit(new_item, wardrobe)
    assert isinstance(result, str)
    assert result.strip() != ""


def test_create_fit_card_empty_outfit_returns_error_string():
    new_item = {"title": "Vintage Jacket", "price": 40.0, "platform": "Depop", "condition": "good"}
    result = create_fit_card("", new_item)
    assert isinstance(result, str)
    assert "could not create a fit card" in result
