import sys
import streamlit as st
import pandas as pd

# UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import (
    NEO4J_URI,
    NEO4J_USERNAME,
    NEO4J_PASSWORD,
    NEO4J_DATABASE,
    QDRANT_PATH,
    QDRANT_URL,
    QDRANT_API_KEY,
    CSV_DATA_PATH,
    MONOGRAPHS_DATA_PATH,
    EMBEDDING_MODEL_NAME
)
from src.graph_db import Neo4jGraphManager
from src.vector_db import VectorStoreManager
from src.agent import BiomedicalAgent

st.set_page_config(
    page_title="Biomedical & Drug Query Agent | Hybrid Graph + Vector RAG",
    page_icon="🧬",
    layout="wide"
)

# Initialize Session State
@st.cache_resource(show_spinner="Initializing Knowledge Graph & Vector Store...")
def load_components():
    graph_mgr = Neo4jGraphManager(
        uri=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE
    )
    graph_mgr.ingest_from_csv(str(CSV_DATA_PATH))

    vector_mgr = VectorStoreManager(
        path=QDRANT_PATH,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        model_name=EMBEDDING_MODEL_NAME
    )
    vector_mgr.build_index(str(MONOGRAPHS_DATA_PATH), force_recreate=False)

    agent = BiomedicalAgent(graph_db=graph_mgr, vector_db=vector_mgr)
    return graph_mgr, vector_mgr, agent


graph_mgr, vector_mgr, agent = load_components()

# --- Sidebar ---
st.sidebar.title("🧬 System Architecture")
st.sidebar.markdown(
    "**Hybrid Graph + Vector RAG** orchestrates Neo4j for 100% factual accuracy with Qdrant for semantic scientific context."
)

st.sidebar.subheader("📡 Database Connections")
graph_summary = graph_mgr.get_summary()
vector_summary = vector_mgr.get_summary()

if "Live" in graph_summary.get("mode", ""):
    st.sidebar.success(f"🟢 Neo4j: {graph_summary['mode']}")
else:
    st.sidebar.info(f"🔵 Neo4j: {graph_summary['mode']}")
    st.sidebar.caption("*(Configure NEO4J_URI/PASSWORD in .env for live AuraDB)*")

st.sidebar.success(f"🟢 Qdrant Vector DB: Ready ({vector_summary.get('indexed_monographs_count', 0)} monographs)")

with st.sidebar.expander("⚙️ Knowledge Graph Metrics", expanded=False):
    st.metric("Drugs (:Drug)", graph_summary.get("drugs_count", 0))
    st.metric("Diseases (:Disease)", graph_summary.get("diseases_count", 0))
    st.metric("Symptoms (:Symptom)", graph_summary.get("symptoms_count", 0))
    st.metric("[:TREATS] Relationships", graph_summary.get("treats_relationships", 0))
    st.metric("[:CAUSES_SIDE_EFFECT]", graph_summary.get("side_effect_relationships", 0))

st.sidebar.markdown("---")
st.sidebar.subheader("💡 Sample Questions")
samples = [
    "What drugs treat Type 2 Diabetes?",
    "What side effects does Metformin cause?",
    "How does Metformin work?",
    "What drugs treat Asthma and how does Albuterol work?",
    "What are the indications and side effects of Lisinopril?",
    "Which drugs cause Major Bleeding as a side effect?",
    "Explain the mechanism of action of SGLT2 inhibitors."
]

selected_sample = None
for s in samples:
    if st.sidebar.button(s, key=f"btn_{s}", use_container_width=True):
        selected_sample = s

# --- Main App Layout ---
st.title("🧬 Biomedical & Drug Query Agent")
st.caption(
    "Hybrid Graph + Vector RAG powered by **LangGraph**, **Neo4j** (Cypher), and **Qdrant** (Dense Vector Search)"
)

tab1, tab2, tab3 = st.tabs([
    "🤖 LangGraph Query Agent",
    "🕸️ Knowledge Graph Explorer (Neo4j)",
    "📚 Vector Monographs (Qdrant)"
])

