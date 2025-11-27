"""
RAG (Retrieval Augmented Generation) module for HR Agent.
Handles LLM integration and prompt templates for grounded Q&A.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# OpenAI integration
try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None
    OpenAI = None

# Gemini integration
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """Retrieval Augmented Generation engine for HR questions with multi-provider support."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        provider: str = "auto",
        model: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.1
    ):
        """
        Initialize the RAG engine with multi-provider support.
        
        Args:
            openai_api_key: OpenAI API key (or from environment)
            gemini_api_key: Gemini API key (or from environment)
            provider: LLM provider - "openai", "gemini", or "auto"
            model: Model name (provider-specific defaults if None)
            max_tokens: Maximum tokens in response
            temperature: Creativity/randomness (0.0 = deterministic)
        """
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.provider = provider or os.getenv('LLM_PROVIDER', 'auto')
        self.low_latency = False
        
        # Initialize clients
        self.openai_client = None
        self.gemini_client = None
        self.active_provider = None
        
        # Setup OpenAI
        if OpenAI is not None:
            openai_key = openai_api_key or os.getenv('OPENAI_API_KEY')
            if openai_key and openai_key != "your_openai_api_key_here":
                try:
                    self.openai_client = OpenAI(api_key=openai_key)
                    self.openai_model = model or "gpt-3.5-turbo"
                    logger.info(f"OpenAI client initialized with model: {self.openai_model}")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Setup Gemini
        if genai is not None:
            gemini_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
            if gemini_key and gemini_key != "your_gemini_api_key_here":
                try:
                    genai.configure(api_key=gemini_key)
                    self.gemini_model = model or os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
                    self.gemini_client = genai.GenerativeModel(self.gemini_model)
                    logger.info(f"Gemini client initialized with model: {self.gemini_model}")
                except Exception as e:
                    logger.warning(f"Failed to initialize Gemini client: {e}")
        
        # Determine active provider based on availability and preference
        self._select_active_provider()
    
    def _select_active_provider(self):
        """Select the active LLM provider based on availability and configuration."""
        if self.provider == "openai" and self.openai_client:
            self.active_provider = "openai"
        elif self.provider == "gemini" and self.gemini_client:
            self.active_provider = "gemini"
        elif self.provider == "auto":
            # Auto mode: prefer OpenAI, fallback to Gemini
            if self.openai_client:
                self.active_provider = "openai"
            elif self.gemini_client:
                self.active_provider = "gemini"
            else:
                self.active_provider = None
        else:
            self.active_provider = None
        
        if self.active_provider:
            logger.info(f"Active LLM provider: {self.active_provider}")
        else:
            logger.warning("No LLM provider available. Running in fallback mode.")

    def set_provider(self, provider: str):
        """Update the preferred provider and reselect active provider."""
        provider = (provider or "").lower()
        if provider not in ("openai", "gemini", "auto"):
            raise ValueError("provider must be 'openai', 'gemini', or 'auto'")
        self.provider = provider
        self._select_active_provider()

    def set_low_latency(self, enabled: bool):
        """Toggle low-latency mode for faster responses."""
        self.low_latency = bool(enabled)
    
    def get_active_model(self) -> str:
        """Get the currently active model name."""
        if self.active_provider == "openai":
            return self.openai_model
        elif self.active_provider == "gemini":
            return self.gemini_model
        else:
            return "fallback_mode"
    
    def create_rag_prompt(
        self, 
        user_question: str, 
        retrieved_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        conversation_summary: Optional[str] = None
    ) -> str:
        """
        Create a RAG prompt with retrieved context and user question.
        
        Args:
            user_question: The user's HR question
            retrieved_chunks: Relevant document chunks from vector search
            conversation_history: Optional previous conversation context
            
        Returns:
            Formatted prompt for the LLM
        """
        # System prompt
        system_prompt = """You are an expert HR assistant helping employees with company policy questions.

IMPORTANT GUIDELINES:
1. Answer ONLY based on the provided document context
2. If the answer is not in the provided documents, say "I don't have enough information in the policy documents to answer that question"
3. Always include citations in your response using [Doc: filename, Page: X] format
4. Be helpful but precise - don't make assumptions beyond what's written
5. If policies seem unclear, suggest the employee contact HR for clarification

Your responses should be:
- Professional and helpful
- Based only on provided evidence
- Include specific citations
- Clear about any limitations or gaps in information"""
        
        # Build context from retrieved chunks
        context_sections = []
        if retrieved_chunks:
            context_sections.append("=== RELEVANT POLICY DOCUMENTS ===")
            
            for i, chunk in enumerate(retrieved_chunks, 1):
                filename = chunk.get('filename', 'Unknown')
                page = chunk.get('page', 'Unknown')
                text = chunk.get('text', '').strip()
                score = chunk.get('score', 0.0)
                
                context_sections.append(f"\nDocument {i}:")
                context_sections.append(f"Source: {filename}, Page: {page}")
                context_sections.append(f"Relevance: {score:.2f}")
                context_sections.append(f"Content: {text}")
                context_sections.append("-" * 50)
        else:
            context_sections.append("=== NO RELEVANT DOCUMENTS FOUND ===")
            context_sections.append("No policy documents were found that match your question.")
        
        context = "\n".join(context_sections)
        
        # Add conversation summary and recent history if provided
        history_text = ""
        history_sections: List[str] = []
        if conversation_summary:
            history_sections.append("=== CONVERSATION SUMMARY ===")
            history_sections.append(conversation_summary.strip())
        if conversation_history:
            history_sections.append("=== RECENT TURNS ===")
            for turn in conversation_history[-2:]:  # Last 2 turns for recency
                role = turn.get('role', 'unknown')
                content = turn.get('content', '')
                history_sections.append(f"{role.upper()}: {content}")
        if history_sections:
            history_text = "\n".join(history_sections) + "\n\n"
        
        # Combine into final prompt
        user_prompt = f"""{history_text}{context}

=== EMPLOYEE QUESTION ===
{user_question}

=== YOUR RESPONSE ===
Please provide a helpful answer based on the policy documents above. Remember to include citations and be clear about any limitations."""
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        logger.info(f"Created RAG prompt with {len(retrieved_chunks)} chunks for question: '{user_question[:50]}...'")
        return full_prompt
    
    def _generate_openai_response(self, prompt: str) -> Dict[str, Any]:
        """Generate response using OpenAI API."""
        try:
            completion = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            response_text = completion.choices[0].message.content.strip()
            tokens_used = completion.usage.total_tokens if hasattr(completion, 'usage') else 0
            
            return {
                "success": True,
                "response": response_text,
                "model": self.openai_model,
                "provider": "openai",
                "tokens_used": tokens_used
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                "success": False,
                "error": f"OpenAI API error: {str(e)}",
                "provider": "openai"
            }
    
    def _generate_gemini_response(self, prompt: str) -> Dict[str, Any]:
        """Generate response using Gemini API."""
        try:
            response = self.gemini_client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
            )
            
            response_text = response.text.strip()
            
            # Gemini doesn't provide token usage in the same way
            estimated_tokens = len(response_text.split()) * 1.3  # Rough estimate
            
            return {
                "success": True,
                "response": response_text,
                "model": self.gemini_model,
                "provider": "gemini",
                "tokens_used": int(estimated_tokens)
            }
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {
                "success": False,
                "error": f"Gemini API error: {str(e)}",
                "provider": "gemini"
            }
    
    def _try_llm_response(self, prompt: str) -> Dict[str, Any]:
        """Try to generate response with available LLM providers."""
        results = []
        
        # Try the configured provider first
        if self.active_provider == "openai":
            result = self._generate_openai_response(prompt)
            if result["success"]:
                return result
            results.append(result)
            
            # If OpenAI fails and Gemini is available, try Gemini
            if self.gemini_client:
                logger.info("OpenAI failed, trying Gemini as fallback...")
                result = self._generate_gemini_response(prompt)
                if result["success"]:
                    return result
                results.append(result)
                
        elif self.active_provider == "gemini":
            result = self._generate_gemini_response(prompt)
            if result["success"]:
                return result
            results.append(result)
            
            # If Gemini fails and OpenAI is available, try OpenAI
            if self.openai_client:
                logger.info("Gemini failed, trying OpenAI as fallback...")
                result = self._generate_openai_response(prompt)
                if result["success"]:
                    return result
                results.append(result)
        
        # All providers failed
        error_details = "; ".join([f"{r['provider']}: {r.get('error', 'Unknown error')}" for r in results])
        return {
            "success": False,
            "error": f"All LLM providers failed. {error_details}",
            "provider": "none",
            "attempts": results
        }
    def generate_response(
        self, 
        user_question: str, 
        retrieved_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        conversation_summary: Optional[str] = None,
        low_latency: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using RAG with multi-provider LLM support.
        
        Args:
            user_question: The user's question
            retrieved_chunks: Retrieved document chunks
            conversation_history: Optional conversation context
            
        Returns:
            Dictionary with response and metadata
        """
        logger.info(f"Generating RAG response for: '{user_question[:50]}...' using {self.active_provider or 'fallback'}")
        
        # Create prompt
        prompt = self.create_rag_prompt(
            user_question, retrieved_chunks, conversation_history, conversation_summary
        )
        
        # Try LLM providers
        if self.active_provider:
            # In low-latency mode, prefer faster/cheaper models and fewer tokens
            use_low_latency = self.low_latency if low_latency is None else bool(low_latency)
            original_openai_model = getattr(self, 'openai_model', None)
            original_gemini_model = getattr(self, 'gemini_model', None)
            original_max_tokens = self.max_tokens
            original_temperature = self.temperature

            try:
                if use_low_latency:
                    self.max_tokens = min(self.max_tokens, int(os.getenv('LOW_LATENCY_MAX_TOKENS', '350')))
                    self.temperature = float(os.getenv('LOW_LATENCY_TEMPERATURE', '0.0'))
                    # Swap to fast models if available
                    if self.active_provider == 'openai' and original_openai_model is not None:
                        fast_om = os.getenv('FAST_OPENAI_MODEL')
                        if fast_om:
                            self.openai_model = fast_om
                    if self.active_provider == 'gemini' and original_gemini_model is not None:
                        fast_gm = os.getenv('FAST_GEMINI_MODEL', 'gemini-1.5-flash')
                        # Only override if model exists setting
                        if fast_gm:
                            self.gemini_model = fast_gm

                llm_result = self._try_llm_response(prompt)
            finally:
                # Restore settings
                self.max_tokens = original_max_tokens
                self.temperature = original_temperature
                if original_openai_model is not None:
                    self.openai_model = original_openai_model
                if original_gemini_model is not None:
                    self.gemini_model = original_gemini_model
            
            if llm_result["success"]:
                # LLM response successful
                result = {
                    "success": True,
                    "response": llm_result["response"],
                    "question": user_question,
                    "chunks_used": len(retrieved_chunks),
                    "chunks_details": retrieved_chunks,
                    "model": llm_result["model"],
                    "provider": llm_result["provider"],
                    "tokens_used": llm_result["tokens_used"],
                    "timestamp": datetime.now().isoformat(),
                    "has_citations": "[Doc:" in llm_result["response"] or "Page:" in llm_result["response"]
                }
                
                logger.info(f"RAG response generated successfully using {llm_result['provider']} ({llm_result['tokens_used']} tokens)")
                return result
            else:
                logger.warning(f"LLM providers failed: {llm_result.get('error', 'Unknown error')}")
        
            # Fallback mode - use retrieved chunks only
        fallback_response = self.generate_fallback_response(user_question, retrieved_chunks)
        
        return {
            "success": True,
            "response": fallback_response,
            "question": user_question,
            "chunks_used": len(retrieved_chunks),
            "chunks_details": retrieved_chunks,
            "model": "fallback_mode",
            "provider": "fallback",
            "tokens_used": 0,
            "timestamp": datetime.now().isoformat(),
            "has_citations": True,
            "mode": "fallback",
            "note": "Response generated using fallback mode due to LLM provider issues"
        }
    
    def generate_fallback_response(
        self, 
        user_question: str, 
        retrieved_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a fallback response using retrieved chunks without LLM.
        
        Args:
            user_question: The user's question
            retrieved_chunks: Retrieved document chunks
            
        Returns:
            Formatted response string with citations
        """
        logger.info(f"Generating fallback response for: '{user_question[:50]}...'")
        
        if not retrieved_chunks:
            return f"""I found your question about "{user_question}" but I don't have access to relevant policy documents right now.

**Please contact HR directly for accurate information about:**
- Company policies
- Benefits and leave
- Procedures and requirements

**Contact Information:**
- HR Department
- Email: hr@company.com
- Phone: (555) 123-4567

I apologize that I cannot provide specific policy details at this moment."""

        # Build response with retrieved information
        response_parts = [
            f"Based on the available policy documents, here's what I found regarding your question: \"{user_question}\"",
            "",
            "**Relevant Policy Information:**"
        ]
        
        for i, chunk in enumerate(retrieved_chunks[:3], 1):  # Limit to top 3 chunks
            filename = chunk.get('filename', 'Unknown Document')
            page = chunk.get('page', 'Unknown')
            text = chunk.get('text', '').strip()
            score = chunk.get('score', 0.0)
            
            response_parts.extend([
                f"",
                f"**Source {i}:** {filename} (Page {page}, Relevance: {score:.2f})",
                f"{text}",
                f"",
                f"---"
            ])
        
        response_parts.extend([
            "",
            "**Important Note:**",
            "This response was generated using document search only. For complete and current policy information, please:",
            "- Contact HR directly for clarification",
            "- Refer to the complete policy documents", 
            "- Verify any specific requirements or procedures",
            "",
            "**HR Contact:** hr@company.com | (555) 123-4567"
        ])
        
        return "\n".join(response_parts)
    
    def generate_simple_response(self, user_question: str) -> Dict[str, Any]:
        """
        Generate a simple response without retrieval (fallback mode).
        
        Args:
            user_question: The user's question
            
        Returns:
            Dictionary with response
        """
        logger.info(f"Generating simple response for: '{user_question[:50]}...' using {self.active_provider or 'fallback'}")
        
        if not self.active_provider:
            return {
                "success": False,
                "error": "No LLM provider available",
                "response": "I'm sorry, I cannot process your request right now. Please contact HR directly."
            }
        
        simple_prompt = f"""You are an HR assistant. The user asked: "{user_question}"

Since I don't have access to specific company policy documents right now, I cannot provide detailed policy information. Please respond helpfully by:
1. Acknowledging their question
2. Explaining that you need access to current policy documents
3. Suggesting they contact HR directly for accurate information
4. Being professional and helpful

Keep the response brief and professional."""
        
        llm_result = self._try_llm_response(simple_prompt)
        
        if llm_result["success"]:
            return {
                "success": True,
                "response": llm_result["response"],
                "question": user_question,
                "model": llm_result["model"],
                "provider": llm_result["provider"],
                "mode": "simple",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": llm_result.get("error", "LLM providers failed"),
                "response": "I apologize, but I'm unable to process your question right now. Please contact HR directly for assistance."
            }


class ConversationManager:
    """Manages conversation history and context."""
    
    def __init__(self, max_history: int = 10):
        """
        Initialize conversation manager.
        
        Args:
            max_history: Maximum number of conversation turns to remember
        """
        self.conversations = {}  # user_id -> conversation history
        self._cache = None
        self.max_history = max_history
        logger.info("Conversation Manager initialized")

    def _get_cache(self):
        """Lazy-load Redis cache or fallback in-memory cache."""
        if self._cache is None:
            try:
                from tools.cache.redis_cache import get_cache
                self._cache = get_cache()
            except Exception as e:
                logger.warning(f"Cache unavailable, using in-memory fallback: {e}")
                class _Dummy:
                    def get_json(self, *a, **k): return None
                    def set_json(self, *a, **k): return None
                    def set_json_ttl(self, *a, **k): return None
                    def delete(self, *a, **k): return None
                self._cache = _Dummy()
        return self._cache
    
    def add_turn(self, user_id: str, role: str, content: str):
        """
        Add a conversation turn.
        
        Args:
            user_id: User identifier
            role: 'user' or 'assistant'
            content: Message content
        """
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        self.conversations[user_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim history if too long
        if len(self.conversations[user_id]) > self.max_history:
            self.conversations[user_id] = self.conversations[user_id][-self.max_history:]
    
    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of conversation turns
        """
        return self.conversations.get(user_id, [])
    
    def clear_history(self, user_id: str):
        """Clear conversation history for user."""
        if user_id in self.conversations:
            del self.conversations[user_id]
            logger.info(f"Cleared conversation history for user {user_id}")
        # also clear cached summary
        cache = self._get_cache()
        try:
            cache.delete(f"conv:summary:{user_id}")
        except Exception:
            pass

    def summarize_history(self, user_id: str, max_chars: int = 600) -> Optional[str]:
        """Create a lightweight summary of the conversation without LLM calls."""
        history = self.get_history(user_id)
        if not history:
            return None
        # Take last ~8 turns for context and compress
        turns = history[-8:]
        parts: List[str] = []
        for t in turns:
            role = t.get('role', 'user')
            content = (t.get('content', '') or '').strip().replace('\n', ' ')
            if not content:
                continue
            prefix = 'Q' if role == 'user' else 'A'
            parts.append(f"{prefix}: {content}")
        s = " \n".join(parts)
        if len(s) > max_chars:
            s = s[:max_chars - 3] + "..."
        return s

    def get_or_update_summary(self, user_id: str, ttl_seconds: int = 1800) -> Optional[str]:
        """Fetch cached summary or compute and cache it for a session."""
        cache = self._get_cache()
        key = f"conv:summary:{user_id}"
        try:
            cached = cache.get_json(key)
            if cached and isinstance(cached, dict) and cached.get('summary'):
                return cached['summary']
        except Exception:
            pass

        summary = self.summarize_history(user_id)
        if summary:
            try:
                cache.set_json_ttl(key, {"summary": summary, "ts": datetime.now().isoformat()}, ttl_seconds)
            except Exception:
                try:
                    cache.set_json(key, {"summary": summary, "ts": datetime.now().isoformat()})
                except Exception:
                    pass
        return summary


# Example usage and testing
if __name__ == "__main__":
    print("\n=== RAG Engine Test ===")
    
    # Initialize RAG engine
    rag = RAGEngine()
    
    # Test prompt creation
    print("\n--- Prompt Creation Test ---")
    
    sample_chunks = [
        {
            "filename": "hr_policy.pdf",
            "page": 5,
            "text": "All employees are entitled to 20 days of paid vacation per year. Vacation requests must be submitted at least 2 weeks in advance.",
            "score": 0.85
        },
        {
            "filename": "benefits_guide.pdf", 
            "page": 12,
            "text": "Sick leave is available for up to 10 days per year. No advance notice required for emergency situations.",
            "score": 0.72
        }
    ]
    
    test_question = "How many vacation days do I get per year?"
    
    prompt = rag.create_rag_prompt(test_question, sample_chunks)
    print("Generated prompt:")
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    
    # Test response generation (only if API key available)
    print("\n--- Response Generation Test ---")
    if rag.client:
        response = rag.generate_response(test_question, sample_chunks)
        print(f"Response generated: {response['success']}")
        if response['success']:
            print(f"Response: {response['response']}")
            print(f"Citations included: {response['has_citations']}")
    else:
        print("OpenAI client not available - skipping response test")
    
    # Test conversation manager
    print("\n--- Conversation Manager Test ---")
    conv_mgr = ConversationManager()
    
    conv_mgr.add_turn("user123", "user", "How many vacation days do I get?")
    conv_mgr.add_turn("user123", "assistant", "You get 20 paid vacation days per year according to company policy.")
    conv_mgr.add_turn("user123", "user", "Do I need to give advance notice?")
    
    history = conv_mgr.get_history("user123")
    print(f"Conversation history has {len(history)} turns")
    for turn in history:
        print(f"  {turn['role']}: {turn['content'][:50]}...")
    
    print("\nRAG Engine test completed")