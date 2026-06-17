
# FitFindr — Starter Kit

This starter kit contains the core code and data for Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
├── tools.py                   # Tool implementations for the agent
├── agent.py                   # Planning loop implementation
├── app.py                     # Gradio UI for FitFindr
├── tests/
│   └── test_tools.py          # Pytest coverage for the tools
└── requirements.txt           # Python dependencies
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with:

```
GROQ_API_KEY=your_key_here
```

## Tool Inventory

### `search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]`

- Purpose: search the mock listings dataset for items matching a natural language description, optional size, and optional maximum price.
- Inputs:
  - `description` (str): the user's query text, e.g. "vintage graphic tee".
  - `size` (str | None): optional clothing size filter, e.g. "M".
  - `max_price` (float | None): optional maximum price filter.
- Outputs:
  - `list[dict]`: matching listing dictionaries sorted by relevance.
- Notes:
  - Uses `load_listings()` from `utils.data_loader.py`.
  - Filters out items above `max_price` and items whose size does not match.
  - Scores remaining listings by keyword overlap across title, description, category, style tags, colors, brand, and platform.

### `suggest_outfit(new_item: dict, wardrobe: dict) -> str`

- Purpose: generate 1–2 outfit suggestions that incorporate the selected thrift find and the user's wardrobe.
- Inputs:
  - `new_item` (dict): the selected listing from `search_listings()`
  - `wardrobe` (dict): a wardrobe dict with an `items` key; may be empty.
- Outputs:
  - `str`: outfit suggestion text from the LLM.
- Notes:
  - Uses Groq model `llama-3.3-70b-versatile`.
  - If the wardrobe is empty, it still returns useful styling advice rather than crashing.

### `create_fit_card(outfit: str, new_item: dict) -> str`

- Purpose: create a short, social-media-friendly outfit caption for the thrifted find.
- Inputs:
  - `outfit` (str): the outfit suggestion returned by `suggest_outfit()`
  - `new_item` (dict): the selected listing dict
- Outputs:
  - `str`: a caption string.
- Notes:
  - Uses Groq model `llama-3.1-8b-instant`.
  - If `outfit` is empty, it returns a descriptive error string instead of raising an exception.

## Planning Loop

The planning loop is implemented in `agent.py`.

1. Initialize a new session dict with `_new_session(query, wardrobe)`.
2. Parse the query into `description`, `size`, and `max_price` using regex.
3. Call `search_listings(description, size, max_price)`.
4. If no listings are found, set `session["error"]` and return early.
5. Otherwise, store the first result in `session["selected_item"]`.
6. Call `suggest_outfit(session["selected_item"], wardrobe)` and store the returned text in `session["outfit_suggestion"]`.
7. Call `create_fit_card(session["outfit_suggestion"], session["selected_item"])` and store the caption in `session["fit_card"]`.
8. Set `session["error"] = None` and return the session.

This ensures the tools run in sequence and that the agent does not call `suggest_outfit` or `create_fit_card` when there are no search results.

## State Management

The session dict is the single source of truth for each interaction. It includes:

- `query`: original user query string
- `parsed`: extracted values for `description`, `size`, and `max_price`
- `search_results`: list of matching listing dicts
- `selected_item`: top listing dict chosen from search results
- `wardrobe`: the selected wardrobe dict
- `outfit_suggestion`: text returned from `suggest_outfit()`
- `fit_card`: text returned from `create_fit_card()`
- `error`: error message or `None`

All intermediate values are stored so the agent state can be inspected after a run.

## Error Handling

Each tool and branch is handled explicitly:

- `search_listings`: returns `[]` for no matches, which causes `agent.py` to set `session["error"]` and return without calling the later tools.
  - Example test: `run_agent('designer ballgown size XXS under $5', get_example_wardrobe())` produces an error message and keeps `session['fit_card']` as `None`.

