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
    subheadline: str = Field(
        description="A concise secondary line under the main headline that provides a key insight, detail, or context, enhancing the readers understanding of the headline. The subheadline often emphasizes the significance, relevance, or impact of the main topic, creating an enticing hook that complements the main headline and are very short."
    )

    storyline_type: StorylineType = Field(
        description="The type of storyline. If other is selceted, explain what category it is"
    )
    newsworthiness: List[NewsworthinessCriteria] = Field(
        description="Two of newsworthiness criteria that apply best and an argument for how they apply."
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

                        #1. example user input
                    {"role": "user", "content": "One-third of Mars surface has shallow-buried H2O, but it is currently too cold for use by life. Proposals to warm Mars using greenhouse gases require a large mass of ingredients that are rare on Mars surface. However, we show here that artificial aerosols made from materials that are readily available at Mars—for example, conductive nanorods that are ~9 micrometers long—could warm Mars >5 103 times more effectively than the best gases. Such nanoparticles forward-scatter sunlight and efficiently block upwelling thermal infrared. Like the natural dust of Mars, they are swept high into Mars’ atmosphere, allowing delivery from the near-surface. For a 10-year particle lifetime, two climate models indicate that sustained release at 30 liters per second would globally warm Mars by ≳30 kelvin and start to melt the ice. Therefore, if nanoparticles can be made at scale on (or delivered to) Mars, then the barrier to warming of Mars appears to be less high than previously thought. INTRODUCTION Dry river valleys cross Mars’s once-habitable surface (1, 2), but today the icy soil is too cold for Earth-derived life (3–5). Streams may have flowed as recently as 600 thousand years ago (6), hinting at a planet on the cusp of habitability. Many methods have been proposed to warm Mars’ surface by closing the spectral windows, centered around wavelengths (λ) 22 and 10 μm, through which the surface is cooled by thermal infrared radiation upwelling to space (7–9). Modern Mars has a thin (~6 mbar) CO2 atmosphere that provides only ~5 K greenhouse warming via absorption in the 15-μm band (10), and Mars apparently lacks enough condensed or mineralized CO2 to restore a warm climate (11). The spectral windows can be closed using artificial greenhouse gases (e.g., chloroflourocarbons) (8, 12), but this would require volatilizing ~100,000 megatons of fluorine, which is sparse on the Mars surface. An alternative approach is suggested by natural Mars dust aerosol. Mars dust is almost all ultimately sourced from slow comminution [indirect estimate O(3) liters/s (13)] of iron-rich minerals on Mars’ surface. Because of its small size (1.5-μm effective radius), Mars dust is lofted to high altitude (altitude of peak dust mass mixing ratio, 15 to 25 km), is always visible in the Mars sky, and is present up to >60 km altitude (14–15). Natural Mars dust aerosol lowers daytime surface temperature [e.g., (16)], but this is due to compositional and geometric specifics that can be modified in the case of engineered dust. For example, a nanorod about half as long as the wavelength of upwelling thermal infrared radiation should interact strongly with that radiation (17). RESULTS Consider a 9-μm-long conductive nanorod (we consider aluminum and iron) with a ~60:1 aspect ratio, not much smaller than commercially available glitter. Finite-difference time domain calculations (Supplementary Text) show that such nanorods, randomly oriented due to Brownian motion (18), would strongly scatter and absorb upwelling thermal infrared in the spectral windows and forward-scatter sunlight down to the surface, leading to net warming (Fig. 1 and figs. S1 to S4). Results are robust to changing particle material type, cross-sectional shape, and mesh resolution and change as expected with particle length and aspect ratio (figs. S5 to S8). The calculated thermal infrared scattering is near-isotropic (Fig. 1), which favors surface warming (19). Such nanorods would settle >10× more slowly in the Mars atmosphere than natural Mars dust (Supplementary Text), implying that, once the particles are lifted into the air, they would be lofted to high altitude and have a long atmospheric lifetime. This motivates calculating surface warming (K) as a function of (artificial) aerosol column density (kilograms per square meter). The Mars Weather Research and Forecasting (MarsWRF) global climate model is suitable for such a calculation (20–22). Following many previous works (22–26), we prescribe a layer of aerosol and calculate the resulting steady-state warming (Supplementary Text). Our calculation does not include dynamic transport of aerosol but includes realistic topography, seasonal forcing, and surface thermophysical properties and albedo. The model output (Fig. 2 and figs. S9 to S19) shows that an Al nanorod column density of 160 mg/m2 yields surface temperatures and pressures permitting extensive summertime (i.e., the warmest ~70 sols period each year) liquid water in locations with shallow ground ice. This is >5000× more effective, on a warming-per-unit-mass-in-the-atmosphere basis, than the current state of the art (Supplementary Text) (8). Temperatures experienced by subsurface ice will be lower due to insulation by soil. Water ice at <1 m depth is almost ubiquitous poleward of ±50° latitude (blue lines in Fig. 2) (1). H2O ice is present further equatorward (27) but is insulated beneath >1-m soil cover and so would not melt unless the annual average surface temperature is raised close to 273 K."},

                    # Assistant example response (this is the assistant prompt showing the model how to respond)
                    {"role": "assistant", "content": """
                    StorylineDetail(
                        angle="Using engineered nanodust to warm Mars offers a highly efficient and scalable solution for making the planet more habitable.",
                        title="Engineered Dust Could Help Make Mars Habitable",
                        subheadline="Restoring water on Mars may be easier than you think",
                        storyline_type=StorylineType.ENVIRONMENTAL_IMPACT,
                        newsworthiness=[
                            NewsworthinessCriteria(criteria="Impact: The method has the potential to transform Mars' climate, making it more habitable and significantly advancing space exploration."),
                            NewsworthinessCriteria(criteria="Novelty: The approach of using engineered nanodust is an innovative and original concept in planetary climate engineering."),
                            NewsworthinessCriteria(criteria="Feasibility: The method leverages materials already present on Mars, making it a practical solution for large-scale climate modification."),
                            NewsworthinessCriteria(criteria="Relevance: The topic ties into the growing interest in human colonization of Mars, making it timely and significant in the context of space exploration.")
                        ],
                        elaboration="For decades, scientists and science-fiction authors have toyed with the idea of restoring Mars to that warmer state by “terraforming” it—changing the planet’s climate to make it friendly to Earthlings. Their proposals tend to involve heroic engineering: injecting vast quantities of greenhouse gases into the atmosphere, say, or using nuclear explosives to melt underground ice. A paper published this week in Science Advances offers an easier method. Samaneh Ansari, a graduate student at Northwestern University, in Illinois, and her colleagues reckon that pumping engineered dust into the atmosphere could warm Mars to the point where much of the water ice that lies beneath its surface would melt, at least in the Martian summer."
                    )
                    """},

                    #2. example user input
                    {"role": "user", "content": "Abstract In this paper, we combine administrative data for Spain from 2010 to 2018 with meteorological data, to identify the effect of daily mean temperature on fertility. We demonstrate for Spain that hot days (≥25°C) decrease the total fertility rate nine months after exposure. Moreover, we do not observe any substantial heterogeneities in the effect of heat by mother’s age, mother’s educational attainment, sex of the newborn, climatic area, or air conditioning penetration. Our results suggest that climate change may be altering the seasonal distribution of births and affect fertility rates in a context with low fertility and rapid population ageing. Introduction Climate change and its associated extreme meteorological events have become urgent challenges for human populations in the twenty-first century. According to NASA’s Goddard Institute for Space Studies, the summer of 2023 was the hottest since records began in 1880, and the period between 2015 and 2022 has been the hottest since records began (NASA Citation2023). The increasing—and likely unceasing—escalation of extreme climatic events has led to calls for urgent action to mitigate their effects and for a better understanding of the possible population impacts in the decades ahead (Muttarak Citation2021). A vast body of literature has investigated the impact of climate change and extreme temperatures on various population outcomes, including mortality (Stafoggia et al. Citation2006; Carleton et al. Citation2022; Conte Keivabu Citation2022; Masiero et al. Citation2022;), infant health (Chen et al. Citation2020; Le and Nguyen Citation2021; Conte Keivabu and Cozzani Citation2022), adult health (Barreca and Shimshack Citation2012; Bai et al. Citation2014), income (Isen et al. Citation2017), educational attainment (Wilde et al. Citation2017; Randell and Gray Citation2019), and migration (Hoffmann et al. Citation2021). Surprisingly, far less attention has been paid to the impact of climate change on fertility, with only a handful of studies conducted to date, as noted by Grace (Citation2017) and Hajdu and Hajdu (Citation2020). Specifically, two studies have been conducted in the US (Lam and Miron Citation1996; Barreca et al. Citation2018), one in South Korea (Cho Citation2020), one in Hungary (Hajdu and Hajdu Citation2022), one in Brazil (Marteleto et al. Citation2023), and one study that pooled together data from sub-Saharan Africa (Thiede et al. Citation2022). Overall, these studies have found a reduction in fertility 8–10 months after abnormally hot days. However, this literature contains significant gaps. First, many researchers have analysed aggregate fertility rates at subnational level without exploring heterogeneous patterns within these populations, often due to a lack of relevant data. While such studies are useful in determining the population-level effects of temperature variation, it is important to elucidate possible heterogeneous effects, for example by maternal age, parental educational level, and sex of the newborn, to understand the stratified effects of climate change on individuals. This is particularly important because there are cogent theoretical arguments that certain populations are better able to mitigate temperature shocks than others. Individuals with a lower socio-economic status (SES) may lack access to mitigation technologies (e.g. fans, air conditioning [AC]), live in housing units which are poorly insulated from temperature variations, or work in professions which are more likely to be outdoors (e.g. construction, agriculture). Thiede et al. (Citation2022) used microdata to explore these heterogeneities, but their analysis used only annual variation in temperatures rather than the high-frequency daily shocks aggregated to monthly level as preferred in this literature (see Dell et al. Citation2014) to understand trimester- or month-specific temperature effects. Conversely, Cho (Citation2020) used aggregated subnational data on maternal characteristics to explore whether the fraction of mothers in certain groups changed with temperature, but they did not find any significant heterogeneities by mother’s age or SES. Second, this literature lacks attention to heterogeneous effects across contexts. Most studies have focused on locations that are either: (1) areas with high income and high AC penetration (e.g. the United States (US), South Korea); or (2) small areas with homogeneous climatic zones (e.g. South Korea, Hungary). Only Thiede et al. (Citation2022), in their pan-African analysis, looked broadly at a low-AC-penetration context with broad differences in climate, but such heterogeneities were not explored within their study. For example, many of these studies have posited parental reproductive health as a major possible mechanism driving fertility effects yet lacked any direct evidence on the role of parental SES in the temperature–fertility relationship. In this paper, we provide new evidence on the link between temperature and fertility. Using data from Spanish registers between 2010 and 2018, we study this relationship across climatic zones, maternal age groups, parental educational levels, and sex of newborns. To this aim, we calculate total fertility rates (TFRs) from Spanish population-wide birth registers and statistics on resident population, and we create a province-by-month data set, which we combine with fine-grained meteorological data provided by the Copernicus Climate Data Store (CDS)."},

                    # assistant example
                    {"role": "assistant", "content": """
                    StorylineDetail(
                        angle="Extreme heat is shown to reduce fertility rates, with the impact becoming more significant as climate change accelerates.",
                        title="Fewer babies are born in the months following hot days",
                        subheadline="The effect is small but consistent",
                        storyline_type=StorylineType.HEALTH_IMPLICATIONS,
                        newsworthiness=[
                            NewsworthinessCriteria(criteria="Impact: The findings highlight how climate change could further strain low fertility rates in countries like Spain, contributing to broader concerns about population aging."),
                            NewsworthinessCriteria(criteria="Relevance: As climate change continues to affect global temperatures, understanding its impact on fertility becomes crucial in addressing demographic challenges."),
                            NewsworthinessCriteria(criteria="Novelty: The study offers new evidence linking daily temperatures to fertility, expanding on limited previous research in this field and providing unique insights into Spain's demographic trends."),
                            NewsworthinessCriteria(criteria="Timeliness: The study is highly relevant given the increasing number of record-breaking heat events globally, with the summer of 2023 being the hottest on record.")
                        ],
                        elaboration="This study is the latest to show that extreme heat reliably leads to decreased birth rates around nine months later, with evidence from Spain echoing similar findings from other countries. While the overall effect is small, it could grow more significant as climate change intensifies, making heat shocks more frequent. This adds a new dimension to the ongoing discussion about declining fertility rates and highlights the potential long-term demographic impacts of a warming climate."
                    )
                    """},
                    
                    #3. user example input
                    {"role": "user", "content": "Enhancing the durability of mosquito repellent textiles through microencapsulation of lavender oil. Abstract In this study, the objective was to develop a long-lasting mosquito repellent textile by synthesizing silk-based lavender oil microcapsules and applying them to cotton fabric. Lavender oil, derived from Lavandula angustifolia, was chosen as the plant-based material. The microcapsules’ morphology and the fabric’s surface were examined using optical and scanning electron microscopes. Dynamic light scattering was utilized to measure the capsule size and zeta potential. The mosquito repellent efficacy was evaluated through cage tests before and after multiple wash cycles and after exposure to different environments. A cytotoxicity assay was conducted on functionalized fabrics in order to assess their biocompatibility. Additionally, comfort properties such as breathability and water absorbency were assessed and compared to a control fabric. The results indicated that a higher concentration of lavender oil microcapsules (15 wt%) on the fabric exhibited excellent mosquito repellent efficacy (95.7%) prior to washing, which remained effective as 84.5% even after 40 washes. Furthermore, the functionalized fabric maintained its repellent properties following exposure to temperatures of 25°C and 37°C for 4 weeks. The cytotoxicity results indicated that the functionalized fabric exhibited non-toxic properties toward L929 cells, thereby confirming its favorable biocompatibility. This study successfully demonstrated the synthesis and application of silk-based lavender oil microcapsules on textiles, resulting in highly durable mosquito repellent fabrics effective against Aedes aegypti mosquitoes. These findings highlight the potential of this eco-friendly approach for developing effective and long-lasting mosquito repellent textiles. Introduction Insects play a significant role in human life, providing both benefits and drawbacks. While they contribute to pollination and support agriculture (Mateos Fernández et al. 2022), they also pose a threat to human health by transmitting diseases (Nava-Doctor et al. 2021). Among these disease vectors, mosquitoes are particularly concerning due to their ability to transmit life-threatening arboviruses (Gräf et al. 2021; Uwishema et al. 2022; Tyagi 2023). Aedes aegypti, a mosquito species, is responsible for transmitting diseases such as dengue and yellow fever, affecting millions of people globally (Zahir et al. 2021). Various methods have been developed to combat the impact of mosquitoes. Mosquito nets have been widely used, but they are only effective for stationary individuals. Alternative methods, such as mosquito coils, candles, lanterns, and torches, have been developed to cater to individuals on the move. However, these methods emit smoke that can contain harmful contaminants, posing health risks, and there is also a fire hazard associated with their use. Prior research has highlighted DEET (N,N-diethyl-methyl-toluamide) as the most popular and effective synthetic insect repellent (Mbuba et al. 2021). Another synthetic repellent, permethrin, has been widely used on textiles using various methods (Xiang et al. 2020). However, despite their effectiveness, synthetic repellents such as DEET and permethrin have been associated with health risks, including low blood pressure, skin rashes, eye irritation, and respiratory problems in children (Madan and Rani 2019). In light of these concerns, researchers have turned to natural resources for the development of mosquito repellents. Natural materials, including plant extracts, oils, mud, and tar, have been explored as mosquito repellents, with essential oils showing particular promise. Essential oils have been found to be effective against mosquitoes while being eco-friendly and having minimal negative effects on the environment and human health, as reported in the literature (Asadollahi et al. 2019; Azeem et al. 2019; Li et al. 2021; Santos et al. 2022)."},

                    #assistant example
                    {"role": "assistant", "content": """
                    StorylineDetail(
                        angle="The development of the first nuclear clock could revolutionize precision timekeeping, surpassing atomic clocks by a factor of 1,000.",
                        title="The worlds first nuclear clock is on the horizon",
                        subheadline="It would be 1,000 times more accurate than todays atomic timekeepers"
                        storyline_type=StorylineType.BREAKTHROUGH,
                        newsworthiness=[
                            NewsworthinessCriteria(criteria="Impact: This innovation could significantly advance timekeeping precision, improving fields like GPS, stock trading, and fundamental physics studies, potentially altering how we measure time across various industries."),
                            NewsworthinessCriteria(criteria="Novelty: The nuclear clock introduces a new, groundbreaking method of timekeeping based on nuclear transitions, offering a major improvement over atomic clocks and marking a significant technological leap."),
                            NewsworthinessCriteria(criteria="Feasibility: With the successful measurement of the 229Th nuclear clock transition and its frequency link to the 87Sr atomic clock, this development is no longer theoretical but on the verge of practical implementation."),
                            NewsworthinessCriteria(criteria="Relevance: The research is timely as it opens new avenues for testing the limits of Einsteins theories of relativity and deepens our understanding of fundamental physics.")
                        ],
                        elaboration="The next generation of timekeeping is approaching with the development of the nuclear clock, which could be 1,000 times more precise than todays atomic clocks. While atomic clocks are already highly accurate and essential for technologies like GPS and stock-market trading, the nuclear clock offers an independent way of measuring time, relying on both the strong nuclear force and the electromagnetic force. This breakthrough also provides a new tool for testing Einstein’s theory of relativity, which posits that time moves slower in stronger gravitational fields. If nuclear clocks behave differently under these conditions, it could lead to revisions in our understanding of fundamental physics."
                    )
                    """},

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
