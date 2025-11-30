import os
import io
from typing import List, Dict, Any

import pdfplumber
import numpy as np
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class ResumeInput(BaseModel):
    filename: str = Field(..., description="Original resume filename")
    content: bytes = Field(..., description="Raw file bytes (PDF or TXT)")


class JobDescriptionInput(BaseModel):
    text: str = Field(..., description="Job description plain text")
    skills: List[str] = Field(default_factory=list, description="Optional list of target skills/keywords")


class RankedCandidate(BaseModel):
    filename: str
    score: float
    top_snippets: List[str]
    matched_skills: List[str]


class ResumeScreeningTool:
    def __init__(self, embedding_model_name: str = os.getenv("RESUME_EMBEDDING_MODEL", "all-MiniLM-L6-v2")):
        self.model = SentenceTransformer(embedding_model_name)

    def _extract_text(self, filename: str, content: bytes) -> str:
        name_lower = filename.lower()
        if name_lower.endswith(".pdf"):
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
            return "\n".join(pages)
        else:
            # treat as text
            try:
                return content.decode("utf-8", errors="ignore")
            except Exception:
                return ""

    def _chunk_text(self, text: str, chunk_size: int = 700, overlap: int = 100) -> List[str]:
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk = words[i:i + chunk_size]
            chunks.append(" ".join(chunk))
            i += chunk_size - overlap
        return chunks

    def _embed(self, texts: List[str]) -> np.ndarray:
        embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings

    def _score_resume(self, resume_text: str, jd_text: str, skills: List[str]) -> Dict[str, Any]:
        jd_chunks = [jd_text]
        resume_chunks = self._chunk_text(resume_text)
        if not resume_chunks:
            resume_chunks = [resume_text]

        jd_vec = self._embed(jd_chunks)
        res_vecs = self._embed(resume_chunks)
        sims = cosine_similarity(res_vecs, jd_vec)[:, 0]
        # overall score: mean of top-k chunk similarities
        top_k = min(5, len(sims))
        top_indices = np.argsort(sims)[-top_k:][::-1]
        top_snippets = [resume_chunks[i][:500] for i in top_indices]
        base_score = float(np.mean(sims[top_indices])) if top_indices.size > 0 else 0.0

        # skill match bonus: proportion of skills found
        resume_lower = resume_text.lower()
        matched = [s for s in skills if s.lower() in resume_lower] if skills else []
        skill_ratio = (len(matched) / max(1, len(skills))) if skills else 0.0
        final_score = base_score + 0.1 * skill_ratio

        return {
            "score": final_score,
            "top_snippets": top_snippets,
            "matched_skills": matched,
        }

    def rank_resumes(self, resumes: List[ResumeInput], jd: JobDescriptionInput) -> List[RankedCandidate]:
        results: List[RankedCandidate] = []
        for r in resumes:
            text = self._extract_text(r.filename, r.content)
            if not text.strip():
                results.append(RankedCandidate(filename=r.filename, score=0.0, top_snippets=[], matched_skills=[]))
                continue
            scored = self._score_resume(text, jd.text, jd.skills)
            results.append(RankedCandidate(
                filename=r.filename,
                score=scored["score"],
                top_snippets=scored["top_snippets"],
                matched_skills=scored["matched_skills"],
            ))
        results.sort(key=lambda c: c.score, reverse=True)
        return results


# Minimal MCP glue (callable functions)
tool_instance: ResumeScreeningTool | None = None


def get_tool() -> ResumeScreeningTool:
    global tool_instance
    if tool_instance is None:
        tool_instance = ResumeScreeningTool()
    return tool_instance


def mcp_rank_resumes(resumes: List[Dict[str, Any]], jd: Dict[str, Any]) -> List[Dict[str, Any]]:
    """MCP-exposed function: rank resumes against a job description.

    resumes: [{ filename: str, content: base64 or bytes }]
    jd: { text: str, skills?: [str] }
    """
    # Convert to models
    res_models = [ResumeInput(filename=r["filename"], content=r["content"]) for r in resumes]
    jd_model = JobDescriptionInput(text=jd.get("text", ""), skills=jd.get("skills", []))
    ranked = get_tool().rank_resumes(res_models, jd_model)
    return [c.model_dump() for c in ranked]