- `suggest_outfit`: returns a helpful string even when the wardrobe is empty.
  - Example test: `python3 -c "from tools import search_listings, suggest_outfit; from utils.data_loader import get_empty_wardrobe; results = search_listings('vintage graphic tee', size=None, max_price=50); print(suggest_outfit(results[0], get_empty_wardrobe()))"`

- `create_fit_card`: returns an error message string when the `outfit` argument is empty instead of raising an exception.
  - Example test: `python3 -c "from tools import search_listings, create_fit_card; results = search_listings('vintage graphic tee', None, 50); print(create_fit_card('', results[0]))"`

## Testing

Run the tool tests with:

```bash
pytest tests/
```

The repository includes `tests/test_tools.py` covering:
- search results returned for normal queries
- empty search results returning `[]`
- price filtering in `search_listings`
- empty wardrobe handling in `suggest_outfit`
- empty outfit handling in `create_fit_card`

## Spec Reflection

This README now reflects the actual implementation in the repo, including:
- exact tool names and signatures from `tools.py`
- the planning loop behavior from `agent.py`
- the session state shape used for inspection and debugging
- concrete error-handling behavior verified with direct tests

The current implementation differs slightly from the earlier starter spec by keeping `search_listings()` focused on `description`, `size`, and `max_price` only, and by not exposing `style_tags` as a separate external parameter in the public tool signature.

## AI Usage

Two specific AI-assisted development steps were used during implementation:

1. Tool implementation generation
- Input: the `planning.md` tool spec sections for Tool 1, Tool 2, and Tool 3 plus the dataset shape from `utils/data_loader.py` and `data/wardrobe_schema.json`.
- Produced: a first draft of `search_listings()`, `suggest_outfit()`, and `create_fit_card()` in `tools.py`.
- Changed/overrode: adapted the draft to the actual repo APIs by removing the separate external `style_tags` parameter, adding a guard in `create_fit_card()` so it returns a safe message for empty outfits, and verifying `suggest_outfit()` works when the wardrobe is empty.

2. Planning loop and branch behavior
- Input: the Architecture mermaid diagram and the Planning Loop section from `planning.md`.
- Produced: a draft `run_agent()` flow in `agent.py` that parsed query fields, ran `search_listings()`, and branched on result existence before calling the later tools.
- Changed/overrode: explicitly stored session state fields such as `search_results`, `selected_item`, `outfit_suggestion`, and `fit_card`; added the early-return no-results branch; and simplified the query parser to match the actual available inputs.

## Running the App

Start the Gradio app with:

```bash
python3 app.py
```

Then open the local URL printed in the terminal, usually `http://127.0.0.1:7860`.


# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.
## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

Milestone 1:
FitFindr helps the user find a clothing item based on their request, such as style, size, and budget. The search_listings tool runs first, and if it finds a matching item, FitFindr uses suggest_outfit to match it with the user’s wardrobe, then create_fit_card to write a short social-style outfit caption. If search_listings finds no results, FitFindr stops and tells the user how to change the search instead of calling the next tools.
Milestone 2:
### Tool 1: search_listings

**What it does:**  
Searches the secondhand listings dataset for clothing items that match the user's request.

**Input parameters:**
- `query` — string — the item the user wants, such as "vintage graphic tee"
- `size` — string — the clothing size the user wants, such as "M"
- `max_price` — float — the highest price the user is willing to pay
- `style_tags` — list of strings — style words from the user, such as ["vintage", "grunge"]

