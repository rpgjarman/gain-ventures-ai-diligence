import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional

class EmailClient:
    def __init__(self):
        self.email_user = os.getenv('EMAIL_USER', 'robertpj235@gmail.com')
        self.email_password = os.getenv('EMAIL_PASSWORD', 'rjiyoya2003')
        self.company_email = os.getenv('COMPANY_EMAIL', 'robert@gain.ventures')
        
        # Gmail SMTP configuration
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
    
    async def send_diligence_report(self, company_name: str, pdf_path: str, summary: str) -> bool:
        """Send diligence report to partners"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.company_email
            msg['Subject'] = f"AI Diligence Report: {company_name}"
            
            # Email body
            body = f"""
            New AI diligence report completed for: {company_name}
            
            Executive Summary:
            {summary[:500]}...
            
            Please review the attached detailed report and provide your decision on whether to proceed with outreach.
            
            To approve for outreach, update the record in Airtable with "Partner Decision" = "Approved"
            
            Best regards,
            Gain Ventures AI System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach PDF if it exists
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(pdf_path)}'
                )
                msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_user, self.company_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    async def send_outreach_email(self, company_email: str, subject: str, body: str, 
                                cc_emails: List[str] = None) -> bool:
        """Send outreach email to prospect"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.company_email
            msg['To'] = company_email
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            
            recipients = [company_email] + (cc_emails or [])
            text = msg.as_string()
            server.sendmail(self.company_email, recipients, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Error sending outreach email: {str(e)}")
            return False
    
    async def send_notification(self, subject: str, message: str, to_email: str = None) -> bool:
        """Send general notification email"""
        try:
            recipient = to_email or self.company_email
            
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = recipient
            msg['Subject'] = f"[Gain Ventures] {subject}"
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_user, recipient, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            return False