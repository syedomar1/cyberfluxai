# backend/agents/format_agent.py
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_ollama import OllamaLLM  # optional if you use Ollama; else not required

# NOTE: we will provide a simpler formatting function here if you aren't using LangChain.
# This file can be ignored if you don't use LangChain. Instead use the safe_parse_json helper in llm_helpers.