**Returns:**  
A list of matching listing dictionaries. Each dictionary contains `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

**If it fails or returns nothing:**  
The agent stops and tells the user to try a broader search, a different size, or a higher budget. It does not call `suggest_outfit`.

### Tool 2: suggest_outfit

**What it does:**  
Creates an outfit suggestion using the selected listing and the user’s wardrobe.

**Input parameters:**
- `new_item` — dictionary — the listing selected from `search_listings`
- `wardrobe` — list of dictionaries — the user’s wardrobe items, where each item includes fields such as item name, category, colors, style tags, and notes

**Returns:**  
A dictionary containing the selected new item, matched wardrobe pieces, and a written outfit suggestion explaining how to wear them together.

**If it fails or returns nothing:**  
The agent explains that it could not match the item with the wardrobe. If the wardrobe is empty, it gives a general styling suggestion instead.

### Tool 3: create_fit_card

**What it does:**  
Creates a short social-media-style outfit caption for the final look.

**Input parameters:**
- `outfit` — dictionary — the outfit suggestion returned by `suggest_outfit`
- `new_item` — dictionary — the selected listing from `search_listings`

**Returns:**  
A string caption that includes the new item, price/platform when useful, and a short description of the outfit vibe.

**If it fails or returns nothing:**  
The agent still shows the outfit suggestion without the caption and tells the user the fit card could not be created.

Planning tool:
The agent first reads the user request and extracts the item name, size, max price, and style words. If size or budget is missing, the agent asks a follow-up question before using any tool.

Next, the agent calls `search_listings(query, size, max_price, style_tags)`. After `search_listings` runs, the agent checks if `results` is empty. If `results` is empty, the agent sets an error message telling the user to try a broader item name, different size, or higher budget, then returns early.

If `results` is not empty, the agent sets `selected_item = results[0]` because the results are sorted by relevance. Then the agent loads the user wardrobe and calls `suggest_outfit(new_item=selected_item, wardrobe=wardrobe)`.

After `suggest_outfit` runs, the agent checks if the outfit suggestion is empty or failed. If it failed, the agent returns the selected item plus a general styling suggestion. If it succeeds, the agent saves the outfit suggestion and calls `create_fit_card(outfit=outfit_suggestion, new_item=selected_item)`.

After `create_fit_card` runs, the agent checks if the fit card caption is empty. If it is empty, the agent returns the selected item and outfit suggestion only. If it succeeds, the agent returns the selected item, the outfit suggestion, and the fit card caption to the user.

## Architecture

```mermaid
flowchart TD
    A[User Query] --> B[Planning Loop]

    B --> C[Extract item name, size, max price, style tags]
    C --> D[search_listings query, size, max_price, style_tags]

    D --> E{Any results?}
    E -- No --> F[Session State: error_message = No listings found]
    F --> G[Return early to user]

    E -- Yes --> H[Session State: selected_item = results[0]]
    H --> I[suggest_outfit selected_item, wardrobe]

    I --> J{Outfit suggestion created?}
    J -- No --> K[Session State: general styling suggestion]
    K --> L[Return item + general styling]

    J -- Yes --> M[Session State: outfit_suggestion]
    M --> N[create_fit_card outfit_suggestion, selected_item]

    N --> O{Fit card created?}
    O -- No --> P[Return selected item + outfit suggestion]
    O -- Yes --> Q[Session State: fit_card]
    Q --> R[Return selected item + outfit suggestion + fit card]

## AI Tool Plan

For `search_listings`, I will use ChatGPT. I will give it the Tool 1 block from `planning.md` the dataset fields from the README, and the helper function `load_listings()` from `utils/data_loader.py`. I expect it to produce a Python function that filters listings by query, size, max price, and style tags. Before using it I will verify that it checks all required fields, returns full listing dictionaries, sorts results by relevance and returns an empty list when nothing matches.

For `suggest_outfit` I will use ChatGPT. I will give it the Tool 2 block from `planning.md` the wardrobe schema and the example wardrobe format from `data/wardrobe_schema.json`. I expect it to produce a Python function that takes a selected item and wardrobe list chooses matching wardrobe pieces and returns a dictionary with the new item matched wardrobe items and outfit explanation. Before using it I will verify that it does not invent wardrobe items handles an empty wardrobe and explains why the outfit works.

For `create_fit_card` I will use ChatGPT. I will give it the Tool 3 block from `planning.md` and examples of the caption style from the Complete Interaction section. I expect it to produce a function that creates a short social-media-style caption using the selected item, price, platform, and outfit vibe. Before using it I will verify that the caption uses real listing details and does not make up prices, brands, or platforms.

