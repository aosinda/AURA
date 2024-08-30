from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI



class StorylineDetail(BaseModel):
    storyline_option: str = Field(
    description="The storyline based on the research papers or articles."
    )
    elaboration: str = Field(
    description="Elaboration on the storyline, explaining what makes it newsworthy or other angles to explore."
)



class Storylines(BaseModel):
    storyline_1: StorylineDetail
    storyline_2: StorylineDetail
    storyline_3: StorylineDetail



storyline_prompt_template = """
    A research abstract or document has high newsworthiness if it is relevant to contemporary issues in society.
    A research abstract or document has high newsworthiness if it potentially impacts many people in society in
    positive or negative ways. A research abstract or document has high newsworthiness if it has potential for controversy.
    A research abstract or document has high newsworthiness if it can be easily understood by a general audience, and this
    counts two times as much as other newsworthiness criteria. Rate the newsworthiness of the following research
    abstracts, articles, or documents by providing a numeric rating on a scale from 1 to 5 where 1 is a low newsworthiness rating and 5
    is a high newsworthiness rating:



    {context}



    Then I want you to provide me with three storylines based on these research papers, articles, or documents. The storylines are related
    to high newsworthiness. For each storyline, provide the following:
    1. The storyline option.
    2. An elaboration on the storyline, including what makes it newsworthy or any other angles that should be explored in relation to this storyline.
    Only output the three storylines with their elaborations.
    """



def generate_storyline(user_input_text):
    # Chain the model with a prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
        ("system", storyline_prompt_template),
        ("human", "{context}"),
        ]
    )
    # Set up model
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    # Use structured output with Pydantic model
    structured_llm = llm.with_structured_output(Storylines)
    # Combine into chain
    chain = prompt | structured_llm



    response = chain.invoke({"context": user_input_text})
    return response