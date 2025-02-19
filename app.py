# import streamlit as st
# import os
# import smtplib
# from email.message import EmailMessage
# from langchain_openai import ChatOpenAI
# from crewai_tools import PDFSearchTool
# from crewai import Crew, Task, Agent
# from crewai.tools import BaseTool
# from pydantic import Field
# from langchain_community.utilities import GoogleSerperAPIWrapper
# from markdown_pdf import MarkdownPdf, Section
# from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource


# def main():
#     st.title("Fargo Assist")
#     st.write(
#         "Enter your query below. Once the report is generated, it will be sent to your email."
#     )

#     question = st.text_input("How can I assist you today?")

#     email_address = st.text_input("Enter your email address:")

#     uploaded_files = st.file_uploader(
#         "Upload relevant PDFs",
#         type=["pdf"],
#         accept_multiple_files=True,
#     )

#     if st.button("Submit"):
#         if question and email_address:
#             st.info("Generating your financial report. Please wait...")

#             upload_folder = "knowledge\\uploads"
#             os.makedirs(upload_folder, exist_ok=True)
#             uploaded_file_paths = []
#             if uploaded_files is not None:
#                 for file in uploaded_files:
#                     file_path = os.path.join(
#                         "D:\\Programming\\phi\\phi\\knowledge\\uploads", file.name
#                     )
#                     with open(file_path, "wb") as f:
#                         f.write(file.getbuffer())
#                     uploaded_file_paths.append(os.path.join("uploads", file.name))

#             base_lst = os.listdir(path="knowledge\\base")
#             base_path_list = [os.path.join("base", f) for f in base_lst]

#             all_pdf_paths = base_path_list + uploaded_file_paths

#             pdf_source = PDFKnowledgeSource(file_paths=all_pdf_paths)

#             llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

#             Router_Agent = Agent(
#                 role="Router",
#                 goal="Route user question to a vectorstore or web search",
#                 backstory=(
#                     "You are an expert at routing a user question to a vectorstore or web search. "
#                     "Use the vectorstore for questions on the user information. "
#                     "Use the vectorstore when the word 'report' is used or when you are asked to generate a report. "
#                     "Use web-search for questions on latest news or recent topics. "
#                     "Use generation for generic questions otherwise."
#                 ),
#                 verbose=True,
#                 allow_delegation=False,
#                 llm=llm,
#             )

#             Retriever_Agent = Agent(
#                 role="Retriever",
#                 goal="Retrieve data from the vectorstore and consolidate it into text format. Include all details and convert it into text format. Do not modify any information.",
#                 backstory=(
#                     "You are a financial data processor. "
#                     "You collect and consolidate all financial data about a person. "
#                     "Use all the information in the document and convert it into text format."
#                 ),
#                 verbose=True,
#                 knowledge_sources=[pdf_source],
#                 allow_delegation=False,
#                 llm=llm,
#             )

#             ReportGeneratorAgent = Agent(
#                 role="Financial Report Compiler",
#                 goal="Compile the extracted data into a financial history report for the customer requesting {question}",
#                 backstory=(
#                     "As a financial report compiler, you specialize in transforming raw data into comprehensive reports. "
#                     "Your attention to detail ensures that each report is tailored to meet the specific needs of the customer. "
#                     "Any derivable parameters in the report must be calculated by you."
#                 ),
#                 verbose=True,
#                 allow_delegation=False,
#                 knowledge_sources=[pdf_source],
#                 llm=llm,
#             )

#             class PDFSearchTool(BaseTool):
#                 name: str = "Search a PDF's content"
#                 description: str = (
#                     "A tool that can be used to semantically search the content of the provided PDF. "
#                     "Make sure to supply a query string."
#                 )
#                 pdf: str

#                 def _run(self, query: str) -> str:
#                     if not isinstance(query, str):
#                         raise ValueError(
#                             f"Expected query to be a string, got {type(query).__name__}: {query}"
#                         )
#                     return f"Searching in PDF '{self.pdf}' for query: '{query}'"

#             class SearchTool(BaseTool):
#                 name: str = "Search"
#                 description: str = (
#                     "Useful for search-based queries. Use this to find current information about interest rates, markets, companies, and trends."
#                 )
#                 search: GoogleSerperAPIWrapper = Field(
#                     default_factory=GoogleSerperAPIWrapper
#                 )

