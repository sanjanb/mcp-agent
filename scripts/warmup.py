"""
Warm-up script to pre-initialize embeddings, vector index, and the LLM provider.
Run this once before starting the Streamlit app to reduce first-response latency.

Usage (PowerShell):
  python scripts/warmup.py
"""
import os
import sys
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from tools.policy_rag.mcp_tool import PolicySearchTool
from tools.policy_rag.rag_engine import RAGEngine


def main():
    print("[warmup] Starting warm-up...")
    # Initialize components
    try:
        tool = PolicySearchTool()
        # Touch the index
        _ = tool.search_policies("policy", top_k=1)
        print("[warmup] Vector DB warmed")
    except Exception as e:
        print(f"[warmup] Vector DB warm-up skipped: {e}")

    try:
        rag = RAGEngine()
        if getattr(rag, 'active_provider', None):
            # low token, low latency ping
            rag.set_low_latency(True)
            _ = rag.generate_response("warmup", [], conversation_history=[], conversation_summary="Initializing session")
            print(f"[warmup] LLM provider warmed: {rag.get_active_model()}")
        else:
            print("[warmup] No LLM provider configured; skipping LLM warm-up")
    except Exception as e:
        print(f"[warmup] LLM warm-up skipped: {e}")

    print("[warmup] Done.")


if __name__ == "__main__":
    main()
