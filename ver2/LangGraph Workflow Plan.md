> I want to build a multi-step agentic research and report writing LLM application like DeepResearch, using LangGraph, Claude, online search, SEC Edgar, and some internal private data sources. My goal is to create financial pitchbooks and reports that aims to provide bankers with material ready for pitches they'd make to potential clients, advertising our company's resources, past, experience and tie it in to the sector that the client participates in. As Claude does not have online search grounding abilities like other LLMs like Gemini, I plan to use DuckDuckGo for online search. 
> Please prepare a LangGraph workflow plan for me, especially how I organize the workflow, what the ideal step by step process for the agent's research and generation pipeline should be, and what data sources I will need for my aims, like what I can use SEC Edgar for, which sources would be best for market cap, market share, what types of graphs and infographics I can prepare, etc.

To design the best LangGraph workflow for your multi-step agentic research and report writing application, could you clarify a few points:

1. What industries or sectors do you primarily want to support in your pitchbooks (e.g., tech, healthcare, industrials)?
2. What internal/private data sources do you have access to (CRM, proprietary transaction databases, previous pitchbooks, etc.)?
3. What output format do you need (PDF, HTML, PowerPoint, etc.)?
4. Do you want to customize the reports based on geography, company size, or deal type (e.g., M&A vs. capital raising)?
5. Are you interested in automated generation of charts/infographics (and if so, what kind: comps tables, market share pie charts, deal timelines, etc.)?

Once I have these details, I can map out a precise LangGraph workflow and data integration plan tailored to your goals.

> To answer your points:
> 1. It should be able to adapt to any industrial. We, ourselves, act as an investment bank, and our clients could be from any sectors. So this should be generalizable.
> 2. We've got previous pitchbooks, public executed deals from an internal database, and some letters to shareholders. Mostly we're planning to rely on public data like from yahoo finance or 10Q and 10K filings from SEC, and just research into the field and putting that into perspective with what deals we've executed in the past.
> 3. Markdown would work or whatever is most simple for Claude to generate as a format will work, we can then convert whatever it is programmatically into a PDF without reliance on the LLM.
> 4. Yes, please customize the reports based on the most optimal or popular types that you deem fit.
> 5. All of the stated chart/infographic types here sound great, could we have the LLM pick one based on what they feel is needed based on the report at the moment?

Great — here's a **LangGraph workflow plan** tailored to your goals, broken down into **agentic steps**, **data sources**, and **output structuring**, followed by **charting ideas** and automation strategies.

---

### **LangGraph Workflow Plan: Agentic Pitchbook Generator**

#### **1. Graph Structure Overview**
Your LangGraph can be structured as a **multi-agent graph with task-specific nodes**, where each node performs one of the following:

- **Data Gathering**
- **Data Analysis**
- **Contextualization**
- **Drafting**
- **Refinement**
- **Final Assembly**

Each node may loop or retry based on confidence thresholds, fallback strategies, or error correction (e.g., if search returns insufficient results).

---

### **2. Agent Nodes & Step-by-Step Workflow**

| Step | Node | Role | Tools | Output |
|------|------|------|-------|--------|
| 1 | **Client Profiling Agent** | Understands the target client: company, sector, geography, deal type, etc. | Claude | JSON profile (company, sector, region, type of pitch) |
| 2 | **Public Company Data Collector** | Gathers financials, filings, company info from public sources | DuckDuckGo, Yahoo Finance API, SEC Edgar | Raw financials, company description, key filings |
| 3 | **Market Landscape Agent** | Searches for sector news, trends, key competitors, deals | DuckDuckGo, possibly AlphaSense-like tools or Reddit scraping | Market overview, competitive positioning |
| 4 | **Internal Relevance Finder** | Matches previous deals, pitchbooks, shareholder letters based on similarity | Vector DB, keyword matching | Internal experience summary, relevant past work |
| 5 | **Comparables & Metrics Generator** | Gathers comps, market cap, valuation multiples | Yahoo Finance, Finviz, internal DB | Comparables table (valuation, revenue, EBITDA, etc.) |
| 6 | **Infographics Generator** | Suggests and creates suitable visuals based on context | Claude + Matplotlib/Plotly | Market share pie chart, comps bar chart, timeline |
| 7 | **Narrative Drafting Agent** | Writes the draft report (markdown, structured sections) | Claude | Full draft with placeholders for charts |
| 8 | **Critique & Refinement Agent** | Reviews for tone, data inconsistencies, flow | Claude (review prompt) | Cleaned up draft |
| 9 | **Output Compiler** | Assembles report into Markdown or PDF | Python/Pandoc or PDFLib | Final PDF or DOCX |

