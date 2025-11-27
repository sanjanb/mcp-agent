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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """Retrieval Augmented Generation engine for HR questions."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.1
    ):
        """
        Initialize the RAG engine.
        
        Args:
            api_key: OpenAI API key (or from environment)
            model: OpenAI model to use
            max_tokens: Maximum tokens in response
            temperature: Creativity/randomness (0.0 = deterministic)
        """
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize OpenAI client
        if OpenAI is None:
            logger.warning("OpenAI library not available. Install with: pip install openai")
            self.client = None
        else:
            api_key = api_key or os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("No OpenAI API key provided. Set OPENAI_API_KEY environment variable.")
                self.client = None
            else:
                self.client = OpenAI(api_key=api_key)
                logger.info(f"RAG Engine initialized with model: {model}")
    
    def create_rag_prompt(
        self, 
        user_question: str, 
        retrieved_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
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
        
        # Add conversation history if provided
        history_text = ""
        if conversation_history:
            history_sections = ["=== CONVERSATION HISTORY ==="]
            for turn in conversation_history[-3:]:  # Last 3 turns
                role = turn.get('role', 'unknown')
                content = turn.get('content', '')
                history_sections.append(f"{role.upper()}: {content}")
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
    
    def generate_response(
        self, 
        user_question: str, 
        retrieved_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using RAG with LLM.
        
        Args:
            user_question: The user's question
            retrieved_chunks: Retrieved document chunks
            conversation_history: Optional conversation context
            
        Returns:
            Dictionary with response and metadata
        """
        logger.info(f"Generating RAG response for: '{user_question[:50]}...'")
        
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not available. Check API key and installation.",
                "response": "I'm sorry, I cannot process your request right now. Please contact HR directly.",
                "chunks_used": retrieved_chunks,
                "question": user_question
            }
        
        try:
            # Create prompt
            prompt = self.create_rag_prompt(user_question, retrieved_chunks, conversation_history)
            
            # Call OpenAI
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Extract response
            response_text = completion.choices[0].message.content.strip()
            
            # Calculate response metadata
            tokens_used = completion.usage.total_tokens if hasattr(completion, 'usage') else 0
            
            result = {
                "success": True,
                "response": response_text,
                "question": user_question,
                "chunks_used": len(retrieved_chunks),
                "chunks_details": retrieved_chunks,
                "model": self.model,
                "tokens_used": tokens_used,
                "timestamp": datetime.now().isoformat(),
                "has_citations": "[Doc:" in response_text or "Page:" in response_text
            }
            
            logger.info(f"RAG response generated successfully ({tokens_used} tokens)")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate RAG response: {e}")
            
            # Provide a helpful fallback response with the retrieved information
            fallback_response = self.generate_fallback_response(user_question, retrieved_chunks)
            
            return {
                "success": True,  # Mark as success since we're providing useful info
                "response": fallback_response,
                "question": user_question,
                "chunks_used": len(retrieved_chunks),
                "chunks_details": retrieved_chunks,
                "model": "fallback_mode",
                "tokens_used": 0,
                "timestamp": datetime.now().isoformat(),
                "has_citations": True,
                "mode": "fallback",
                "note": "Response generated using fallback mode due to OpenAI API issue"
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
        logger.info(f"Generating simple response for: '{user_question[:50]}...'")
        
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not available",
                "response": "I'm sorry, I cannot process your request right now. Please contact HR directly."
            }
        
        try:
            simple_prompt = f"""You are an HR assistant. The user asked: "{user_question}"

Since I don't have access to specific company policy documents right now, I cannot provide detailed policy information. Please respond helpfully by:
1. Acknowledging their question
2. Explaining that you need access to current policy documents
3. Suggesting they contact HR directly for accurate information
4. Being professional and helpful

Keep the response brief and professional."""
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": simple_prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            return {
                "success": True,
                "response": response_text,
                "question": user_question,
                "mode": "simple",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate simple response: {e}")
            return {
                "success": False,
                "error": str(e),
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
        self.max_history = max_history
        logger.info("Conversation Manager initialized")
    
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