from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


# Updated StorylineDetail class
class StorylineDetail(BaseModel):
    storyline_option: str = Field(
        description="Sharp angle of the storyline presented as a title and what makes it newsworthy."
    )

    newsworthiness: str = Field(
    description=("Explanation of what makes the storyline newsworthy. A research abstract or document has high "
                 "newsworthiness if it is relevant to contemporary issues in society. A research abstract or document "
                 "has high newsworthiness if it potentially impacts many people in society in positive or negative ways. "
                 "A research abstract or document has high newsworthiness if it has potential for controversy. "
                 "A research abstract or document has high newsworthiness if it can be easily understood by a general "
                 "audience, and this counts two times as much as other newsworthiness criteria.")
    )

    exploration: str = Field(
        description="What should be explored/researched in relation to this storyline."
    )


class Storylines(BaseModel):
    storyline_1: StorylineDetail
    storyline_2: StorylineDetail
    storyline_3: StorylineDetail


# Updated prompt to match new structure
storyline_prompt_template = """
You are an editor on a pricewinning mediaorganization. You are tasked with creating news worthy storylines.
The target audience for the storylines should be everyday people, meaning that the explanations must avoid technical jargon, 
should be clear, and easily understandable by a general audience. The language should be accessible to people without specialized knowledge.

For each of the following documents, provide a storyline as follows:

Title: [Title of the storyline]
Newsworthiness: [Why it is newsworthy]
Exploration: [What should be explored or researched]

{context}

"""


def generate_storyline(user_input_text: str):
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

    # Print the formatted prompt to inspect it before passing it to the LLM
    formatted_prompt = storyline_prompt_template.format(context=user_input_text)
    print(f"Prompt passed to LLM: {formatted_prompt}")
    
    # Combine into chain
    chain = prompt | structured_llm

    # Invoke the chain with user input
    response = chain.invoke({"context": user_input_text})
    
    return response
