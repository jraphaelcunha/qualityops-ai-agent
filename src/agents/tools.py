try:
    from crewai.tools import BaseTool
except (ImportError, AttributeError):
    class BaseTool:  # Fallback stub when crewai is unavailable
        pass

from src.rag.retriever import query_knowledge_base


class RulesSearchTool(BaseTool):
    name: str = "Rules Search Tool"
    description: str = "Useful for searching company compliance rules, specifically about security protocols, PIN verification requirements, and forbidden phrases. Use this to check if the agent followed the correct procedures."

    def _run(self, query: str) -> str:
        results = query_knowledge_base(query)
        if isinstance(results, list):
            return "\n\n".join(results)
        return str(results)
