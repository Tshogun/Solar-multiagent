"""
Logging Utilities
Handles logging of agent decisions and system events
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import uuid

from backend.config import settings
from backend.models import LogEntry, AgentDecision, AgentResponse


class AgentLogger:
    """Logger for agent decisions and interactions"""
    
    def __init__(self, log_file: Path = None):
        self.log_file = log_file or settings.LOG_FILE
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize log file if it doesn't exist
        if not self.log_file.exists():
            self.log_file.write_text("[]")
    
    def _read_logs(self) -> List[Dict[str, Any]]:
        """Read existing logs from file"""
        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading logs: {e}")
            return []
    
    def _write_logs(self, logs: List[Dict[str, Any]]):
        """Write logs to file"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2, default=str)
        except Exception as e:
            print(f"Error writing logs: {e}")
    
    def log_request(
        self,
        query: str,
        decision: AgentDecision,
        agent_responses: List[AgentResponse],
        final_answer: str,
        total_execution_time: float
    ) -> str:
        """
        Log a complete request with all agent interactions
        
        Args:
            query: User query
            decision: Controller's routing decision
            agent_responses: Responses from all agents
            final_answer: Final synthesized answer
            total_execution_time: Total time taken
        
        Returns:
            Request ID
        """
        request_id = str(uuid.uuid4())
        
        log_entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "decision": {
                "agents_called": [a.value for a in decision.agents_to_call],
                "rationale": decision.rationale,
                "confidence": decision.confidence
            },
            "agent_responses": [
                {
                    "agent_type": resp.agent_type.value,
                    "success": resp.success,
                    "error": resp.error,
                    "num_retrieved_docs": len(resp.retrieved_docs),
                    "execution_time": resp.execution_time
                }
                for resp in agent_responses
            ],
            "final_answer": final_answer,
            "total_execution_time": total_execution_time
        }
        
        # Read existing logs
        logs = self._read_logs()
        
        # Add new log
        logs.append(log_entry)
        
        # Keep only last 1000 logs to prevent file from growing too large
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        # Write back
        self._write_logs(logs)
        
        print(f"✓ Logged request {request_id}")
        return request_id
    
    def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent logs
        
        Args:
            limit: Maximum number of logs to return
        
        Returns:
            List of log entries
        """
        logs = self._read_logs()
        return logs[-limit:]
    
    def get_log_by_id(self, request_id: str) -> Dict[str, Any]:
        """
        Get a specific log entry by request ID
        
        Args:
            request_id: Request ID to search for
        
        Returns:
            Log entry dictionary or None
        """
        logs = self._read_logs()
        for log in logs:
            if log.get("request_id") == request_id:
                return log
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about logged requests
        
        Returns:
            Dictionary with statistics
        """
        logs = self._read_logs()
        
        if not logs:
            return {
                "total_requests": 0,
                "avg_execution_time": 0,
                "agent_usage": {},
                "success_rate": 0
            }
        
        # Calculate statistics
        total_requests = len(logs)
        total_time = sum(log.get("total_execution_time", 0) for log in logs)
        avg_time = total_time / total_requests if total_requests > 0 else 0
        
        # Agent usage statistics
        agent_usage = {}
        successful_requests = 0
        
        for log in logs:
            # Count agent usage
            for agent_type in log.get("decision", {}).get("agents_called", []):
                agent_usage[agent_type] = agent_usage.get(agent_type, 0) + 1
            
            # Count successful requests
            agent_responses = log.get("agent_responses", [])
            if agent_responses and all(resp.get("success", False) for resp in agent_responses):
                successful_requests += 1
        
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_requests": total_requests,
            "avg_execution_time": round(avg_time, 2),
            "agent_usage": agent_usage,
            "success_rate": round(success_rate, 2)
        }
    
    def clear_logs(self):
        """Clear all logs"""
        self._write_logs([])
        print("✓ Cleared all logs")


# Global logger instance
logger = AgentLogger()


if __name__ == "__main__":
    # Test logger
    from backend.models import AgentType, AgentDecision, AgentResponse
    
    # Create test log
    decision = AgentDecision(
        agents_to_call=[AgentType.WEB_SEARCH, AgentType.ARXIV],
        rationale="Test routing",
        confidence=0.9
    )
    
    responses = [
        AgentResponse(
            agent_type=AgentType.WEB_SEARCH,
            success=True,
            execution_time=1.2
        ),
        AgentResponse(
            agent_type=AgentType.ARXIV,
            success=True,
            execution_time=0.8
        )
    ]
    
    request_id = logger.log_request(
        query="Test query",
        decision=decision,
        agent_responses=responses,
        final_answer="Test answer",
        total_execution_time=2.5
    )
    
    print(f"Logged request: {request_id}")
    
    # Get stats
    stats = logger.get_stats()
    print(f"Stats: {stats}")
    
    # Get recent logs
    logs = logger.get_logs(limit=10)
    print(f"Recent logs: {len(logs)}")