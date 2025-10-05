"""
Base Agent Class
All specialized agents inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
import time
from datetime import datetime

from backend.models import AgentType, AgentResponse


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, agent_type: AgentType, name: str):
        self.agent_type = agent_type
        self.name = name
        self.initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize agent resources (models, connections, etc.)
        Returns True if successful
        """
        pass
    
    @abstractmethod
    async def process(self, query: str, **kwargs) -> AgentResponse:
        """
        Process a query and return response
        
        Args:
            query: User query string
            **kwargs: Additional parameters specific to agent
        
        Returns:
            AgentResponse with results or error
        """
        pass
    
    async def execute(self, query: str, **kwargs) -> AgentResponse:
        """
        Execute the agent with timing and error handling
        
        Args:
            query: User query
            **kwargs: Additional parameters
        
        Returns:
            AgentResponse with execution details
        """
        start_time = time.time()
        
        try:
            # Ensure agent is initialized
            if not self.initialized:
                await self.initialize()
            
            # Process the query
            response = await self.process(query, **kwargs)
            response.execution_time = time.time() - start_time
            
            return response
            
        except Exception as e:
            # Handle errors gracefully
            execution_time = time.time() - start_time
            return AgentResponse(
                agent_type=self.agent_type,
                success=False,
                error=f"{self.name} error: {str(e)}",
                execution_time=execution_time
            )
    
    def log_action(self, action: str, details: Dict[str, Any] = None):
        """Log agent actions for debugging"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "action": action,
            "details": details or {}
        }
        print(f"[{self.name}] {action}: {details}")
    
    async def cleanup(self):
        """Cleanup resources when agent is done"""
        self.log_action("cleanup", {"status": "completed"})
    
    def __str__(self):
        return f"{self.name} ({self.agent_type})"
    
    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name} initialized={self.initialized}>"