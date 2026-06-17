# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Searches the static mock listings dataset for secondhand clothing items that match the user's natural language request, optional size, and optional maximum price.

**Input parameters:**
- `description` (str): the search text extracted from the user's query, e.g. "vintage graphic tee".
- `size` (str | None): optional clothing size filter, e.g. "M" or "L".
- `max_price` (float | None): optional maximum price filter.

**What it returns:**
A list of matching listing dictionaries sorted by relevance. Each result contains the listing fields from `data/listings.json`, including `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

**What happens if it fails or returns nothing:**
If no listings match the query, the agent should stop the pipeline, set a user-facing error message, and return without calling `suggest_outfit` or `create_fit_card`.

---

### Tool 2: suggest_outfit

**What it does:**
Generates 1–2 outfit suggestions using the selected thrifted item and the user's wardrobe contents.

**Input parameters:**
- `new_item` (dict): the selected listing dictionary from `search_listings`.
- `wardrobe` (dict): the user's wardrobe dictionary, which contains an `items` list.

**What it returns:**
A string describing how to style the new item with wardrobe pieces. If the wardrobe is empty, it returns general styling advice rather than pairing with real items.

**What happens if it fails or returns nothing:**
If the wardrobe is empty, return a general styling recommendation for the selected item. If the tool otherwise fails, the agent should surface a fallback error message and stop.

---

### Tool 3: create_fit_card

**What it does:**
Creates a short, social-media-style outfit caption based on the outfit suggestion and the selected thrift item.

**Input parameters:**
- `outfit` (str): the outfit suggestion returned by `suggest_outfit`.
- `new_item` (dict): the selected listing dictionary from `search_listings`.

**What it returns:**
A short caption string that mentions the item, price, platform, and the overall outfit vibe.

**What happens if it fails or returns nothing:**
If the outfit suggestion is empty or missing, return a safe string explaining that a fit card could not be created. If the tool fails, surface an error and stop.

---

### Additional Tools (if any)

None.

---

## Planning Loop

**How does your agent decide which tool to call next?**

The agent follows a fixed sequential pipeline:
1. Parse the user query into `description`, `size`, and `max_price`.
2. Call `search_listings(description, size, max_price)`.
3. If `search_listings` returns no results, stop and return an error.
4. Otherwise, select the top result and call `suggest_outfit(selected_item, wardrobe)`.
5. Then call `create_fit_card(outfit_suggestion, selected_item)`.
6. Return the completed session state.

The decision is based on whether the search results are empty. If results exist, the agent proceeds; if not, it ends early and does not call the later tools.

---

## State Management

**How does information from one tool get passed to the next?**

A session dictionary stores all interaction state. The agent writes tool inputs and outputs into this session and reads from it for the next step.

Tracked fields:
- `query`: original raw user query
- `parsed`: extracted `description`, `size`, and `max_price`
- `search_results`: output list from `search_listings`
- `selected_item`: the top listing selected for styling
- `wardrobe`: user's wardrobe dict
- `outfit_suggestion`: text returned by `suggest_outfit`
- `fit_card`: caption returned by `create_fit_card`
- `error`: any error message or `None`

Flow:
- `parsed` feeds `search_listings`
- `search_results[0]` becomes `selected_item`
- `selected_item` and `wardrobe` feed `suggest_outfit`
- `outfit_suggestion` and `selected_item` feed `create_fit_card`

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Set `session["error"]` with a helpful message and return early without calling later tools. |
| suggest_outfit | Wardrobe is empty | Return a general styling recommendation that does not rely on wardrobe items. |
| create_fit_card | Outfit input is missing or incomplete | Return a safe caption error string and avoid raising an exception. |

---

## Architecture

```mermaid
flowchart TD
    U[User query] --> P[Planning loop]
    P --> Q[Parse query: description, size, max_price]
    Q --> S[search_listings(description, size, max_price)]
    S -->|no results| E[Set error, return early]
    S -->|results| T[selected_item = top result]
    T --> O[suggest_outfit(selected_item, wardrobe)]
    O --> C[create_fit_card(outfit_suggestion, selected_item)]
    C --> R[Return session with selected_item, outfit_suggestion, fit_card]

    P ---|stores| D[Session state]
    D --> S
    D --> O
    D --> C
```

State / session acts as the shared memory between tool calls.

---

## AI Tool Plan

**Milestone 3 — Individual tool implementations:**
- Use an AI code generation tool (Copilot/ChatGPT) to implement each tool from the `Tools` spec.
- Input the `search_listings` spec plus `utils/data_loader.py` and ask for a function that filters and ranks listings by keyword overlap, size, and price.
- Input the `suggest_outfit` spec plus `data/wardrobe_schema.json` and ask for a function that composes a Groq prompt using the selected item and wardrobe items.
- Input the `create_fit_card` spec and ask for a function that generates a short caption with item title, price, and platform.
- Verify each output by running unit tests and by checking that the tool returns expected types and safe fallback strings.

**Milestone 4 — Planning loop and state management:**
- Use the `Planning Loop` section and the Architecture diagram as input to the AI tool.
- Ask it to implement `run_agent()` so it parses the query, stores state in a session dict, handles no-results early return, and sequences the three tools.
- Verify the output by running `run_agent()` with both a successful query and a query that returns no results.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The agent parses the query to extract `description = "vintage graphic tee"`, `size = "M"` if present, and `max_price = 30.0`.

**Step 2:**
The agent calls `search_listings(description, size, max_price)` using the parsed values. The tool returns a list of matching listing dictionaries.

**Step 3:**
The agent checks `search_results`. If the list is empty, it sets an error message and returns early. If there are results, it selects `selected_item = search_results[0]`.

**Step 4:**
The agent calls `suggest_outfit(selected_item, wardrobe)` with the user's wardrobe. The tool returns a text outfit recommendation.

**Step 5:**
The agent calls `create_fit_card(outfit_suggestion, selected_item)` and stores the returned caption.

**Final output to user:**
The user receives the selected listing details, the outfit recommendation, and a short fit card caption, or an error message if no matching item exists.
