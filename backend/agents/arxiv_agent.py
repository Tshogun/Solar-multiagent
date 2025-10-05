"""
ArXiv Agent
Searches and retrieves academic papers from ArXiv
"""

from typing import List, Dict, Any
import arxiv

from backend.agents.base_agent import BaseAgent
from backend.models import AgentType, AgentResponse, DocumentChunk
from backend.config import settings


class ArXivAgent(BaseAgent):
    """Agent for ArXiv paper search and retrieval"""
    
    def __init__(self):
        super().__init__(AgentType.ARXIV, "ArXiv Agent")
        self.max_results = settings.ARXIV_MAX_RESULTS
        self.client = arxiv.Client()
    
    async def initialize(self) -> bool:
        """Initialize the ArXiv agent"""
        try:
            self.log_action("initialized", {"max_results": self.max_results})
            self.initialized = True
            return True
        except Exception as e:
            self.log_action("initialization_failed", {"error": str(e)})
            return False
    
    async def search_arxiv(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Search ArXiv for papers
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            List of paper information dictionaries
        """
        max_results = max_results or self.max_results
        
        try:
            # Create search
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            results = []
            
            # Fetch results
            for paper in self.client.results(search):
                paper_info = {
                    "title": paper.title,
                    "authors": [author.name for author in paper.authors],
                    "summary": paper.summary,
                    "published": paper.published.strftime("%Y-%m-%d"),
                    "updated": paper.updated.strftime("%Y-%m-%d") if paper.updated else None,
                    "pdf_url": paper.pdf_url,
                    "arxiv_id": paper.entry_id.split("/")[-1],
                    "primary_category": paper.primary_category,
                    "categories": paper.categories,
                    "doi": paper.doi
                }
                results.append(paper_info)
            
            self.log_action("arxiv_search_completed", {
                "query": query,
                "num_results": len(results)
            })
            
            return results
            
        except Exception as e:
            self.log_action("arxiv_search_failed", {"error": str(e)})
            return []
    
    async def format_paper_summary(self, paper: Dict[str, Any]) -> str:
        """
        Format paper information into a readable summary
        
        Args:
            paper: Paper information dictionary
        
        Returns:
            Formatted summary string
        """
        authors = ", ".join(paper["authors"][:3])
        if len(paper["authors"]) > 3:
            authors += " et al."
        
        summary = f"""Title: {paper['title']}
Authors: {authors}
Published: {paper['published']}
ArXiv ID: {paper['arxiv_id']}
Category: {paper['primary_category']}

Abstract:
{paper['summary']}

PDF: {paper['pdf_url']}"""
        
        return summary
    
    async def search_and_format(self, query: str) -> List[DocumentChunk]:
        """
        Search ArXiv and return results as DocumentChunks
        
        Args:
            query: Search query
        
        Returns:
            List of DocumentChunk objects
        """
        # Perform search
        papers = await self.search_arxiv(query)
        
        if not papers:
            return []
        
        # Convert to DocumentChunks
        chunks = []
        for i, paper in enumerate(papers):
            # Format paper as content
            content = await self.format_paper_summary(paper)
            
            chunk = DocumentChunk(
                content=content,
                source=paper['pdf_url'],
                score=1.0 - (i * 0.1),  # Decreasing score based on recency
                metadata={
                    "title": paper['title'],
                    "authors": paper['authors'],
                    "arxiv_id": paper['arxiv_id'],
                    "published": paper['published'],
                    "category": paper['primary_category'],
                    "pdf_url": paper['pdf_url'],
                    "rank": i + 1
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    async def process(self, query: str, **kwargs) -> AgentResponse:
        """
        Process an ArXiv search query
        
        Args:
            query: Search query
            **kwargs: Additional parameters
        
        Returns:
            AgentResponse with paper results
        """
        try:
            max_results = kwargs.get("max_results", self.max_results)
            
            # Perform search and get results
            chunks = await self.search_and_format(query)
            
            if not chunks:
                return AgentResponse(
                    agent_type=self.agent_type,
                    success=False,
                    error="No ArXiv papers found for the query.",
                    retrieved_docs=[]
                )
            
            # Prepare response data
            data = {
                "num_results": len(chunks),
                "papers": [
                    {
                        "title": chunk.metadata.get("title", ""),
                        "arxiv_id": chunk.metadata.get("arxiv_id", ""),
                        "published": chunk.metadata.get("published", "")
                    }
                    for chunk in chunks
                ]
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
        agent = ArXivAgent()
        await agent.initialize()
        
        # Test search
        response = await agent.execute("large language models transformers")
        print(f"Success: {response.success}")
        print(f"Retrieved papers: {len(response.retrieved_docs)}")
        
        if response.retrieved_docs:
            print("\nTop papers:")
            for i, doc in enumerate(response.retrieved_docs[:3], 1):
                print(f"\n{i}. {doc.metadata.get('title', 'No title')}")
                print(f"   ArXiv ID: {doc.metadata.get('arxiv_id', 'N/A')}")
                print(f"   Published: {doc.metadata.get('published', 'N/A')}")
    
    # Run the test function
    asyncio.run(test_agent())