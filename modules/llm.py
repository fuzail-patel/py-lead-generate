import os
from openai import OpenAI
from constants.prompts import PROMPTS
import json

class LLMModule:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided or set in OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)

    def build_prompt(
        self, topic: str, content: str, mode: str = "lead", sender_company_summary: str = None, recipient_name: str = None
    ) -> str:
        """
        Build the full prompt for the AI based on mode and optional sender company summary.
        """
        if mode not in PROMPTS:
            mode = "general"
        
        # Build recipient instruction
        recipient_instruction = ""
        if mode == "lead":
            if recipient_name and recipient_name.strip():
                recipient_instruction = f"\n\nRECIPIENT NAME: {recipient_name.strip()}\nIMPORTANT: Address the email directly to '{recipient_name.strip()}' using their actual name. Do NOT use placeholders like [Recipient], [Name], or [Recipient Name]. Use the actual name provided."
            else:
                recipient_instruction = "\n\nIMPORTANT: Since no recipient name is provided, address the email to a generic but professional greeting such as 'Dear Team', 'Hello', 'Dear [Company Name] Team', or similar. Do NOT use placeholders like [Recipient], [Name], or [Recipient Name]. Use a complete, natural greeting."
        
        prompt = f"""
        {PROMPTS["base"]}

        {PROMPTS[mode]}

        TOPIC TO SUMMARIZE: {topic}
        {recipient_instruction}
        {"YOUR COMPANY SUMMARY (description of sender's company for context in lead email): " + sender_company_summary if sender_company_summary else ""}

        CONTENT TO ANALYZE:
        {content}

        Respond strictly in JSON with this structure:
        {{
            "summary": "Professional summary of the topic/company here in short paragraphs.",
            "email": {{
                "subject": "Concise, professional email subject here only applies if you generate lead emails",
                "body": "Full email body here addressing the recipient and referencing your company naturally only applies if you generate lead emails. The email must be complete with proper greeting - NO placeholders."
            }}
        }}
        """.strip()

        return prompt


    def generate_summary_email(
        self, topic: str, content: str, mode: str = "lead", sender_company_summary: str = None, recipient_name: str = None
    ):
        if mode != "lead":
            raise ValueError("generate_summary_email should only be used for lead emails")

        prompt = self.build_prompt(topic, content, mode, sender_company_summary, recipient_name)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=700,
                temperature=0.7,
            )

            output_text = response.choices[0].message.content.strip()
            try:
                parsed = json.loads(output_text)
                summary = parsed.get("summary", "")
                subject = parsed.get("email", "").get("subject", "100% Relevant Business Opportunity")
                email_body = parsed.get("email", "").get("body", "")
            except json.JSONDecodeError:
                summary = output_text[:300]
                email_body = output_text
                subject = "100% Relevant Business Opportunity"

            return summary, email_body, subject

        except Exception as e:
            summary = f"Summary of {topic} based on scraped content."
            email_body = f"Here is an overview of {topic}:\n\n{summary}"
            return summary, email_body, "100% Relevant Business Opportunity"


    def generate_summary(self, topic: str, content: str, mode: str = "general"):
        if mode not in ["general", "research"]:
            raise ValueError(
                "generate_summary is intended for general or research modes only"
            )

        prompt = self.build_prompt(topic, content, mode)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.6,
            )

            output_text = response.choices[0].message.content.strip()
            try:
                parsed = json.loads(output_text)
                return parsed.get("summary", output_text)
            except json.JSONDecodeError:
                return output_text

        except Exception as e:
            return f"Summary of {topic} based on scraped content."