# --- Tab 1: Agent ---
with tab1:
    default_q = selected_sample or "What drugs treat Type 2 Diabetes?"
    query = st.text_input("Enter your clinical or pharmacological question:", value=default_q)

    col_btn, col_clear = st.columns([1, 6])
    run_clicked = col_btn.button("🚀 Run Agent", type="primary")

    if run_clicked or selected_sample:
        with st.spinner("LangGraph orchestrating query across Router, Neo4j, and Qdrant..."):
            result = agent.run(query)

        # Execution Trace Banner
        st.subheader("🧭 LangGraph Orchestrator Execution Trace")
        c1, c2 = st.columns([1, 2])
        with c1:
            route_badge = result["route"].upper()
            if route_badge == "RELATIONAL":
                st.info(f"**Route Selected:** `RELATIONAL (Neo4j Cypher)`")
            elif route_badge == "DESCRIPTIVE":
                st.warning(f"**Route Selected:** `DESCRIPTIVE (Qdrant Vector)`")
            else:
                st.success(f"**Route Selected:** `HYBRID (Graph + Vector)`")

        with c2:
            st.markdown("**LangGraph Execution Path:**")
            for step in result["trace"]:
                st.markdown(f"- `{step}`")

        # If Cypher was executed
        if result.get("cypher_query"):
            with st.expander("⚡ Cypher Query & Graph Results", expanded=(result["route"] in ("relational", "hybrid"))):
                st.code(result["cypher_query"], language="cypher")
                if result.get("graph_facts"):
                    st.dataframe(pd.DataFrame(result["graph_facts"]), use_container_width=True)
                else:
                    st.info("No direct graph relations matched — agent triggered vector fallback.")

        # If Vector Context was retrieved
        if result.get("vector_context"):
            with st.expander("🔬 Qdrant Vector Retrieval Context", expanded=(result["route"] in ("descriptive", "hybrid"))):
                for doc in result["vector_context"]:
                    st.markdown(f"**{doc['drug_name']}** (`{doc['drug_class']}`) — Similarity Score: `{doc['score']:.4f}`")
                    st.markdown(f"> {doc['mechanism_description']}")
                    st.markdown("---")

        # Final Synthesized Output
        st.subheader("📝 Citation-Backed Agent Response")
        st.markdown(result["final_answer"])

# --- Tab 2: Knowledge Graph Explorer ---
with tab2:
    st.subheader("🕸️ Neo4j Knowledge Graph Data")
    st.markdown("Inspect entities and clinical edges (:Drug)-[:TREATS]->(:Disease), (:Drug)-[:CAUSES_SIDE_EFFECT]->(:Symptom)")

    k_col1, k_col2, k_col3 = st.columns(3)
    k_col1.metric("Total Drugs", graph_summary.get("drugs_count", 0))
    k_col2.metric("Total Diseases", graph_summary.get("diseases_count", 0))
    k_col3.metric("Total Symptoms", graph_summary.get("symptoms_count", 0))

    view_type = st.radio("Select View:", ["All Drug Treatments", "All Adverse Side Effects", "Disease Symptoms"], horizontal=True)

    if view_type == "All Drug Treatments":
        treats_data = graph_mgr.execute_cypher("MATCH (d:Drug)-[:TREATS]->(dis:Disease) RETURN d.name AS Drug, d.drug_class AS Class, dis.name AS Disease, dis.category AS Category")
        if treats_data:
            st.dataframe(pd.DataFrame(treats_data), use_container_width=True)
    elif view_type == "All Adverse Side Effects":
        se_data = graph_mgr.execute_cypher("MATCH (d:Drug)-[:CAUSES_SIDE_EFFECT]->(s:Symptom) RETURN d.name AS Drug, d.drug_class AS Class, s.name AS Side_Effect")
        if se_data:
            st.dataframe(pd.DataFrame(se_data), use_container_width=True)
    else:
        sym_data = graph_mgr.execute_cypher("MATCH (dis:Disease)-[:HAS_SYMPTOM]->(s:Symptom) RETURN dis.name AS Disease, dis.category AS Category, s.name AS Symptom")
        if sym_data:
            st.dataframe(pd.DataFrame(sym_data), use_container_width=True)

# --- Tab 3: Qdrant Vector Store Explorer ---
with tab3:
    st.subheader("📚 Qdrant Semantic Drug Monographs")
    st.markdown("Test vector similarity search directly over detailed clinical monographs.")

    search_query = st.text_input("Semantic Search over Monographs:", value="SGLT2 mechanism of action and renal protection")
    if search_query:
        vector_hits = vector_mgr.search(search_query, top_k=4)
        for hit in vector_hits:
            with st.expander(f"💊 {hit['drug_name']} ({hit['drug_class']}) — Score: {hit['score']:.4f}", expanded=True):
                st.markdown(hit["pharmacology_summary"])
                st.caption(f"Citations: {', '.join(hit.get('citations', []))}")