#                 def _run(self, query: str) -> str:
#                     if not isinstance(query, str):
#                         raise ValueError(
#                             f"Expected query to be a string, got {type(query).__name__}: {query}"
#                         )
#                     try:
#                         return self.search.run(query)
#                     except Exception as e:
#                         return f"Error performing search: {str(e)}"

#             class GenerationTool(BaseTool):
#                 name: str = "Generation_tool"
#                 description: str = (
#                     "Useful for generic-based queries. Use this to find information based on your own knowledge."
#                 )

#                 def _run(self, query: str) -> str:
#                     if not isinstance(query, str):
#                         raise ValueError(
#                             f"Expected query to be a string, got {type(query).__name__}: {query}"
#                         )
#                     llm_local = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
#                     return llm_local.invoke(query)

#             class EmailTool(BaseTool):
#                 name: str = "Email Tool"
#                 description: str = (
#                     "Sends an email with a PDF attachment. Input should include receiver_email, subject, body, and attachment_path."
#                 )

#                 sender_email: str = Field(
#                     default_factory=lambda: os.environ.get("SENDER_EMAIL")
#                 )
#                 sender_password: str = Field(
#                     default_factory=lambda: os.environ.get("SENDER_PASSWORD")
#                 )

#                 def _run(self, input_data: dict) -> str:
#                     receiver_email = input_data.get("receiver_email")
#                     subject = input_data.get("subject")
#                     body = input_data.get("body")
#                     attachment_path = input_data.get("attachment_path")
#                     if not (receiver_email and subject and body and attachment_path):
#                         return "Missing parameters for sending email."

#                     msg = EmailMessage()
#                     msg["Subject"] = subject
#                     msg["From"] = self.sender_email
#                     msg["To"] = receiver_email
#                     msg.set_content(body)

#                     with open(attachment_path, "rb") as f:
#                         file_data = f.read()
#                         file_name = os.path.basename(attachment_path)
#                     msg.add_attachment(
#                         file_data,
#                         maintype="application",
#                         subtype="pdf",
#                         filename=file_name,
#                     )

#                     try:
#                         with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
#                             smtp.login(self.sender_email, self.sender_password)
#                             smtp.send_message(msg)
#                         return "Email sent successfully."
#                     except Exception as e:
#                         return f"Error sending email: {e}"

#             generation_tool = GenerationTool()
#             web_search_tool = SearchTool()
#             pdf_search_tool = PDFSearchTool(pdf="base.pdf")
#             email_tool = EmailTool()

#             router_task = Task(
#                 description=(
#                     "Analyse the keywords in the question {question}. "
#                     "Based on the keywords decide whether it is eligible for a vectorstore search or a web search or generation. "
#                     "Return a single word 'vectorstore' if it is eligible for vectorstore search. "
#                     "Return a single word 'websearch' if it is eligible for web search. "
#                     "Return a single word 'generate' if it is eligible for generation. "
#                     "Do not provide any other preamble or explanation."
#                 ),
#                 expected_output=(
#                     "Give a choice 'websearch' or 'vectorstore' or 'generate' based on the question. "
#                     "Do not provide any other preamble or explanation."
#                 ),
#                 agent=Router_Agent,
#             )

#             retriever_task = Task(
#                 description=(
#                     "Based on the response from the router task, extract information for the question {question} with the help of the respective tool. "
#                     "Use the web_search_tool to retrieve information from the web if the router task output is 'websearch'. "
#                     "Use the pdf_search_tool to retrieve information from the vectorstore if the router task output is 'vectorstore'. "
#                     "Otherwise, generate the output based on your own knowledge if the router task output is 'generate'."
#                 ),
#                 expected_output=(
#                     "Analyze the output of the 'router_task'. "
#                     "If the response is 'websearch', then use the web_search_tool; if it is 'vectorstore', then use the pdf_search_tool; "
#                     "if it is 'generate', then use the generation_tool. "
#                     "Return the router's output appended with the extracted text."
#                 ),
#                 agent=Retriever_Agent,
#                 context=[router_task],
#                 tools=[pdf_search_tool, web_search_tool, generation_tool],
#             )

#             generate_financial_report_task = Task(
#                 description=(
#                     "Based on the response from the retriever task, help the customer by generating a financial report for the request {question}. "
#                     "Ensure the report is clear, concise, and tailored to the customer's needs."
#                 ),
#                 expected_output=(
#                     "Analyze the output of the 'retriever_task'. "
#                     "If it starts with 'websearch', return a consolidated answer; "
#                     "if it starts with 'vectorstore', return a detailed financial report with all relevant details; "
#                     "if it starts with 'generate', return a consolidated answer."
#                 ),
#                 agent=ReportGeneratorAgent,
#                 context=[retriever_task],
#                 tools=[generation_tool],
#             )

