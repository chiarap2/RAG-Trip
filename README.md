# RAGTrip 🗺️🤖  
**A Spatially-Grounded Conversational Planner for Personalized Urban Itineraries**  
Accepted Demo at ACM SIGSPATIAL 2025

![Python](https://img.shields.io/badge/python-3.10+-blue)

---

## 🧠 What is RAGTrip?

**RAGTrip** is a modular conversational system that combines:
- **Large Language Models (LLMs)** for dialogue and natural language understanding,
- **Spatial reasoning** for route planning,
- **Retrieval-Augmented Generation (RAG)** for factual grounding.

Unlike traditional itinerary tools, RAGTrip supports **natural language interaction** and generates **personalized walking routes** grounded in real urban data and semantics.

### Key Features:
- 🎯 Interprets complex natural language queries with time, distance, and POI constraints
- 📍 Combines semantic and spatial grounding for accurate itineraries
- 🗺️ Generates dynamic maps with POIs from OpenStreetMap
- 🔄 Supports a RAG toggle to compare grounded vs. ungrounded outputs
- 💬 Interactive chat interface (demo-ready)

---

## 🗂️ Architecture

```
User Query
    ↓
[Conversational Module]
    ↓
 ┌───────────────────┐        ┌────────────────────┐
 │    Spatial Module │◀─────▶ │   Information      │
 │  (Routing + OSM)  │        │   Retrieval Module │
 └───────────────────┘        │   (FAISS + Embeds) │
                              └────────────────────┘
    ↓
Structured JSON → LLM → Final Response
                        ↳ Map + Summary
```

## 🚀 Quick Start

### ⚙️ Requirements

- Python 3.10+
- PyTorch with CUDA (GPU strongly recommended)
- [GraphHopper API key](https://www.graphhopper.com/)
- OSMnx + GeoPandas + Folium
- Model weights (download via Hugging Face):
  - `meta-llama/Llama-3.1-8B-Instruct`
  - `Snowflake/snowflake-arctic-embed-l-v2.0`

### 🛠 Installation

```bash
git clone https://github.com/your-org/RAGTrip.git
cd RAGTrip
pip install -r requirements.txt
```

🗂️ Code Structure
| File / Module                  | Description                                                     |
| ------------------------------ | --------------------------------------------------------------- |
| `RAG.py`                       | Loads encoder, tokenizer, and document index; handles retrieval |
| `RAGTrip.py`                   | Core orchestrator: intent classification and query routing      |
| `spatial.py`                   | Builds walking routes with GraphHopper and extracts POIs        |
| `utils.py`                     | Utilities for embedding, searching, and LLM querying            |
| `routing.py`                   | GraphHopper routing API interface                               |
| `enrichment.py`                | Retrieves and categorizes POIs using OSMnx                      |
| `filtering.py`                 | Filters segments based on time/distance constraints             |
| `visualization.py`             | Generates map visualizations (Folium)                           |
| `tools.py` / `search_tools.py` | Support for embedding creation and FAISS management             |



🧪 Example Use Case

"Plan a walk from Notre-Dame to the Louvre including museums and cafes within 5 minutes of the end."
`With RAG enabled:`
  - Suggests POIs like Sainte-Chapelle and nearby cafes within range
  - Generates a spatially coherent itinerary and interactive map
`With RAG disabled:`
  - The LLM might hallucinate POIs or place them in the wrong location

