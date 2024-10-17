import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel, Field
from enum import Enum

from langchain_core.messages import HumanMessage
from langchain.schema import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import create_react_agent
from langchain.tools.retriever import create_retriever_tool

# Configure logging to only log to the console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Load environment variables
load_dotenv()

try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print(load_dotenv())
        raise ValueError("OpenAI API key not found.")
    client = OpenAI(api_key=openai_api_key)
    logging.info("OpenAI client initialized.")
except Exception as e:
    logging.error(f"Error initializing OpenAI client: {e}")
    raise


# Define the StorylineType Enum
class StorylineType(Enum):
    SOCIETAL_IMPACT = "Societal Impact"
    CONTROVERSY = "Controversy"
    BREAKTHROUGH = "Breakthrough"
    ETHICAL_CONCERNS = "Ethical Concerns"
    HISTORICAL_CONTEXT = "Historical Context"
    TECHNICAL_ANALYSIS = "Technical Analysis"
    CULTURAL_SIGNIFICANCE = "Cultural Significance"
    ECONOMIC_IMPACT = "Economic Impact"
    REGULATORY_CHALLENGES = "Regulatory Challenges"
    ENVIRONMENTAL_IMPACT = "Environmental Impact"
    HEALTH_IMPLICATIONS = "Health Implications"
    FUTURE_PERSPECTIVES = "Future Perspectives"
    CASE_STUDIES = "Case Studies"
    OTHER = "Other"


class NewsworthinessCriteria(BaseModel):
    criteria: str = Field(
        description=(
            "The newsworthiness criteria that applies and an argument for how they apply. "
            "Examples of criteria include: "
            "Relevance: Relevance to contemporary issues. "
            "Impact: Potential societal impact. "
            "Controversy: Potential for controversy. "
            "Accessibility: Ease of understanding by a general audience. "
            "Timeliness: Relation to current events. "
            "Novelty: Uniqueness or originality. "
            "Proximity: Closeness to the target audience. "
            "Human Interest: Emotional appeal to the audience. "
            "Prominence: Involvement of prominent figures or entities. "
            "Conflict: Presence of disagreement or struggle. "
            "Consequence: Long-term effects or future implications. "
            "Public Interest: Alignment with public good or general concern. "
            "Feasibility: Practicality of covering the topic. "
            "Other: Other criteria that may apply."
        )
    )


# Define the StorylineDetail model
class StorylineDetail(BaseModel):
    angle: str = Field(
        description="Sharp journalistic angle of the storyline with a speciic focus."
    )
    title: str = Field(
        description="Short and sharp title of the storyline. Only one sentence is allowed and avoid splitting it with semicolon."
    )
    storyline_type: StorylineType = Field(
        description="The type of storyline. If other is selceted, explain what category it is"
    )
    newsworthiness: List[NewsworthinessCriteria] = Field(
        description="List of newsworthiness criteria that apply and an argument for how they apply."
    )
    elaboration: str = Field(
        description="Elaboration on the storyline, including what should be researched to gather information for a journalistic article."
    )

    class Config:
        extra = "forbid"


# Define the Storylines model
class Storylines(BaseModel):
    storyline_1: StorylineDetail
    storyline_2: StorylineDetail
    storyline_3: StorylineDetail

    class Config:
        extra = "forbid"


def generate_storyline(doc: str, user_query: str = None) -> Storylines:
    """Analyzes a document using OpenAI to extract three storylines."""
    logging.info("Starting document analysis.")
    # Change to qdrant
    vectorstore = InMemoryVectorStore.from_documents(
        documents=[Document(page_content=doc)], embedding=OpenAIEmbeddings()
    )
    retriever = vectorstore.as_retriever()

    tool = create_retriever_tool(
        retriever,
        "document_retriever",
        "Searches and returns excerpts from the provided document.",
    )
    tools = [tool]

    llm = ChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)
    memory = MemorySaver()
    agent_executor = create_react_agent(llm, tools, checkpointer=memory)

    def call_agent(state: dict):
        response = agent_executor.invoke(state)
        storylines_str = response["messages"][-1].content
        try:
            completion = client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a journalistic editor from an award-winning news media organization. "
                            "Your task is to critically read through documents and find three different newsworthy storylines that are relevant, impactful, or controversial. "
                            "Explain all technical jargon in simple terms and use examples or analogies that a general audience can understand. "
                            "For example, if the document discusses a genetic mutation like DAT-K619N, avoid the scientific code and instead describe what it does, why it matters, and how it could affect people's lives. "
                            "Highlight the real-world significance and potential impact of these storylines. "
                            "Delve into the societal, economic, political, and ethical implications of the findings, creating a multi-layered narrative. "
                            "Emphasize areas of conflict, paradoxes, and tensions within the document to uncover deeper angles. "
                            "Your goal is to craft storylines that not only present the facts but also pose provocative questions and highlight interconnectedness between issues. "
                            "Explore potential controversies, such as political motivations behind scientific findings or economic dilemmas faced by nations. "
                            "Balance the storyline by considering both breakthrough and potential ethical concerns, driving an engaging narrative that prompts critical thinking."
                            "When listing newsworhiness criteria, you need to explain why they apply and an argument from the text for how they apply. for example: Impact: The discovery has the potential to imacp x amount of people with this condition it says in the report."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Please analyze the following document: {storylines_str}",
                    },
                ],
                response_format=Storylines,
            )
            storylines: Storylines = completion.choices[0].message.parsed
        except Exception as e:
            logging.error(f"Error parsing storylines: {e}")
            raise
        return {"storylines": storylines}

    workflow = StateGraph(state_schema=dict)
    workflow.add_edge(START, "agent")
    workflow.add_node("agent", call_agent)

    app = workflow.compile()
    messages = [HumanMessage(content=doc)]
    if user_query:
        messages.append(HumanMessage(content=user_query))
    result = app.invoke({"messages": messages})
    storylines = result["storylines"]

    logging.info("Storyline generation complete.")
    return storylines
