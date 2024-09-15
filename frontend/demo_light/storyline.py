import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel, Field
from enum import Enum

# Configure logging to only log to the console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
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

# Define the NewsworthinessCriteria Enum
class NewsworthinessCriteria(Enum):
    RELEVANCE = "Relevance to contemporary issues"
    IMPACT = "Potential societal impact"
    CONTROVERSY = "Potential for controversy"
    ACCESSIBILITY = "Ease of understanding by a general audience"
    TIMELINESS = "Relation to current events"
    NOVELTY = "Uniqueness or originality"
    PROXIMITY = "Closeness to the target audience"
    HUMAN_INTEREST = "Emotional appeal to the audience"
    PROMINENCE = "Involvement of prominent figures or entities"
    CONFLICT = "Presence of disagreement or struggle"
    CONSEQUENCE = "Long-term effects or future implications"
    PUBLIC_INTEREST = "Alignment with public good or general concern"
    FEASIBILITY = "Practicality of covering the topic"
    OTHER = "Other"

# Define the StorylineDetail model
class StorylineDetail(BaseModel):
    angle: str = Field(description="Sharp journalistic angle of the storyline with a speciic focus.")
    title: str = Field(description="Short and sharp title of the storyline. Only one sentence is allowed and avoid splitting it with semicolon.")
    storyline_type: StorylineType = Field(description="The type of storyline. If other is selceted, explain what category it is")
    newsworthiness: List[NewsworthinessCriteria] = Field(description="List of newsworthiness criteria that apply. You need to explain how they apply.")
    elaboration: str = Field(description="Elaboration on the storyline, including what should be researched to gather information for a journalistic article.")

    class Config:
        extra = 'forbid'

# Define the Storylines model
class Storylines(BaseModel):
    storyline_1: StorylineDetail
    storyline_2: StorylineDetail
    storyline_3: StorylineDetail

    class Config:
        extra = 'forbid'

def generate_storyline(doc: str) -> Storylines:
    """Analyzes a document using OpenAI to extract three storylines."""
    logging.info("Starting document analysis.")
    
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": (
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
                )},
                {"role": "user", "content": f"Please analyze the following document: {doc}"}
            ],
            response_format=Storylines
        )
        storylines: Storylines = completion.choices[0].message.parsed 
        logging.info("Storyline generation complete.")
        return storylines
    except Exception as e:
        logging.error(f"Error analyzing document: {e}")
        raise