---

### **3. Suggested Report Structure (Output)**

Generated in **Markdown**, then exported:

```
# [Client Name] – Sector Overview & Pitchbook

## Executive Summary
- High-level pitch customized to client sector and business

## Company Snapshot
- Description
- Financial Summary (Table)

## Market Landscape
- Sector trends
- Recent transactions
- Key competitors (with revenue, valuation if public)

## Our Experience
- Relevant past deals
- Timeline or key stats

## Comparative Analysis
- Comps table (public comparables, valuation multiples)

## Strategic Fit
- Why we’re a good fit
- Suggested deal structures or investment ideas

## Appendix
- Raw financials
- Market news snippets
- Charts/Infographics
```

---

### **4. Data Sources by Section**

| Section | Source |
|--------|--------|
| Financials | SEC Edgar (10-K/10-Q parsing), Yahoo Finance |
| Sector Trends | DuckDuckGo News, Financial blogs, press releases |
| Comparables | Yahoo Finance, Finviz, internal deal DB |
| Internal Experience | Prior pitchbooks, internal database |
| Visuals | Generated based on financial/comps data |

---

### **5. Chart/Infographic Ideas (LLM Picks Contextually)**

- **Market Share Pie Chart** – If multiple competitors are discussed
- **Valuation Bar Graph** – Comparing EV/EBITDA or P/E
- **Timeline of Sector Deals** – Highlighting activity over past years
- **Revenue Growth Line Chart** – If historical financials are available
- **Custom Graphic** – Claude can describe a custom chart, which your code renders

Use a Python tool (e.g., Plotly, Matplotlib) or D3.js if needed, and Claude can generate chart instructions.

---

### **6. Claude-Specific Considerations**

Since Claude lacks native browsing:
- Use **LangGraph tooling nodes** or external functions to handle search and scraping.
- Pass results to Claude for synthesis (e.g., wrap DuckDuckGo search in a Python node).
- Make sure to **chunk long SEC filings** and use summarization steps.

---

### **7. Error Handling & Regeneration**

- Set thresholds (e.g., “Did this agent find at least 3 relevant comps?”)
- Allow fallback to manual human curation node or regenerate via search
- Claude can return self-assessment metadata like “Confidence: 7/10” with each draft

---

Would you like a code scaffold for the LangGraph setup next (including sample nodes and chaining structure), or mock JSON outputs for each stage to help with implementation?

> I don't need a code scaffold, but an overview of the nodes and chaining structure would be helpful, as well as mock JSON ouputs for each stage.

Great! Below is a clear overview of the **LangGraph node structure**, including **chaining logic**, followed by **mock JSON outputs** for each major node. This should help you design the flow and validate outputs at each step.

---

## **LangGraph Workflow: Node Overview**

```
[Start] 
   |
   v
[1. Client Profiling Agent]
   |
   v
[2. Public Company Data Collector]  ---> [3. Market Landscape Agent]
   |                                             |
   |                                             v
   |<---------------------------------merge----[4. Internal Relevance Finder]
   |                                                     |
   v                                                     v
[5. Comparables & Metrics Generator]              [6. Infographics Generator]
   \                                                    /
    \--------------------------------------------------/
                          |
                          v
                [7. Narrative Drafting Agent]
                          |
                          v
               [8. Critique & Refinement Agent]
                          |
                          v
                    [9. Output Compiler]
                          |
                          v
                        [End]
```

---

## **Node-by-Node Breakdown with Mock JSON Outputs**

---

### **1. Client Profiling Agent**

**Purpose:** Interpret initial prompt (e.g., "Create a pitchbook for XYZ Corp in the fintech sector.")

**Mock Input:**  
User input: `"Create a pitchbook for XYZ Corp, a mid-cap fintech company in New York."`

**Mock Output:**
```json
{
  "company_name": "XYZ Corp",
  "sector": "Fintech",
  "region": "North America",
  "pitch_type": "M&A advisory",
  "company_size": "Mid-cap"
}
```

---

### **2. Public Company Data Collector**

**Purpose:** Pull key financials, summary, recent performance

**Mock Output:**
```json
{
  "financials": {
    "revenue": "450000000",
    "ebitda": "72000000",
    "net_income": "32000000",
    "market_cap": "1200000000"
  },
  "description": "XYZ Corp is a fintech firm offering payment processing and digital wallets.",
  "headquarters": "New York, USA",
  "sec_filings": {
    "10K_summary": "Revenue increased 12% YoY; focus on international expansion...",
    "10Q_summary": "Q1 shows modest growth with increased R&D spending..."
  }
}
```

