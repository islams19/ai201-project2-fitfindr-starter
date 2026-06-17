"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.
    """

    if not description or not description.strip():
        return []

    keywords = description.lower().split()
    listings = load_listings()
    results: list[tuple[int, dict]] = []

    for listing in listings:
        if max_price is not None and listing.get("price", float("inf")) > max_price:
            continue

        if size is not None:
            listing_size = listing.get("size", "")
            if size.lower() not in listing_size.lower():
                continue

        searchable_text = " ".join([
            str(listing.get("title", "")),
            str(listing.get("description", "")),
            str(listing.get("category", "")),
            " ".join(listing.get("style_tags", [])),
            " ".join(listing.get("colors", [])),
            str(listing.get("brand", "") or ""),
            str(listing.get("platform", "")),
        ]).lower()

        score = sum(1 for word in keywords if word in searchable_text)
        if score > 0:
            results.append((score, listing))

    results.sort(key=lambda item: item[0], reverse=True)
    return [listing for _, listing in results]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.
    """

    client = _get_groq_client()
    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        prompt = f"""
The user found this thrifted item:

{new_item}

The user's wardrobe is empty.

Give general styling advice for this item.
Be specific and helpful.
"""
    else:
        prompt = f"""
The user found this thrifted item:

{new_item}

The user's wardrobe contains:

{wardrobe_items}

Suggest 1-2 outfits using ONLY the wardrobe items listed above.
Do not invent any items.
Explain why each outfit works.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are FitFindr, a fashion outfit assistant."
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.
    """

    if not outfit or outfit.strip() == "":
        return (
            "I found an item, but I could not create a fit card "
            "because the outfit suggestion was empty."
        )

    client = _get_groq_client()

    prompt = f"""
Create a short social media outfit caption.

Item:
Title: {new_item.get("title")}
Price: ${new_item.get("price")}
Platform: {new_item.get("platform")}
Condition: {new_item.get("condition")}

Outfit suggestion:
{outfit}

Requirements:
- 2 to 4 sentences
- casual and authentic
- mention the item name, price, and platform naturally
- describe the outfit vibe
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You write casual outfit captions for FitFindr."
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        temperature=0.9,
    )

    return response.choices[0].message.content.strip()
