from modules.search import Search
from modules.scrapper import Scraper
from modules.email import EmailModule
from modules.llm import LLMModule
from modules.filter import FilterModule
from utils.helpers import is_sufficient_content, is_search_blocked
from modules.exceptions.exceptions import InsufficientContentError, SearchBlockedError


class WorkflowFacade:
    def __init__(self):
        self.search = Search()
        self.scraper = Scraper()
        self.filter = FilterModule()
        self.llm = LLMModule()
        self.email = EmailModule()

    def process_topic(
        self,
        topic: str,
        mode: str = "lead",
        max_results: int = 5,
        receipient_name: str = "",
        sender_company_summary: str = None,
    ):
        # Step 1: Search
        search_html = self.search.search(topic, mode)

        # Step 2: filter contents and raise exception
        self.filter.filter_insufficient_and_blocked_content(search_html, topic)

        # Step 3: Scrape links
        page_contents = self.scraper.extract_and_scrape(search_html, max_results)

        # Step 4: Filter content
        filtered_contents = self.filter.filter_page_contents(
            tuple(page_contents), topic
        )

        # Step 5: LLM Processing
        llm_result = None


        if mode == "lead":
            summary, email_body, subject = self.llm.generate_summary_email(
                topic, filtered_contents, mode, sender_company_summary, receipient_name
            )

            email_data = self.email.compose_email(
                receipient_name, subject, email_body
            )

            llm_result = {
                "summary": summary,
                "email": email_data,
                "content": filtered_contents,
                "content_length": len(filtered_contents),
            }
        else:
            summary = self.llm.generate_summary(topic, filtered_contents, mode)
            llm_result = {
                "summary": summary,
                "topic": topic,
                "content": filtered_contents,
                "content_length": len(filtered_contents),
            }

        return llm_result
