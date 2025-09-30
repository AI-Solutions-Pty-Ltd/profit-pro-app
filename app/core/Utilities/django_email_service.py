import mimetypes
import time
from datetime import datetime, timedelta
from functools import wraps
from threading import Lock
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.mail.backends.smtp import EmailBackend


class EmailConnectionManager:
    _instance = None
    _lock = Lock()
    _connection: EmailBackend | None = None
    _last_used: datetime | None = None
    _connection_errors = 0

    # Configuration
    MAX_CONNECTION_AGE = timedelta(minutes=30)  # Create new connection after 30 minutes
    MAX_ERRORS = 3  # Create new connection after 3 errors

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def _is_connection_stale(self) -> bool:
        """Check if the current connection is too old."""
        if self._last_used is None:
            return True
        return datetime.now() - self._last_used > self.MAX_CONNECTION_AGE

    def _should_create_new_connection(self) -> bool:
        """Check if we need to create a new connection."""
        return (
            self._connection is None  # No existing connection
            or self._is_connection_stale()  # Connection is too old
            or self._connection_errors
            >= self.MAX_ERRORS  # Too many errors on this connection
        )

    def _close_existing_connection(self) -> None:
        """Safely close the existing connection if there is one."""
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                # If closing fails, we still want to create a new connection
                pass
            finally:
                self._connection = None
                self._last_used = None
                self._connection_errors = 0

    def _create_new_connection(self) -> None:
        """Create a new email connection and reset all counters."""
        self._connection = get_connection()
        self._last_used = datetime.now()
        self._connection_errors = 0

    def get_connection(self) -> EmailBackend:
        """Get an email connection from the pool, creating a new one if necessary.

        The connection will be reused until one of these conditions is met:
        - Connection is older than MAX_CONNECTION_AGE (30 minutes)
        - Connection has experienced MAX_ERRORS errors (3)
        - Connection is explicitly closed due to an error

        Returns:
            EmailBackend: A connection to the email server
        """
        with self._lock:
            if self._should_create_new_connection():
                self._close_existing_connection()
                self._create_new_connection()
            else:
                self._last_used = datetime.now()

            return self._connection

    def record_error(self) -> None:
        """Record that an error occurred with the current connection."""
        with self._lock:
            self._connection_errors += 1

    def close_connection(self):
        """Close the current connection if it exists."""
        with self._lock:
            if self._connection is not None:
                try:
                    self._connection.close()
                except Exception as _:
                    pass
                self._connection = None
                self._connection_attempts = 0


_connection_manager = EmailConnectionManager()


def convert_email_to_list(email: str | list[str]) -> list[str]:
    """Convert various email input formats to a list of email addresses.

    Args:
        email: Can be None, a single email string, or a list of email strings

    Returns:
        List[str]: List of email addresses, empty list if input is None

    Raises:
        ValueError: If email input is invalid
    """
    if not email:
        return []
    if isinstance(email, str):
        return [email]
    return email


def with_retries(max_retries: int = 3, initial_delay: float = 1.0):
    """Decorator that implements retry logic with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:  # Last attempt failed
                        raise last_exception from None

                    # Exponential backoff with jitter
                    jitter = (time.time() * 1000) % 0.1  # Small random jitter
                    time.sleep(delay + jitter)
                    delay *= 2  # Exponential backoff

            raise Exception(last_exception)  # Should never reach here

        return wrapper

    return decorator


def _send_email_internal(
    email: EmailMultiAlternatives,
    connection_manager: EmailConnectionManager,
) -> tuple[bool, str]:
    """Internal function to send email with error handling."""
    try:
        email.send(fail_silently=False)
        return True, "Email sent successfully"
    except Exception as e:
        # Record the error and close the connection
        connection_manager.record_error()
        if connection_manager._connection_errors >= connection_manager.MAX_ERRORS:
            connection_manager.close_connection()
        raise Exception(f"Failed to send email: {str(e)}") from e


def django_email_service(
    to: str | list[str],
    subject: str,
    plain_body: str = "",
    html_body: str = "",
    attachments: list[ContentFile] | None = None,  # In-memory file attachments
    from_email: str | None = None,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    cc: str | list[str] | None = None,
    bcc: str | list[str] | None = None,
) -> tuple[bool, str]:
    """Send an email using the connection pool with retry logic.

    This function will reuse SMTP connections when possible to improve performance.
    A single connection will be kept alive and reused until:
    - It's been open for 30 minutes
    - It encounters 3 errors
    - It's explicitly closed due to an error

    If sending fails, it will retry with exponential backoff:
    - 1st retry: Wait 1 second
    - 2nd retry: Wait 2 seconds
    - 3rd retry: Wait 4 seconds

    Args:
        to: Email address(es) to send to
        cc: Email address(es) to cc
        bcc: Email address(es) to bcc
        subject: Email subject
        plain_body: Plain text email body
        html_body: HTML email body
        attachments: List of files to attach
        from_email: Sender email address
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay between retries in seconds (default: 1.0)

    Returns:
        tuple[bool, str]: (success, message)
    """
    if bcc is None:
        bcc = []
    if cc is None:
        cc = []
    if attachments is None:
        attachments = []
    if not settings.USE_EMAIL:
        return True, "Email sending is disabled"
    try:
        # Get connection from the connection pool
        connection = _connection_manager.get_connection()

        # Prepare the email
        email = EmailMultiAlternatives(
            to=convert_email_to_list(to),
            cc=convert_email_to_list(cc),
            bcc=convert_email_to_list(bcc),
            subject=subject,
            from_email=from_email or settings.EMAIL_HOST_USER,
            connection=connection,
        )

        for file in attachments:
            # Guess MIME type from file extension
            mime_type, _ = mimetypes.guess_type(file.name)
            if mime_type is None:
                # Fallback to generic binary if can't determine type
                mime_type = "application/octet-stream"

            email.attach(file.name, file.read(), mime_type)

        # Set plain text version as the default body
        email.body = plain_body or html_body.replace("<br>", "\n").replace(
            "</p>", "\n\n"
        ).replace("<[^>]*>", "")

        # Add HTML version as an alternative
        if html_body:
            email.attach_alternative(html_body, "text/html")

        # Send email with retries
        @with_retries(max_retries=max_retries, initial_delay=initial_delay)
        def send_with_retries():
            return _send_email_internal(email, _connection_manager)

        return send_with_retries()

    except Exception as e:
        return False, f"Failed to send email after {max_retries} retries: {str(e)}"
