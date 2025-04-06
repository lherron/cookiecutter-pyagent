"""
FastmailClient for interacting with Fastmail JMAP API.
"""

import logging
from typing import Dict, List, Any, Optional, cast, Union, TypeVar, Generic

from jmapc import (
    Client, 
    EmailQueryFilterCondition, 
    MailboxQueryFilterCondition,
    Ref,
    Address,
    Email,
    EmailAddress,
    EmailBodyPart,
    EmailBodyValue,
    EmailHeader,
    EmailSubmission,
    Envelope
)
from jmapc.methods import (
    EmailGet, 
    EmailQuery, 
    EmailGetResponse,
    MailboxGet, 
    MailboxQuery, 
    MailboxGetResponse,
    EmailSet, 
    EmailSubmissionSet,
    IdentityGet,
    IdentityGetResponse
)
from {{cookiecutter.project_slug}}.config import JMAPConfig
import markdown
from markdown.extensions import codehilite
import os

logger = logging.getLogger("{{cookiecutter.project_slug}}.util.fastmail_client")

# Type variable for response types
T = TypeVar('T')

class FastmailClient:
    """Client for interacting with Fastmail via JMAP API."""

    def __init__(self, jmap_config: JMAPConfig) -> None:
        """Initialize the Fastmail client with JMAP configuration.

        Args:
            jmap_config: JMAP configuration object from config.py.
        """
        self.jmap_config = jmap_config
        
        # Extract just the hostname without protocol
        server_url = jmap_config.server_url
        if server_url.startswith(("http://", "https://")):
            server_url = server_url.split("//", 1)[1]
            
        # Remove any trailing path or slashes
        server_url = server_url.split("/", 1)[0]
            
        logger.info(f"Initializing JMAP client with host: {server_url}")
        
        if not jmap_config.api_key:
            raise ValueError("API key is required to initialize Fastmail client")
            
        try:
            self.jmap_client = Client.create_with_api_token(
                host=server_url,
                api_token=jmap_config.api_key
            )
            logger.info("JMAP client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize JMAP client: {e}")
            raise
            
        # self._test_connection()

    def _test_connection(self) -> None:
        """Test the connection to the Fastmail JMAP server.

        Raises:
            Exception: If the connection fails or no mailboxes are found.
        """
        try:
            query = MailboxQuery()
            query_result = self.jmap_client.request(query)
            if not hasattr(query_result, 'ids') or not query_result.ids:
                raise Exception("No mailboxes found")
            get_result = self.jmap_client.request(MailboxGet(ids=query_result.ids))
            assert isinstance(get_result, MailboxGetResponse), "Expected MailboxGetResponse"
            mailboxes = get_result.data
            logger.info(f"Successfully connected to Fastmail. Found {len(mailboxes)} mailboxes.")
        except Exception as e:
            logger.error(f"Failed to connect to Fastmail: {e}")
            raise

    def get_folder_id(self, folder_name: str) -> str:
        """Get the ID of a folder by its name.

        Args:
            folder_name: Name of the folder (e.g., "Inbox").

        Returns:
            str: Folder ID.

        Raises:
            ValueError: If the folder is not found.
        """
        try:
            query_method = MailboxQuery(filter=MailboxQueryFilterCondition(name=folder_name))
            query_result = self.jmap_client.request(query_method)
            if not hasattr(query_result, 'ids') or not query_result.ids:
                raise ValueError(f"Folder '{folder_name}' not found.")
            get_method = MailboxGet(ids=query_result.ids)
            get_result = self.jmap_client.request(get_method)
            assert isinstance(get_result, MailboxGetResponse), "Expected MailboxGetResponse"
            mailboxes = get_result.data
            if not mailboxes:
                raise ValueError(f"Folder '{folder_name}' not found.")
            logger.info(f"Found folder '{folder_name}' with ID: {mailboxes[0].id}")
            return str(mailboxes[0].id)  # Ensure we return a string
        except Exception as e:
            logger.error(f"Error getting folder ID for '{folder_name}': {e}")
            raise ValueError(f"Error getting folder ID for '{folder_name}': {e}")

    def get_unread_messages(self, folder_id: str) -> List[Dict[str, Any]]:
        """Fetch unread messages from the specified folder.

        Args:
            folder_id: ID of the target folder.

        Returns:
            List of unread message dictionaries.
        """
        try:
            query_method = EmailQuery(
                filter=EmailQueryFilterCondition(
                    in_mailbox=folder_id,
                    not_keyword="$seen"
                ),
                sort=[{"property": "receivedAt", "isAscending": False}]  # type: ignore
            )
            query_result = self.jmap_client.request(query_method)
            if not hasattr(query_result, 'ids') or not query_result.ids:
                logger.info("No unread messages found in the folder.")
                return []
            email_ids = query_result.ids
            logger.info(f"Found {len(email_ids)} unread messages, fetching details...")
            get_method = EmailGet(
                ids=email_ids,
                properties=["id", "threadId", "mailboxIds", "keywords", "from", "to",
                            "subject", "receivedAt", "htmlBody", "textBody", "messageId",
                            "bodyValues", "bodyStructure", "preview"],
                fetch_all_body_values=True
            )
            get_result = self.jmap_client.request(get_method)
            assert isinstance(get_result, EmailGetResponse), "Expected EmailGetResponse"
            messages = get_result.data
            if not messages:
                logger.info("No message details retrieved.")
                return []
                
            # Log message structure for debugging
            if messages:
                sample_msg = messages[0]
                logger.debug(f"Email structure sample: id={sample_msg.id}")
                for attr in ["html_body", "text_body", "body_values"]:
                    if hasattr(sample_msg, attr):
                        attr_value = getattr(sample_msg, attr)
                        logger.debug(f"{attr} present: {bool(attr_value)}")
                        if attr == "body_values" and attr_value:
                            logger.debug(f"body_values keys: {attr_value.keys()}")
                
            message_dicts: List[Dict[str, Any]] = []
            for msg in messages:
                # Create a dictionary to store the message data
                msg_dict: Dict[str, Any] = {
                    "id": msg.id,
                    "threadId": msg.thread_id,
                    "mailboxIds": msg.mailbox_ids,
                    "keywords": msg.keywords,
                    "from": [{"name": addr.name, "email": addr.email} for addr in (msg.mail_from or [])],
                    "to": [{"name": addr.name, "email": addr.email} for addr in (msg.to or [])],
                    "subject": msg.subject,
                    "receivedAt": msg.received_at,
                    "messageId": msg.message_id
                }
                
                # Add body content if available
                html_body_added = False
                text_body_added = False
                
                # Try to extract HTML body content
                if hasattr(msg, "html_body") and msg.html_body:
                    logger.debug(f"Processing HTML body for message {msg.id}")
                    html_parts = msg.html_body
                    for html_part in html_parts:
                        # Log the HTML part details for debugging
                        logger.debug(f"HTML part: {vars(html_part)}")
                        
                        if hasattr(html_part, "part_id") and hasattr(msg, "body_values") and msg.body_values is not None:
                            part_id = html_part.part_id
                            if part_id is not None and part_id in msg.body_values:
                                msg_dict["htmlBody"] = msg.body_values[part_id].value
                                html_body_added = True
                                logger.debug(f"Added HTML body from part_id: {part_id}")
                                break
                
                # Try to extract Text body content
                if hasattr(msg, "text_body") and msg.text_body:
                    logger.debug(f"Processing text body for message {msg.id}")
                    text_parts = msg.text_body
                    for text_part in text_parts:
                        # Log the text part details for debugging
                        logger.debug(f"Text part: {vars(text_part)}")
                        
                        if hasattr(text_part, "part_id") and hasattr(msg, "body_values") and msg.body_values is not None:
                            part_id = text_part.part_id
                            if part_id is not None and part_id in msg.body_values:
                                msg_dict["textBody"] = msg.body_values[part_id].value
                                text_body_added = True
                                logger.debug(f"Added text body from part_id: {part_id}")
                                break
                
                # If we couldn't extract the body content, log a warning
                if not html_body_added and not text_body_added:
                    logger.warning(f"Could not extract body content for message {msg.id}")
                    # Add placeholder content
                    msg_dict["textBody"] = "[Email content could not be retrieved]"
                
                message_dicts.append(msg_dict)
            
            logger.info(f"Retrieved {len(message_dicts)} unread messages.")
            for msg_dict in message_dicts:
                logger.info(f"Message - From: {msg_dict['from'][0]['email']}, Subject: {msg_dict['subject']}")
                
            return message_dicts
                
        except Exception as e:
            logger.error(f"Error getting unread messages: {e}")
            return []

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read by setting the $seen flag.

        Args:
            message_id: ID of the message to mark.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            result = self.jmap_client.request(
                EmailSet(
                    update={message_id: {"keywords": {"$seen": True}}}
                )
            )
            logger.info(f"Marked message {message_id} as read.")
            return True
        except Exception as e:
            logger.error(f"Failed to mark message {message_id} as read: {e}")
            return False

    def archive_message(self, message_id: str, archive_folder_id: str) -> bool:
        """Move a message to the archive folder.

        Args:
            message_id: ID of the message to archive.
            archive_folder_id: ID of the archive folder.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            result = self.jmap_client.request(
                EmailSet(
                    update={message_id: {"mailboxIds": {archive_folder_id: True}}}
                )
            )
            logger.info(f"Archived message {message_id}.")
            return True
        except Exception as e:
            logger.error(f"Failed to archive message {message_id}: {e}")
            return False

    def send_reply(self, message: Dict[str, Any], html_response: str, markdown_response: str) -> bool:
        """Send a reply to the original sender.

        Args:
            message: Original message dictionary.
            html_response: HTML version of the response.
            markdown_response: Markdown version for plaintext part.

        Returns:
            bool: True if the reply was sent successfully, False otherwise.
        """
        if not self.jmap_config.agent_email_address:
            logger.error("Email address is not configured.")
            raise ValueError("Email address is required to send replies.")
        
        # Get email addresses
        to_email = message["from"][0]["email"]
        to_name = message["from"][0].get("name", to_email)
        # Create quoted HTML version of original message
        original_text = message.get("textBody", "")
        
        try:
            # First get the Drafts folder ID and identity details
            results = self.jmap_client.request([
                MailboxQuery(filter=MailboxQueryFilterCondition(name="Drafts")),
                MailboxGet(ids=Ref("/ids")),
                IdentityGet()
            ])
            
            # Get Drafts folder ID
            assert isinstance(
                results[1].response, MailboxGetResponse
            ), "Error in Mailbox/get method"
            mailbox_data = results[1].response.data
            if not mailbox_data:
                logger.error("Drafts folder not found")
                return False
            
            drafts_mailbox_id = mailbox_data[0].id
            logger.info(f"Drafts folder ID: {drafts_mailbox_id}")
            
            # Get identity
            assert isinstance(
                results[2].response, IdentityGetResponse
            ), "Error in Identity/get method"
            identity_data = results[2].response.data
            if not identity_data:
                logger.error("No identities found")
                return False
            
            # Find the identity with the email address that matches the config
            identity = next((i for i in identity_data if i.email == self.jmap_config.agent_email_address), None)
            if not identity:
                logger.error("No identity found with the email address in the config")
                return False
            logger.info(f"Using identity: {identity.name} <{identity.email}>")
            
            # Read the CSS file
            css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'code_highlight.css')
            try:
                with open(css_path, 'r') as f:
                    css_content = f.read()
                
                # Wrap HTML content with CSS
                html_with_css = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                    {css_content}
                    </style>
                </head>
                <body>
                    {html_response}
                </body>
                </html>
                """
            except Exception as e:
                logger.warning(f"Failed to include CSS for code highlighting: {e}")
                html_with_css = html_response
            
            # Create reply email
            results = self.jmap_client.request(
                [
                    # Create a draft email in the Drafts mailbox
                    EmailSet(
                        create=dict(
                            draft=Email(
                                mail_from=[
                                    EmailAddress(name=identity.name, email=identity.email)
                                ],
                                to=[
                                    EmailAddress(name="", email=self.jmap_config.user_email_address)
                                ],
                                subject=f"Re: {message['subject']}",
                                keywords={"$draft": True},
                                mailbox_ids={str(drafts_mailbox_id): True},
                                body_values=dict(
                                    body=EmailBodyValue(value=f"{markdown_response}\n\nOn {message.get('receivedAt', 'earlier')}, {to_email} wrote:\n> {original_text.replace('\n', '\n> ')}"),
                                    html=EmailBodyValue(value=html_with_css)
                                ),
                                text_body=[
                                    EmailBodyPart(part_id="body", type="text/plain")
                                ],
                                html_body=[
                                    EmailBodyPart(part_id="html", type="text/html")
                                ],
                            )
                        )
                    ),
                    # Send the created draft email, and delete from the Drafts mailbox on
                    # success
                    EmailSubmissionSet(
                        on_success_destroy_email=["#emailToSend"],
                        create=dict(
                            emailToSend=EmailSubmission(
                                email_id="#draft",
                                identity_id=identity.id,
                                envelope=Envelope(
                                    mail_from=Address(email=identity.email),
                                    rcpt_to=[Address(email=self.jmap_config.user_email_address)],
                                ),
                            )
                        ),
                    ),
                ]
            )

            # Check results
            create_result = results[0].response
            submit_result = results[1].response
            
            logger.info(f"Create result: {create_result}")
            logger.info(f"Submit result: {submit_result}")
            return True
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")
            return False
            
    def send_email(
        self, 
        to_addresses: List[Dict[str, str]], 
        subject: str, 
        markdown_content: str, 
        from_email: Optional[str] = None,
        cc_addresses: Optional[List[Dict[str, str]]] = None,
        bcc_addresses: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """Send a generic email.

        Args:
            to_addresses: List of dictionaries with 'name' and 'email' keys
            subject: Subject line of the email
            markdown_content: Markdown content of the email
            from_email: Email address to send from (defaults to agent_email_address in config)
            cc_addresses: Optional list of CC recipients with 'name' and 'email' keys
            bcc_addresses: Optional list of BCC recipients with 'name' and 'email' keys

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        # Use from_email parameter if provided, otherwise use agent_email_address from config
        sender_email = from_email
        
        if not sender_email:
            logger.error("Email address is not configured.")
            raise ValueError("Sending email address is required to send emails.")
        
        try:
            # First get the Drafts folder ID and identity details
            results = self.jmap_client.request([
                MailboxQuery(filter=MailboxQueryFilterCondition(name="Drafts")),
                MailboxGet(ids=Ref("/ids")),
                IdentityGet()
            ])
            
            assert isinstance(
                results[1].response, MailboxGetResponse
            ), "Error in Mailbox/get method"
            # Get Drafts folder ID
            mailbox_data = results[1].response.data
            if not mailbox_data:
                logger.error("Drafts folder not found")
                raise ValueError("Drafts folder not found")
            
            drafts_mailbox_id = mailbox_data[0].id
            logger.info(f"Drafts folder ID: {drafts_mailbox_id}")
            
            # Get identity
            assert isinstance(
                results[2].response, IdentityGetResponse
            ), "Error in Identity/get method"
            identity_data = results[2].response.data
            if not identity_data:
                logger.error("No identities found")
                return False
            
            # Find the identity with the specified email address
            identity = next((i for i in identity_data if i.email == sender_email), None)
            if not identity:
                logger.error(f"No identity found with the email address: {sender_email}")
                return False
            logger.info(f"Using identity: {identity.name} <{identity.email}>")
            
            # Prepare recipient lists
            email_to = [EmailAddress(name=addr.get("name", ""), email=addr["email"]) for addr in to_addresses]
            email_cc = [EmailAddress(name=addr.get("name", ""), email=addr["email"]) for addr in (cc_addresses or [])]
            email_bcc = [EmailAddress(name=addr.get("name", ""), email=addr["email"]) for addr in (bcc_addresses or [])]
            
            # Create recipient list for envelope
            rcpt_to = [Address(email=addr["email"]) for addr in to_addresses]
            if cc_addresses:
                rcpt_to.extend([Address(email=addr["email"]) for addr in cc_addresses])
            if bcc_addresses:
                rcpt_to.extend([Address(email=addr["email"]) for addr in bcc_addresses])
            
            # Convert markdown to HTML
            html_content = markdown.markdown(
                markdown_content, 
                extensions=['tables', 'fenced_code', codehilite.CodeHiliteExtension(css_class='highlight')]
            )
            
            # Read the CSS file
            css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'code_highlight.css')
            try:
                with open(css_path, 'r') as f:
                    css_content = f.read()
                
                # Wrap HTML content with CSS
                html_with_css = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                    {css_content}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """
            except Exception as e:
                logger.warning(f"Failed to include CSS for code highlighting: {e}")
                html_with_css = html_content
            
            # Create and send email
            results = self.jmap_client.request(
                [
                    # Create a draft email in the Drafts mailbox
                    EmailSet(
                        create=dict(
                            draft=Email(
                                mail_from=[
                                    EmailAddress(name=identity.name, email=identity.email)
                                ],
                                to=email_to,
                                cc=email_cc if email_cc else None,
                                bcc=email_bcc if email_bcc else None,
                                subject=subject,
                                keywords={"$draft": True},
                                mailbox_ids={str(drafts_mailbox_id): True},
                                body_values=dict(
                                    body=EmailBodyValue(value=markdown_content),
                                    html=EmailBodyValue(value=html_with_css),
                                    attachment=EmailBodyValue(value=markdown_content)
                                ),
                                text_body=[
                                    EmailBodyPart(part_id="body", type="text/plain")
                                ],
                                html_body=[
                                    EmailBodyPart(part_id="html", type="text/html")
                                ],
                                attachments=[
                                    EmailBodyPart(
                                        part_id="attachment",
                                        type="text/markdown",
                                        name="content.md",
                                        disposition="attachment"
                                    )
                                ]
                            )
                        )
                    ),
                    # Send the created draft email, and delete from the Drafts mailbox on success
                    EmailSubmissionSet(
                        on_success_destroy_email=["#emailToSend"],  # DO NOT REMOVE THIS LINE
                        create=dict(
                            emailToSend=EmailSubmission(
                                email_id="#draft",
                                identity_id=identity.id,
                                envelope=Envelope(
                                    mail_from=Address(email=identity.email),
                                    rcpt_to=rcpt_to,
                                ),
                            )
                        ),
                    ),
                ]
            )

            # Check results
            create_result = results[0].response
            submit_result = results[1].response
            
            logger.info(f"Email sent to {', '.join([addr['email'] for addr in to_addresses])}")
            logger.debug(f"Create result: {create_result}")
            logger.debug(f"Submit result: {submit_result}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False