---

### **3. Market Landscape Agent**

**Purpose:** Get recent sector trends and competitors.

**Mock Output:**
```json
{
  "sector_trends": [
    "Digital wallet usage growing rapidly in emerging markets.",
    "Regulatory pressures increasing on cross-border payments."
  ],
  "key_competitors": [
    {"name": "Block Inc", "market_cap": "36000000000"},
    {"name": "PayPal", "market_cap": "70000000000"}
  ],
  "recent_deals": [
    {"deal": "Visa acquired CurrencyCloud for $963M", "year": 2021}
  ]
}
```

---

### **4. Internal Relevance Finder**

**Purpose:** Match prior deals or pitchbooks to the client profile.

**Mock Output:**
```json
{
  "relevant_deals": [
    {
      "client": "Alpha Payments",
      "deal_type": "Series C Fundraising",
      "year": 2022,
      "deal_size": "55M USD"
    },
    {
      "client": "BankLink",
      "deal_type": "M&A Sell-Side",
      "year": 2021,
      "deal_size": "120M USD"
    }
  ],
  "past_pitchbook_sections": [
    "Fintech Market Growth Projections",
    "Digital Infrastructure Investment Trends"
  ]
}
```

---

### **5. Comparables & Metrics Generator**

**Purpose:** Generate comps tables and valuation multiples.

**Mock Output:**
```json
{
  "comps": [
    {
      "company": "PayPal",
      "revenue": "27000000000",
      "ev_ebitda": "18x",
      "p_e": "21x"
    },
    {
      "company": "Block Inc",
      "revenue": "19000000000",
      "ev_ebitda": "22x",
      "p_e": "25x"
    }
  ],
  "suggested_multiple_range": {
    "ev_ebitda": "18x–22x",
    "p_e": "20x–25x"
  }
}
```

---

### **6. Infographics Generator**

**Purpose:** Decide what charts to generate based on current content.

**Mock Output:**
```json
{
  "charts": [
    {
      "type": "bar",
      "title": "Comparable Company EV/EBITDA Multiples",
      "data": {
        "PayPal": 18,
        "Block Inc": 22
      }
    },
    {
      "type": "timeline",
      "title": "Key Fintech M&A Transactions (2020–2024)",
      "data": [
        {"year": 2021, "event": "Visa acquires CurrencyCloud"},
        {"year": 2023, "event": "Mastercard acquires Finicity"}
      ]
    }
  ]
}
```

---

### **7. Narrative Drafting Agent**

**Purpose:** Assemble all content into a structured Markdown pitchbook.

**Mock Output (Markdown):**
```markdown
# XYZ Corp – Fintech Pitchbook

## Executive Summary
XYZ Corp is positioned to capitalize on emerging trends in digital wallets and cross-border payments...

## Company Snapshot
Revenue: $450M | EBITDA: $72M | Market Cap: $1.2B

## Market Landscape
Digital wallet usage is expanding rapidly in Asia and Africa...

## Comparable Companies
| Company     | EV/EBITDA | P/E  |
|-------------|-----------|------|
| PayPal      | 18x       | 21x  |
| Block Inc   | 22x       | 25x  |

## Our Relevant Experience
- 2022: Alpha Payments Series C ($55M)
- 2021: BankLink M&A Sell-Side ($120M)

## Infographics
![Comps Chart](charts/comps_ev_ebitda.png)

## Appendix
- 10-K Summary
- Competitor Market Caps
```

---

### **8. Critique & Refinement Agent**

**Purpose:** Fix tone, tighten writing, flag issues.

**Mock Output:**
```json
{
  "improvements": [
    "Simplified technical jargon in executive summary.",
    "Clarified growth rates for XYZ Corp vs peers.",
    "Flagged outdated financial data for PayPal."
  ],
  "final_markdown": "..."
}
```

---

### **9. Output Compiler**

**Purpose:** Convert Markdown into PDF and embed visuals.

**Mock Output:**
```json
{
  "output_format": "PDF",
  "file_path": "/reports/XYZ_Corp_Pitchbook_2025.pdf",
  "status": "success"
}
```

---

Would you also like:
- A full prompt structure per agent (e.g., Claude prompts)?
- A JSON schema definition to enforce validation between LangGraph nodes?
- A fallback/recovery plan in case certain nodes fail (e.g., no comparables found)?