#             send_email_task = Task(
#                 description=(
#                     "Send the generated PDF report to the user's email address. "
#                     "Inputs required: receiver_email, subject, body, and attachment_path."
#                 ),
#                 expected_output="The email is sent or an error message is returned.",
#                 agent=Agent(
#                     role="Email Sender",
#                     goal="Send the PDF report via email",
#                     backstory="This agent sends the generated PDF report as an email attachment to the user.",
#                     verbose=True,
#                     llm=llm,
#                     tools=[email_tool],
#                     allow_delegation=False,
#                 ),
#                 tools=[email_tool],
#             )

#             rag_crew = Crew(
#                 agents=[
#                     Router_Agent,
#                     Retriever_Agent,
#                     ReportGeneratorAgent,
#                 ],
#                 tasks=[
#                     router_task,
#                     retriever_task,
#                     generate_financial_report_task,
#                 ],
#                 verbose=True,
#             )

#             result = rag_crew.kickoff(inputs={"question": question, "type": "str"})

#             pdf = MarkdownPdf(toc_level=1)
#             pdf.add_section(Section(result.raw))
#             pdf_file = "Report.pdf"
#             pdf.save(pdf_file)

#             email_input = {
#                 "receiver_email": email_address,
#                 "subject": "Financial Report",
#                 "body": f"Hello,\n\nPlease find attached the financial report for your request: {question}\n\nRegards,\nFargo Assist",
#                 "attachment_path": pdf_file,
#             }

#             email_response = send_email_task.agent.tools[0]._run(email_input)

#             if "successfully" in email_response.lower():
#                 st.success("Report generated and email sent successfully!")
#                 st.download_button('Download Report', pdf)
#             else:
#                 st.error(f"There was an error sending the email: {email_response}")

#         else:
#             st.warning("Please enter both a question and your email address.")


# if __name__ == "__main__":
#     main()


import streamlit as st
import os
import smtplib
from email.message import EmailMessage
from langchain_openai import ChatOpenAI
from crewai_tools import PDFSearchTool
from crewai import Crew, Task, Agent
from crewai.tools import BaseTool
from pydantic import Field
from langchain_community.utilities import GoogleSerperAPIWrapper
from markdown_pdf import MarkdownPdf, Section
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource


