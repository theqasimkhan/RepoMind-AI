from dataclasses import dataclass
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

@dataclass
class RagContext:
    repository: str
    question: str
    retrieved_chunks: list[str]

class RagPipeline:
    def __init__(self, gemini_api_key: str | None = None, openrouter_api_key: str | None = None):
        self.gemini_api_key = gemini_api_key
        self.openrouter_api_key = openrouter_api_key

    async def answer(self, context: RagContext) -> str:
        if self.openrouter_api_key:
            # Use OpenRouter with Gemini 2.5 Flash as default model
            llm = ChatOpenAI(
                model="google/gemini-2.5-flash",
                api_key=self.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=0.2
            )
        elif self.gemini_api_key:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=self.gemini_api_key,
                temperature=0.2
            )
        else:
            return "Error: No AI API key configured (Gemini or OpenRouter)."
        
        system_prompt = (
            f"You are RepoMind AI, an expert software architect assistant.\n"
            f"You are analyzing the repository: {context.repository}\n"
            f"Use the provided context chunks to answer the user's question accurately.\n"
            f"If the answer is not in the context, state that you cannot find the answer in the provided code."
        )
        
        joined_context = "\n\n---\n\n".join(context.retrieved_chunks[:10])
        human_prompt = (
            f"Context:\n{joined_context}\n\n"
            f"Question: {context.question}"
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = await llm.ainvoke(messages)
            if isinstance(response.content, str):
                return response.content
            return str(response.content)
        except Exception as e:
            return f"An error occurred while generating the response: {str(e)}"

    async def hyde_hypothetical_snippet(self, question: str) -> str | None:
        """
        One short hypothetical code/doc passage to improve dense retrieval (HyDE).
        Returns None when no API key is configured.
        """
        if self.openrouter_api_key:
            llm = ChatOpenAI(
                model="google/gemini-2.5-flash",
                api_key=self.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=0.3,
            )
        elif self.gemini_api_key:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=self.gemini_api_key,
                temperature=0.3,
            )
        else:
            return None

        system = (
            "You help retrieve source code. Write a single short paragraph of plausible code or "
            "technical prose that could answer the question (no markdown fences, no URLs)."
        )
        human = f"Question about a repository:\n{question}"
        messages = [SystemMessage(content=system), HumanMessage(content=human)]
        try:
            response = await llm.ainvoke(messages)
            text = response.content if isinstance(response.content, str) else str(response.content)
            return text.strip() or None
        except Exception:
            return None

    async def summarize_snippets(self, snippet_blocks: list[str]) -> str | None:
        """Short internal summary for agent tool (bounded context)."""
        if not snippet_blocks:
            return None
        if self.openrouter_api_key:
            llm = ChatOpenAI(
                model="google/gemini-2.5-flash",
                api_key=self.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=0.2,
            )
        elif self.gemini_api_key:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=self.gemini_api_key,
                temperature=0.2,
            )
        else:
            return None
        joined = "\n\n---\n\n".join(snippet_blocks[:12])[:12000]
        messages = [
            SystemMessage(
                content="Summarize the following code/documentation excerpts in 5-8 bullet points. "
                "Be factual; do not invent files or APIs."
            ),
            HumanMessage(content=joined),
        ]
        try:
            response = await llm.ainvoke(messages)
            text = response.content if isinstance(response.content, str) else str(response.content)
            return text.strip() or None
        except Exception:
            return None