> Actually, some code scaffolding relating to the multi-agent setup would be useful. I've only ever used single agent workflows before, how would I set up a multi-agent LangGraph system? How do they share data between each other? Who orchestrates them, provides their inputs, and where do their findings go? Or do I just have Python call each agent programmatically in order, collect their outputs and then provide it to Claude in a new call at the end to put it all together?

I’ve sketched out a Python-based LangGraph scaffold that:

- Defines each agent as a Python function (wrapping Claude calls, data-fetchers, renderers).
- Creates a `Graph` of `Node`s, each linked by `Edge`s to enforce sequential data flow.
- Orchestrates execution via `graph.execute`, passing outputs between agents automatically.
- Shows where you’d integrate DuckDuckGo, SEC Edgar pulls, internal DB queries, and chart rendering.
- Ends by converting final Markdown into a PDF via your chosen library.

You can customize each function (e.g. error handling, retries, confidence thresholds) and swap in your real data-connector implementations. Let me know if you’d like deeper examples for any specific node!

> I'm a little confused on the distinction between agents and nodes here. Can you provide brief definitions of what agents are here and how they relate to the nodes? I was under the impression that an agent was the entire workflow and all the nodes and edges under it. Also, I don't see the LangGraph state that is going to be passed around from node to node in your example.

Great questions — LangGraph can indeed be a bit nuanced at first. Let’s clarify:

---

### **1. What is an “agent” in this context?**

In **LangGraph**, the term “agent” is **not** a special class or type — it's a **conceptual role**.

- You can **implement an agent** as a **function** or **class** that takes some input, possibly uses an LLM or tools, and returns structured output.
- In practice, **each node** can be an “agent” — because it encapsulates a unit of reasoning or action.
- However, **LangGraph doesn’t care if you call it an agent or not** — it's just a node in the graph.

So:
- **Agent = logical unit of reasoning with memory, tools, or goals.**
- **Node = actual implementation of that logic inside a LangGraph.**

> Think of it this way: *“Every node can be an agent, but not all agents need to live in nodes — some can be orchestration logic outside the graph.”*

---

### **2. What is a node then?**

- A **LangGraph `Node`** is a wrapper around a function or callable that:
  - Accepts the current graph **state**
  - Returns an updated **partial state**

Nodes are the *execution units* in the LangGraph.

---

### **3. What is “state” in LangGraph and where is it in the code?**

You’re right — in the scaffold I gave earlier, I abstracted away the **state object**, which is crucial to LangGraph. Let me clarify:

In LangGraph, you define a **state schema** (like a dict) that gets passed from node to node.

#### Example:

```python
from langgraph.graph import State

class PitchbookState(State):
    user_prompt: str
    profile: dict = {}
    public_data: dict = {}
    market_summary: str = ""
    internal_matches: list = []
    comps: dict = {}
    chart: dict = {}
    draft: str = ""
    refined_draft: str = ""
    final_pdf_path: str = ""
```

- Each **node reads from and writes to** one or more fields in this state.
- This allows **shared memory** between “agents”/nodes and enables **branching, merging, memory passing**, etc.

You would then define nodes like:

```python
def client_profiling_agent(state: PitchbookState):
    profile = extract_profile(state.user_prompt)
    return {"profile": profile}
```

And LangGraph will automatically **merge the returned dict into the current state**.

---

### **4. So how do multiple agents share data?**

They share it via the **graph state**, not via function parameters.

This means:
- No manual chaining of function calls like in normal Python.
- State is persisted, and each node only updates its “responsibility”.

LangGraph handles:
- Merging state updates.
- Passing the state between nodes.
- Running the right node based on graph edges.

---

### **Summary Cheat Sheet:**

| Concept | Meaning in LangGraph context |
|--------|-------------------------------|
| **Agent** | A logical unit (often a node) that does autonomous reasoning. Not a formal class. |
| **Node** | A callable wrapper that accepts and returns updates to the `state`. |
| **Graph** | A flow of nodes with defined edges and logic. |
| **State** | A mutable memory object (dict or class) passed through the workflow. |
| **Execution** | Driven by calling `graph.invoke(state)` or `.stream(state)` with initial input. |

---

Would you like me to rewrite the earlier scaffold to include a concrete `PitchbookState` and show how each node consumes/produces parts of it?

> Yes, please rewrite it using the new state. 

I've updated the scaffold to include a clearly defined `PitchbookState`, and each node now reads from and writes to specific fields in that state. This makes the multi-agent design concrete: each “agent” (node) shares information via `state`, and LangGraph handles the orchestration automatically.

Let me know if you'd like to introduce branching logic (e.g., different flows for pitch types) or tool integrations like real SEC Edgar parsers or chart renderers.