def main():
    st.title("Fargo Assist")
    st.write(
        "Enter your query below. Once the report is generated, it will be sent to your email."
    )

    # User inputs
    question = st.text_input("How can I assist you today?")
    email_address = st.text_input("Enter your email address:")

    # Drop-down for writing style selection
    writing_style = st.selectbox(
        "Select Report Writing Style",
        options=["Detailed", "Short", "Summary", "Technical"],
    )

    uploaded_files = st.file_uploader(
        "Upload relevant PDFs",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if st.button("Submit"):
        if question and email_address:
            st.info("Generating your financial report. Please wait...")

            # Process file uploads
            upload_folder = "knowledge\\uploads"
            os.makedirs(upload_folder, exist_ok=True)
            uploaded_file_paths = []
            if uploaded_files is not None:
                for file in uploaded_files:
                    file_path = os.path.join(
                        "D:\\Programming\\phi\\phi\\knowledge\\uploads", file.name
                    )
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    # Use relative path for further processing
                    uploaded_file_paths.append(os.path.join("uploads", file.name))

            base_lst = os.listdir(path="knowledge\\base")
            base_path_list = [os.path.join("base", f) for f in base_lst]

            all_pdf_paths = base_path_list + uploaded_file_paths

            pdf_source = PDFKnowledgeSource(file_paths=all_pdf_paths)

            # Initialize LLM
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

            # Initialize agents with a modified prompt including the writing style.
            Router_Agent = Agent(
                role="Router",
                goal="Route user question to a vectorstore or web search",
                backstory=(
                    "You are an expert at routing a user question to a vectorstore or web search. "
                    "Use the vectorstore for questions on the user information. "
                    "Use the vectorstore when the word 'report' is used or when you are asked to generate a report. "
                    "Use web-search for questions on latest news or recent topics. "
                    "Use generation for generic questions otherwise."
                ),
                verbose=True,
                allow_delegation=False,
                llm=llm,
            )

            Retriever_Agent = Agent(
                role="Retriever",
                goal="Retrieve data from the vectorstore and consolidate it into text format. Include all details and convert it into text format. Do not modify any information.",
                backstory=(
                    "You are a financial data processor. "
                    "You collect and consolidate all financial data about a person. "
                    "Use all the information in the document and convert it into text format."
                ),
                verbose=True,
                knowledge_sources=[pdf_source],
                allow_delegation=False,
                llm=llm,
            )

            # Note: The writing style is injected into the ReportGeneratorAgent's goal/backstory.
            ReportGeneratorAgent = Agent(
                role="Financial Report Compiler",
                goal=f"Compile the extracted data into a financial history report for the customer requesting {{question}}. "
                f"The report should be written in a {writing_style.lower()} style.",
                backstory=(
                    "As a financial report compiler, you specialize in transforming raw data into comprehensive reports. "
                    "Your attention to detail ensures that each report is tailored to meet the specific needs of the customer. "
                    "Any derivable parameters in the report must be calculated by you."
                ),
                verbose=True,
                allow_delegation=False,
                knowledge_sources=[pdf_source],
                llm=llm,
            )

            # Define custom tools

            class PDFSearchTool(BaseTool):
                name: str = "Search a PDF's content"
                description: str = (
                    "A tool that can be used to semantically search the content of the provided PDF. "
                    "Make sure to supply a query string."
                )
                pdf: str

                def _run(self, query: str) -> str:
                    if not isinstance(query, str):
                        raise ValueError(
                            f"Expected query to be a string, got {type(query).__name__}: {query}"
                        )
                    return f"Searching in PDF '{self.pdf}' for query: '{query}'"

            class SearchTool(BaseTool):
                name: str = "Search"
                description: str = (
                    "Useful for search-based queries. Use this to find current information about interest rates, markets, companies, and trends."
                )
                search: GoogleSerperAPIWrapper = Field(
                    default_factory=GoogleSerperAPIWrapper
                )

                def _run(self, query: str) -> str:
                    if not isinstance(query, str):
                        raise ValueError(
                            f"Expected query to be a string, got {type(query).__name__}: {query}"
                        )
                    try:
                        return self.search.run(query)
                    except Exception as e:
                        return f"Error performing search: {str(e)}"

            class GenerationTool(BaseTool):
                name: str = "Generation_tool"
                description: str = (
                    "Useful for generic-based queries. Use this to find information based on your own knowledge."
                )

                def _run(self, query: str) -> str:
                    if not isinstance(query, str):
                        raise ValueError(
                            f"Expected query to be a string, got {type(query).__name__}: {query}"
                        )
                    llm_local = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
                    return llm_local.invoke(query)

            class EmailTool(BaseTool):
                name: str = "Email Tool"
                description: str = (
                    "Sends an email with a PDF attachment. Input should include receiver_email, subject, body, and attachment_path."
                )
                sender_email: str = Field(
                    default_factory=lambda: os.environ.get("SENDER_EMAIL")
                )
                sender_password: str = Field(
                    default_factory=lambda: os.environ.get("SENDER_PASSWORD")
                )

                def _run(self, input_data: dict) -> str:
                    receiver_email = input_data.get("receiver_email")
                    subject = input_data.get("subject")
                    body = input_data.get("body")
                    attachment_path = input_data.get("attachment_path")
                    if not (receiver_email and subject and body and attachment_path):
                        return "Missing parameters for sending email."

                    msg = EmailMessage()
                    msg["Subject"] = subject
                    msg["From"] = self.sender_email
                    msg["To"] = receiver_email
                    msg.set_content(body)

                    with open(attachment_path, "rb") as f:
                        file_data = f.read()
                        file_name = os.path.basename(attachment_path)
                    msg.add_attachment(
                        file_data,
                        maintype="application",
                        subtype="pdf",
                        filename=file_name,
                    )

                    try:
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                            smtp.login(self.sender_email, self.sender_password)
                            smtp.send_message(msg)
                        return "Email sent successfully."
                    except Exception as e:
                        return f"Error sending email: {e}"

            generation_tool = GenerationTool()
            web_search_tool = SearchTool()
            pdf_search_tool = PDFSearchTool(pdf="base.pdf")
            email_tool = EmailTool()

            router_task = Task(
                description=(
                    "Analyse the keywords in the question {question}. "
                    "Based on the keywords decide whether it is eligible for a vectorstore search or a web search or generation. "
                    "Return a single word 'vectorstore' if it is eligible for vectorstore search. "
                    "Return a single word 'websearch' if it is eligible for web search. "
                    "Return a single word 'generate' if it is eligible for generation. "
                    "Do not provide any other preamble or explanation."
                ),
                expected_output=(
                    "Give a choice 'websearch' or 'vectorstore' or 'generate' based on the question. "
                    "Do not provide any other preamble or explanation."
                ),
                agent=Router_Agent,
            )

            retriever_task = Task(
                description=(
                    "Based on the response from the router task, extract information for the question {question} with the help of the respective tool. "
                    "Use the web_search_tool to retrieve information from the web if the router task output is 'websearch'. "
                    "Use the pdf_search_tool to retrieve information from the vectorstore if the router task output is 'vectorstore'. "
                    "Otherwise, generate the output based on your own knowledge if the router task output is 'generate'."
                ),
                expected_output=(
                    "Analyze the output of the 'router_task'. "
                    "If the response is 'websearch', then use the web_search_tool; if it is 'vectorstore', then use the pdf_search_tool; "
                    "if it is 'generate', then use the generation_tool. "
                    "Return the router's output appended with the extracted text."
                ),
                agent=Retriever_Agent,
                context=[router_task],
                tools=[pdf_search_tool, web_search_tool, generation_tool],
            )

            generate_financial_report_task = Task(
                description=(
                    "Based on the response from the retriever task, help the customer by generating a financial report for the request {question}. "
                    "Ensure the report is clear, concise, and tailored to the customer's needs in a "
                    + writing_style.lower()
                    + " style."
                ),
                expected_output=(
                    "Analyze the output of the 'retriever_task'. "
                    "If it starts with 'websearch', return a consolidated answer; "
                    "if it starts with 'vectorstore', return a detailed financial report with all relevant details; "
                    "if it starts with 'generate', return a consolidated answer."
                ),
                agent=ReportGeneratorAgent,
                context=[retriever_task],
                tools=[generation_tool],
            )

            send_email_task = Task(
                description=(
                    "Send the generated PDF report to the user's email address. "
                    "Inputs required: receiver_email, subject, body, and attachment_path."
                ),
                expected_output="The email is sent or an error message is returned.",
                agent=Agent(
                    role="Email Sender",
                    goal="Send the PDF report via email",
                    backstory="This agent sends the generated PDF report as an email attachment to the user.",
                    verbose=True,
                    llm=llm,
                    tools=[email_tool],
                    allow_delegation=False,
                ),
                tools=[email_tool],
            )

            rag_crew = Crew(
                agents=[Router_Agent, Retriever_Agent, ReportGeneratorAgent],
                tasks=[router_task, retriever_task, generate_financial_report_task],
                verbose=True,
            )

            # Kickoff the multi-agent chain
            result = rag_crew.kickoff(inputs={"question": question, "type": "str"})

            # Generate PDF using MarkdownPdf
            pdf = MarkdownPdf(toc_level=1)
            pdf.add_section(Section(result.raw))
            pdf_file = "Report.pdf"
            pdf.save(pdf_file)

            # OPTIONAL: Analyze the report's final verdict / sentiment.
            # For example, you could look for keywords or run another LLM classification.
            # Here we simply use a basic check:
            report_text_lower = result.raw.lower()
            if "approved" in report_text_lower:
                verdict_message = "Congratulations! Your financial report indicates a positive outcome."
            elif "declined" in report_text_lower:
                verdict_message = (
                    "Unfortunately, the report indicates a less favorable outcome."
                )
            else:
                verdict_message = (
                    "Please review the attached report for further details."
                )

            # Generate a custom email body based on the verdict.
            email_body = f"Hello,\n\nPlease find attached the financial report for your request: {question}.\n\n{verdict_message}\n\nRegards,\nFargo Assist"

            email_input = {
                "receiver_email": email_address,
                "subject": "Financial Report",
                "body": email_body,
                "attachment_path": pdf_file,
            }

            email_response = send_email_task.agent.tools[0]._run(email_input)

            if "successfully" in email_response.lower():
                st.success("Report generated and email sent successfully!")
                st.download_button("Download Report", pdf)
            else:
                st.error(f"There was an error sending the email: {email_response}")
        else:
            st.warning("Please enter both a question and your email address.")


if __name__ == "__main__":
    main()
