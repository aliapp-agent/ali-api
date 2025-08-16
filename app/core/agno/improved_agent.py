"""Improved Agent wrapper for backward compatibility."""

from app.core.agno.graph import OptimizedAgnoAgent, get_agno_agent

# Alias for backward compatibility
ImprovedAgnoAgent = OptimizedAgnoAgent


def get_improved_agno_agent(session_id: str = "default_session") -> OptimizedAgnoAgent:
    """Get an instance of the improved Agno agent.
    
    Args:
        session_id: Session identifier for the agent
        
    Returns:
        OptimizedAgnoAgent instance
    """
    return get_agno_agent(session_id)


# Export for convenience
__all__ = ["ImprovedAgnoAgent", "get_improved_agno_agent"]
