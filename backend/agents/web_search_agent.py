"""
Web Search Agent
Performs real-time web searches using SerpAPI or DuckDuckGo
"""

from typing import List, Dict, Any
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import os

from backend.agents.base_agent import BaseAgent
from backend.models import AgentType, AgentResponse, DocumentChunk
from backend.config import settings


class WebSearchAgent(BaseAgent):
    """Agent for web search and content retrieval"""
    
    def __init__(self):
        super().__init__(AgentType.WEB_SEARCH, "Web Search Agent")
        self.max_results = settings.WEB_SEARCH_RESULTS
        self.serpapi_key = settings.SERPAPI_KEY
        self.use_serpapi = bool(self.serpapi_key)
    
    async def initialize(self) -> bool:
        """Initialize the web search agent"""
        try:
            search_method = "SerpAPI" if self.use_serpapi else "DuckDuckGo"
            self.log_action("initialized", {
                "max_results": self.max_results,
                "search_method": search_method
            })
            self.initialized = True
            return True
        except Exception as e:
            self.log_action("initialization_failed", {"error": str(e)})
            return False
    
    async def search_serpapi(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Perform web search using SerpAPI (Google Search)
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of search results
        """
        max_results = max_results or self.max_results
        
        try:
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": self.serpapi_key,
                "num": max_results,
                "engine": "google"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Parse organic results
            for result in data.get("organic_results", [])[:max_results]:
                results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "source": "Google (SerpAPI)"
                })
            
            self.log_action("serpapi_search_completed", {
                "query": query,
                "num_results": len(results)
            })
            
            return results
            
        except Exception as e:
            self.log_action("serpapi_search_failed", {"error": str(e)})
            return []
    
    async def search_duckduckgo(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Perform web search using DuckDuckGo (fallback)
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of search results
        """
        max_results = max_results or self.max_results
        
        import time
        
        for attempt in range(2):  # Try twice
            try:
                with DDGS() as ddgs:
                    results = []
                    search_results = ddgs.text(query, max_results=max_results)
                    
                    for result in search_results:
                        results.append({
                            "title": result.get("title", ""),
                            "link": result.get("link", ""),
                            "snippet": result.get("body", ""),
                            "source": "DuckDuckGo"
                        })
                    
                    self.log_action("duckduckgo_search_completed", {
                        "query": query,
                        "num_results": len(results)
                    })
                    
                    return results
                    
            except Exception as e:
                if "Ratelimit" in str(e) and attempt < 1:
                    wait_time = 3
                    self.log_action("rate_limit_retry", {
                        "attempt": attempt + 1,
                        "wait": wait_time
                    })
                    time.sleep(wait_time)
                else:
                    self.log_action("duckduckgo_search_failed", {"error": str(e)})
                    return []
        
        return []
    
    async def search_web(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Perform web search using best available method
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of search results with title, link, snippet
        """
        # Try SerpAPI first if available
        if self.use_serpapi:
            results = await self.search_serpapi(query, max_results)
            if results:
                return results
            # If SerpAPI fails, fall back to DuckDuckGo
            self.log_action("serpapi_fallback_to_duckduckgo", {})
        
        # Use DuckDuckGo (default or fallback)
        return await self.search_duckduckgo(query, max_results)
    
    async def fetch_content(self, url: str, max_length: int = 2000) -> str:
        """
        Fetch and extract text content from a URL
        
        Args:
            url: URL to fetch
            max_length: Maximum content length
        
        Returns:
            Extracted text content
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Truncate if too long
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
            
        except Exception as e:
            self.log_action("fetch_content_failed", {"url": url, "error": str(e)})
            return ""
    
    async def search_and_summarize(self, query: str) -> List[DocumentChunk]:
        """
        Search web and return results as DocumentChunks
        
        Args:
            query: Search query
        
        Returns:
            List of DocumentChunk objects
        """
        # Perform search
        results = await self.search_web(query)
        
        if not results:
            return []
        
        # Convert to DocumentChunks
        chunks = []
        for i, result in enumerate(results):
            # Combine title and snippet for content
            content = f"{result['title']}\n\n{result['snippet']}"
            
            chunk = DocumentChunk(
                content=content,
                source=result['link'],
                score=1.0 - (i * 0.1),  # Decreasing score based on rank
                metadata={
                    "title": result['title'],
                    "url": result['link'],
                    "search_engine": result['source'],
                    "rank": i + 1
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    async def process(self, query: str, **kwargs) -> AgentResponse:
        """
        Process a web search query
        
        Args:
            query: Search query
            **kwargs: Additional parameters
        
        Returns:
            AgentResponse with search results
        """
        try:
            max_results = kwargs.get("max_results", self.max_results)
            
            # Perform search and get results
            chunks = await self.search_and_summarize(query)
            
            if not chunks:
                return AgentResponse(
                    agent_type=self.agent_type,
                    success=False,
                    error="No web search results found.",
                    retrieved_docs=[]
                )
            
            # Prepare response data
            data = {
                "num_results": len(chunks),
                "sources": [chunk.metadata.get("url", "") for chunk in chunks]
            }
            
            return AgentResponse(
                agent_type=self.agent_type,
                success=True,
                data=data,
                retrieved_docs=chunks
            )
            
        except Exception as e:
            self.log_action("process_error", {"error": str(e)})
            return AgentResponse(
                agent_type=self.agent_type,
                success=False,
                error=str(e),
                retrieved_docs=[]
            )


if __name__ == "__main__":
    import asyncio
    
    async def test_agent():
        agent = WebSearchAgent()
        await agent.initialize()
        
        # Test search
        response = await agent.execute("latest developments in artificial intelligence 2025")
        print(f"Success: {response.success}")
        print(f"Retrieved docs: {len(response.retrieved_docs)}")
        
        if response.retrieved_docs:
            print("\nTop results:")
            for i, doc in enumerate(response.retrieved_docs[:3], 1):
                print(f"\n{i}. {doc.metadata.get('title', 'No title')}")
                print(f"   URL: {doc.source}")
                print(f"   Snippet: {doc.content[:150]}...")
    
    asyncio.run(test_agent())