For the planning loop I will use ChatGPT. I will give it the Planning Loop section and the Architecture Mermaid diagram from `planning.md`. I expect it to produce agent logic that calls `search_listings` first stops early if results are empty, selects `results[0]` if results exist then calls `suggest_outfit` and finally calls `create_fit_card`. Before using it I will check that each branch in the diagram is included and that failure cases return early instead of calling the next tool incorrectly.

For testing I will use ChatGPT to help create test cases. I will give it the tool descriptions, failure modes, and the sample user query from the Complete Interaction section. I expect it to produce test queries for successful search, no results, empty wardrobe, and missing information. I will verify the output by running at least three searches and checking that the agent response follows the planning loop exactly.

## Complete Interaction Walkthrough

Example user query:  
"I'm looking for a vintage graphic tee under $30, size M. I mostly wear baggy jeans and chunky sneakers."

Step 1: The planning loop reads the user query and extracts:
- `query = "vintage graphic tee"`
- `size = "M"`
- `max_price = 30.0`
- `style_tags = ["vintage"]`

Step 2: The agent calls:
`search_listings(query="vintage graphic tee", size="M", max_price=30.0, style_tags=["vintage"])`

Step 3: `search_listings` searches `data/listings.json` and returns matching listing dictionaries. Example return:
`[{"id": "...", "title": "Faded Band Tee", "description": "...", "category": "tops", "style_tags": ["vintage", "grunge"], "size": "M", "condition": "Good", "price": 22.0, "colors": ["black", "gray"], "brand": "...", "platform": "Depop"}]`

Step 4: Since the result list is not empty, the agent sets:
`selected_item = results[0]`

Step 5: The agent loads the example wardrobe and calls:
`suggest_outfit(new_item=selected_item, wardrobe=example_wardrobe)`

Step 6: `suggest_outfit` returns an outfit suggestion dictionary containing the selected item, matched wardrobe pieces, and explanation. Example return:
`{"new_item": selected_item, "matched_items": ["wide-leg jeans", "platform Docs"], "outfit_text": "Pair this with your wide-leg jeans and platform Docs for a classic 90s grunge look. Roll the sleeves once and tuck the front corner slightly for shape."}`

Step 7: Since the outfit suggestion succeeds, the agent calls:
`create_fit_card(outfit=outfit_suggestion, new_item=selected_item)`

Step 8: `create_fit_card` returns a short caption string. Example return:
`"thrifted this faded band tee off depop for $22 and honestly it was made for my wide-legs  full look in my stories"`

Step 9: The user sees the final response with:
- the selected listing name, price, platform, size, and condition
- the outfit suggestion
- the fit card caption

Final user response:
"I found a Faded Band Tee for $22 on Depop in size M and good condition. Pair it with your wide-leg jeans and platform Docs for a classic 90s grunge look. Fit card: thrifted this faded band tee off depop for $22 and honestly it was made for my wide-legs  full look in my stories"

| Error Case | Agent Response |
|------------|---------------|
| No listings found | "I couldn't find any vintage graphic tees in size M under $30. Try increasing your budget, choosing a different size, or using a broader search term such as 'graphic tee' or 'band tee'." |
| Missing size | "What size are you looking for? I need a size before I can search the listings." |
| Missing budget | "What's your maximum budget for this item? I need a price range before searching." |
| Empty wardrobe | "I found a matching item, but your wardrobe is empty. Here's a general styling suggestion for the item instead of a personalized outfit recommendation." |
| Outfit matching failed | "I found a matching item, but I couldn't find any wardrobe pieces that pair well with it. Here's a general outfit suggestion you can use as a starting point." |
| Fit card generation failed | "I found a matching item and created an outfit suggestion, but I couldn't generate a fit card caption. You can still use the outfit recommendation." |
| Invalid user request | "I couldn't understand the item you're looking for. Please provide an item type, size, and budget, such as 'vintage hoodie size L under $40'." |