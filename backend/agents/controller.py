from typing import List, Dict, Any, Tuple
from groq import Groq
import re

from backend.agents.base_agent import BaseAgent
from backend.models import AgentType, AgentResponse, AgentDecision
from backend.config import settings


class ControllerAgent(BaseAgent):
    """Controller agent that routes queries to specialized agents"""
    
    def __init__(self):
        super().__init__(AgentType.CONTROLLER, "Controller Agent")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.LLM_MODEL
    
    async def initialize(self) -> bool:
        """Initialize the controller agent"""
        try:
            # Test Groq connection
            self.log_action("initialized", {"model": self.model})
            self.initialized = True
            return True
        except Exception as e:
            self.log_action("initialization_failed", {"error": str(e)})
            return False
    
    def get_routing_prompt(self, query: str, has_indexed_docs: bool = False) -> str:
        """
        Generate routing prompt for LLM
        
        Args:
            query: User query
            has_indexed_docs: Whether RAG has indexed documents
        
        Returns:
            Prompt string
        """
        prompt = f"""You are a routing agent that decides which specialized agents should handle a user query.

Available agents:
1. PDF_RAG - Retrieves information from indexed PDF documents (knowledge base)
   - Use when: Query asks about specific documents, requires domain knowledge from PDFs, asks to "summarize document"
   - Status: {"AVAILABLE with indexed documents" if has_indexed_docs else "NOT AVAILABLE (no documents indexed)"}

2. WEB_SEARCH - Searches the web for current information
   - Use when: Query needs recent/current information, news, latest developments, real-time data, prices, stocks, weather, scores
   - Use when: Query explicitly mentions "search web", "google", "find online"
   - Status: AVAILABLE

3. ARXIV - Searches academic papers on ArXiv
   - Use when: Query mentions papers, research, academic publications, arxiv, scientific studies
   - Status: AVAILABLE

IMPORTANT ROUTING RULES:
- If query mentions "search web", "google", "online" → ALWAYS use WEB_SEARCH
- If query asks for "price", "stock", "latest", "recent", "current", "today" → use WEB_SEARCH
- If query asks to "summarize document", "according to PDF" → use PDF_RAG (if available)
- If query mentions "paper", "research", "arxiv" → use ARXIV
- You can select MULTIPLE agents if needed
- If PDF_RAG not available, use WEB_SEARCH for factual questions
- When in doubt about current info → use WEB_SEARCH

User Query: "{query}"

Respond in this EXACT format:
AGENTS: [list agent names separated by commas, e.g., WEB_SEARCH, ARXIV]
CONFIDENCE: [number between 0.0 and 1.0]
RATIONALE: [one sentence explaining why these agents were chosen]

Example responses:
AGENTS: WEB_SEARCH
CONFIDENCE: 0.95
RATIONALE: Query asks for current stock price which requires real-time web search.

AGENTS: WEB_SEARCH, ARXIV
CONFIDENCE: 0.9
RATIONALE: Query asks about recent research papers, requiring both web search for context and ArXiv for academic papers.

AGENTS: PDF_RAG
CONFIDENCE: 0.95
RATIONALE: Query asks about content in uploaded documents which can be answered from the knowledge base.

Now respond:"""
        
        return prompt
    
    async def route_with_llm(self, query: str, has_indexed_docs: bool = False) -> AgentDecision:
        """
        Use LLM to decide which agents to call
        
        Args:
            query: User query
            has_indexed_docs: Whether RAG has documents
        
        Returns:
            AgentDecision object
        """
        try:
            prompt = self.get_routing_prompt(query, has_indexed_docs)
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse response
            agents_match = re.search(r'AGENTS:\s*\[?([^\]\n]+)\]?', content, re.IGNORECASE)
            confidence_match = re.search(r'CONFIDENCE:\s*([0-9.]+)', content, re.IGNORECASE)
            rationale_match = re.search(r'RATIONALE:\s*(.+)', content, re.IGNORECASE)
            
            if not agents_match:
                # Fallback to rule-based
                return self.route_with_rules(query, has_indexed_docs)
            
            # Extract agent names
            agents_str = agents_match.group(1).strip()
            agent_names = [name.strip().upper().replace(" ", "_") for name in agents_str.split(',')]
            
            # Map to AgentType
            agents_to_call = []
            for name in agent_names:
                if "PDF" in name or "RAG" in name:
                    if has_indexed_docs:
                        agents_to_call.append(AgentType.PDF_RAG)
                elif "WEB" in name or "SEARCH" in name:
                    agents_to_call.append(AgentType.WEB_SEARCH)
                elif "ARXIV" in name:
                    agents_to_call.append(AgentType.ARXIV)
            
            # Remove duplicates
            agents_to_call = list(dict.fromkeys(agents_to_call))
            
            # If no agents selected, use fallback
            if not agents_to_call:
                return self.route_with_rules(query, has_indexed_docs)
            
            confidence = float(confidence_match.group(1)) if confidence_match else 0.8
            rationale = rationale_match.group(1).strip() if rationale_match else "LLM routing decision"
            
            decision = AgentDecision(
                agents_to_call=agents_to_call,
                rationale=rationale,
                confidence=confidence
            )
            
            self.log_action("llm_routing", {
                "query": query,
                "agents": [a.value for a in agents_to_call],
                "confidence": confidence
            })
            
            return decision
            
        except Exception as e:
            self.log_action("llm_routing_failed", {"error": str(e)})
            # Fallback to rule-based
            return self.route_with_rules(query, has_indexed_docs)
    
    def route_with_rules(self, query: str, has_indexed_docs: bool = False) -> AgentDecision:
        """
        Fallback rule-based routing
        
        Args:
            query: User query
            has_indexed_docs: Whether RAG has documents
        
        Returns:
            AgentDecision object
        """
        query_lower = query.lower()
        agents_to_call = []
        rationale_parts = []
        
        # Check for explicit web search keywords (HIGH PRIORITY)
        web_explicit_keywords = ['search web', 'google search', 'web search', 'search online', 'search internet', 'find online', 'look up online']
        if any(keyword in query_lower for keyword in web_explicit_keywords):
            agents_to_call.append(AgentType.WEB_SEARCH)
            rationale_parts.append("explicit web search requested")
        
        # Check for ArXiv keywords
        arxiv_keywords = ['arxiv', 'paper', 'research', 'publication', 'study', 'academic', 'journal', 'find papers', 'scientific']
        if any(keyword in query_lower for keyword in arxiv_keywords):
            agents_to_call.append(AgentType.ARXIV)
            rationale_parts.append("query mentions research/papers")
        
        # Check for time-sensitive/current information keywords
        web_keywords = ['recent', 'latest', 'current', 'news', 'today', '2024', '2025', 'now', 'price', 'stock', 'weather', 'score', 'live']
        if any(keyword in query_lower for keyword in web_keywords):
            if AgentType.WEB_SEARCH not in agents_to_call:
                agents_to_call.append(AgentType.WEB_SEARCH)
                rationale_parts.append("query asks for recent/current information")
        
        # Check for PDF/document keywords
        doc_keywords = ['document', 'pdf', 'uploaded', 'file', 'knowledge base', 'according to', 'summarize the', 'from the document']
        if any(keyword in query_lower for keyword in doc_keywords) and has_indexed_docs:
            if AgentType.PDF_RAG not in agents_to_call:
                agents_to_call.append(AgentType.PDF_RAG)
                rationale_parts.append("query references documents")
        
        # Default behavior - IMPROVED
        if not agents_to_call:
            # Check if it's a factual/general knowledge question
            general_keywords = ['what is', 'who is', 'explain', 'define', 'how does', 'why']
            is_general = any(keyword in query_lower for keyword in general_keywords)
            
            if is_general and has_indexed_docs:
                # Try RAG first for general questions if docs available
                agents_to_call.append(AgentType.PDF_RAG)
                rationale_parts.append("checking knowledge base for general question")
            else:
                # Default to web search for everything else
                agents_to_call.append(AgentType.WEB_SEARCH)
                rationale_parts.append("default to web search")
        
        rationale = "Rule-based routing: " + ", ".join(rationale_parts)
        
        decision = AgentDecision(
            agents_to_call=agents_to_call,
            rationale=rationale,
            confidence=0.7
        )
        
        self.log_action("rule_based_routing", {
            "query": query,
            "agents": [a.value for a in agents_to_call]
        })
        
        return decision
    
    async def process(self, query: str, **kwargs) -> AgentResponse:
        """
        Process routing decision
        
        Args:
            query: User query
            **kwargs: Additional parameters (has_indexed_docs, use_llm)
        
        Returns:
            AgentResponse with routing decision
        """
        try:
            has_indexed_docs = kwargs.get('has_indexed_docs', False)
            use_llm = kwargs.get('use_llm', True)
            
            # Make routing decision
            if use_llm:
                decision = await self.route_with_llm(query, has_indexed_docs)
            else:
                decision = self.route_with_rules(query, has_indexed_docs)
            
            return AgentResponse(
                agent_type=self.agent_type,
                success=True,
                data=decision.model_dump()
            )
            
        except Exception as e:
            self.log_action("process_error", {"error": str(e)})
            return AgentResponse(
                agent_type=self.agent_type,
                success=False,
                error=str(e)
            )


if __name__ == "__main__":
    import asyncio
    
    async def test_controller():
        controller = ControllerAgent()
        await controller.initialize()
        
        test_queries = [
            "What are recent papers on transformers?",
            "Tell me about the latest AI news",
            "Explain the content in my uploaded PDF",
            "What is machine learning?"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            decision = await controller.route_with_llm(query, has_indexed_docs=True)
            print(f"Agents: {[a.value for a in decision.agents_to_call]}")
            print(f"Rationale: {decision.rationale}")
            print(f"Confidence: {decision.confidence}")
    
    asyncio.run(test_controller())