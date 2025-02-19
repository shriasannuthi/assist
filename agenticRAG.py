from langchain_openai import ChatOpenAI
import os
from crewai_tools import PDFSearchTool
from crewai_tools import tools
from crewai import Crew
from crewai import Task
from crewai import Agent
from crewai.tools import BaseTool
from pydantic import Field
from langchain_community.utilities import GoogleSerperAPIWrapper
from markdown_pdf import MarkdownPdf, Section


llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)


Router_Agent = Agent(
    role="Router",
    goal="Route user question to a vectorstore or web search",
    backstory=(
        "You are an expert at routing a user question to a vectorstore or web search."
        "Use the vectorstore for questions on the user information."
        "Use the vectorstore when the word 'report' is used or when you are asked to generate a report."
        "Use web-search for question on latest news or recent topics."
        "Use generation for generic questions otherwise."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm,
)

Retriever_Agent = Agent(
    role="Retriever",
    goal="Retrieve data from the vectorstore and consolidate it into text format. Include all details and convert it into text format. Do not modiify any information.",
    backstory=(
        "You are a financial data processor."
        "You collect and consolidate all financial data about a person."
        "Use all the information in the document and convert it into text format."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm,
)

ReportGeneratorAgent = Agent(
    role="Financial Report Compiler",
    goal="Compile the extracted data into a financial history report for the customer requesting {question}.",
    backstory="As a Financial Report Compiler, you specialize in transforming raw data into comprehensive reports. Your attention to detail ensures that each report is tailored to meet the specific needs of the customer.",
    verbose=True,
    allow_delegation=False,
    llm=llm,
)

search = GoogleSerperAPIWrapper


class SearchTool(BaseTool):
    name: str = "Search"
    description: str = (
        "Useful for search-based queries. Use this to find current information about current interest rates, comparison of bank offers, markets, companies, and trends."
    )
    search: GoogleSerperAPIWrapper = Field(default_factory=GoogleSerperAPIWrapper)

    def _run(self, query: str) -> str:
        """Execute the search query and return results"""
        try:
            return self.search.run(query)
        except Exception as e:
            return f"Error performing search: {str(e)}"


class GenerationTool(BaseTool):
    name: str = "Generation_tool"
    description: str = (
        "Useful for generic-based queries. Use this to find  information based on your own knowledge."
    )

    def _run(self, query: str) -> str:
        llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
        """Execute the search query and return results"""
        return llm.invoke(query)


generation_tool = GenerationTool()
web_search_tool = SearchTool()

pdf_search_tool = PDFSearchTool(
    pdf="transformer.pdf",
)


router_task = Task(
    description=(
        "Analyse the keywords in the question {question}"
        "Based on the keywords decide whether it is eligible for a vectorstore search or a web search or generation."
        "Return a single word 'vectorstore' if it is eligible for vectorstore search or when the word 'report' is used."
        "Return a single word 'websearch' if it is eligible for web search."
        "Return a single word 'generate' if it is eligible for generation."
        "Do not provide any other preamble or explanation."
    ),
    expected_output=(
        "Give a  choice 'websearch' or 'vectorstore' or 'generate' based on the question"
        "Do not provide any other preamble or explanation."
    ),
    agent=Router_Agent,
)

retriever_task = Task(
    description=(
        "Based on the response from the router task extract information for the question {question} with the help of the respective tool."
        "Use the web_serach_tool to retrieve information from the web in case the router task output is 'websearch'."
        "Use the pdf_search_tool to retrieve information from the vectorstore in case the router task output is 'vectorstore'."
        "otherwise generate the output based on your own knowledge in case the router task output is 'generate"
    ),
    expected_output=(
        "You should analyse the output of the 'router_task'"
        "If the response is 'websearch' then use the web_search_tool to retrieve information from the web and return a clear and consolidated answer."
        "If the response is 'vectorstore' then use the rag_tool to retrieve information from the vectorstore."
        "If the response is 'generate' then use then use generation_tool ."
        "otherwise say i dont know if you dont know the answer"
        "Return the output of the 'router_task' appended with the corresponding text extracted."
    ),
    agent=Retriever_Agent,
    context=[router_task],
    tools=[pdf_search_tool, web_search_tool, generation_tool],
)

generate_financial_report_task = Task(
    description="Based on the response from the retriever task, you must help the customer in satisfying his financial needs. Compile the extracted data into a financial history report for the customer requesting {question}. Ensure that the report is clear, concise, and tailored to the customer's needs.",
    expected_output=(
        "You should analyse the output of the 'retriever_task'"
        "If the response starts with 'websearch' return a clear and consolidated answer of the following text."
        "If the response starts with 'vectorstore' return a detailed financial report of the user containing personal information, employment information, income summary, assets list, liabilities, monthly expenses, financial ratos(debt-to-income ratio, Savings Rate, Housing Expense Ratio, Total Assets to Liabilities), credit information(credit score, total credit accounts, average account age) and a final verdict whether the user is eligible for the service mentioned in  {question} based on all the information extracted."
        "If the response starts with 'generate' return a clear and consolidated answer of the following text."
    ),
    agent=ReportGeneratorAgent,
    context=[retriever_task],
    tools=[generation_tool],
)

rag_crew = Crew(
    agents=[Router_Agent, Retriever_Agent, ReportGeneratorAgent],
    tasks=[router_task, retriever_task, generate_financial_report_task],
    verbose=True,
)

# result = rag_crew.kickoff(inputs={"question":"What is the interest rate on a loan offered by Wells Fargo?"})
# result = rag_crew.kickoff(inputs={"question":"What are the credit card offers by Wells Fargo?"})
# result = rag_crew.kickoff(inputs={"question": "Which bank has a good market sentiment for housing loan?"})
result = rag_crew.kickoff(inputs={"question": "Create a report for me. I'm looking to apply for a housing loan"})


# def run():
#     # question = input("Hi, How can I assist you today? \n")
#     # result = rag_crew.kickoff(inputs={"question": question, "type": "str"})
#     result = rag_crew.kickoff(
#         inputs={
#             "description": "Create a report for me. I'm looking to apply for a housing loan"
#         }
#     )
#     pdf = MarkdownPdf(toc_level=1)
#     pdf.add_section(Section(result.raw))
#     pdf.save(f"report_pdf.pdf")


# run()
