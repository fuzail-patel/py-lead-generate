class EmailModule:
    """
    Formats AI-generated outreach messages into professional emails.
    Supports both plain text and HTML outputs, with dynamic sender info.
    """

    def __init__(self, **kwargs):
        self.sender_name = kwargs.get("sender_name", "")
        self.sender_title = kwargs.get("sender_title", "")
        self.sender_company = kwargs.get("sender_company", "")
        self.sender_phone = kwargs.get("sender_phone", "")
        self.sender_email = kwargs.get("sender_email", "")
        self.sender_website = kwargs.get("sender_website", "")
        self.sender_address = kwargs.get("sender_address", "")

    def set_email_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def _render_html(self, content: str) -> str:
        """Helper: wrap the email content in professional HTML format."""
        # Replace newlines BEFORE using in f-string
        content_html = content.replace('\n', '<br>')
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height:1.5;">
                <p>{content_html}</p>
                <br><br>
                <p style="font-size:0.9em; color:#555;">
                    Regards,<br>
                    <strong>{self.sender_name}</strong><br>
                    {self.sender_title}<br>
                    {self.sender_company}<br>
                    {self.sender_phone}<br>
                    <a href="mailto:{self.sender_email}">{self.sender_email}</a><br>
                    <a href="{self.sender_website}">{self.sender_website}</a><br>
                    {self.sender_address}
                </p>
            </body>
        </html>
        """.strip()

    def compose_email(self, recipient_name: str, subject: str = None, email_body: str = None, html: bool = False):
        """Generate a polished outreach email in plain text or HTML.
        
        Note: The email_body should already be complete from the LLM with no placeholders.
        This method only formats it with sender information.
        """
        sub = subject or f"Outreach from {self.sender_company}"
        content = "\n\n".join(filter(None, [email_body]))
        # No placeholder replacement - AI generates complete emails

        if html:
            body = self._render_html(content)
        else:
            body = f"{content}\n\n---\n\nBest regards,\n{self.sender_name}\n{self.sender_title}\n{self.sender_company}\n{self.sender_phone}\n{self.sender_email}\n{self.sender_website}\n{self.sender_address}"

        return {"subject": sub.strip(), "body": body.strip()}
