"""
Custom exceptions for Clew Directive with user-friendly error messages.

All exceptions include:
- user_message: What to show the user (friendly, actionable)
- technical_message: What to log (detailed, for debugging)
- retry_allowed: Whether the user should try again
- http_status: Appropriate HTTP status code
"""


class ClewException(Exception):
    """Base exception for all Clew Directive errors."""
    
    def __init__(
        self,
        user_message: str,
        technical_message: str = "",
        retry_allowed: bool = True,
        http_status: int = 500,
    ):
        self.user_message = user_message
        self.technical_message = technical_message or user_message
        self.retry_allowed = retry_allowed
        self.http_status = http_status
        super().__init__(self.technical_message)


class ValidationError(ClewException):
    """User input validation failed."""
    
    def __init__(self, field: str, issue: str):
        super().__init__(
            user_message=f"Please check your {field}: {issue}",
            technical_message=f"Validation error: {field} - {issue}",
            retry_allowed=True,
            http_status=400,
        )


class BedrockTimeoutError(ClewException):
    """Bedrock API call timed out."""
    
    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            user_message=(
                "That took longer than expected. Our AI is thinking hard! "
                "Please try again in a moment."
            ),
            technical_message=f"Bedrock timeout: {operation} exceeded {timeout_seconds}s",
            retry_allowed=True,
            http_status=504,
        )


class BedrockThrottleError(ClewException):
    """Bedrock API rate limit exceeded."""
    
    def __init__(self):
        super().__init__(
            user_message=(
                "We're experiencing high traffic right now. "
                "Please wait a moment and try again."
            ),
            technical_message="Bedrock throttling: rate limit exceeded",
            retry_allowed=True,
            http_status=429,
        )


class InvalidLLMResponseError(ClewException):
    """LLM returned invalid or unparseable response."""
    
    def __init__(self, operation: str, details: str):
        super().__init__(
            user_message=(
                "We encountered an error processing your request. "
                "Please try again."
            ),
            technical_message=f"Invalid LLM response in {operation}: {details}",
            retry_allowed=True,
            http_status=500,
        )


class ResourceLoadError(ClewException):
    """Failed to load resources from knowledge base."""
    
    def __init__(self, domain: str, details: str):
        super().__init__(
            user_message=(
                "We're having trouble loading our resource directory. "
                "Please try again in a few minutes."
            ),
            technical_message=f"Resource load failed for domain={domain}: {details}",
            retry_allowed=True,
            http_status=503,
        )


class NoResourcesFoundError(ClewException):
    """No resources found for the requested domain."""
    
    def __init__(self, domain: str):
        super().__init__(
            user_message=(
                f"We don't have resources for '{domain}' yet. "
                "Please check back soon!"
            ),
            technical_message=f"No resources found for domain={domain}",
            retry_allowed=False,
            http_status=404,
        )


class PDFGenerationError(ClewException):
    """PDF generation failed."""
    
    def __init__(self, details: str):
        super().__init__(
            user_message=(
                "We couldn't generate your PDF, but your learning path is ready below. "
                "You can still access all the links here."
            ),
            technical_message=f"PDF generation failed: {details}",
            retry_allowed=False,  # Path is still usable without PDF
            http_status=200,  # Not a failure - partial success
        )


class SessionExpiredError(ClewException):
    """Session data expired or not found."""
    
    def __init__(self):
        super().__init__(
            user_message=(
                "Your session has expired. Let's start fresh!"
            ),
            technical_message="Session expired or not found",
            retry_allowed=True,
            http_status=410,
        )


class RefinementLimitError(ClewException):
    """User exceeded refinement limit."""
    
    def __init__(self, limit: int):
        super().__init__(
            user_message=(
                f"You've reached the refinement limit ({limit} attempts). "
                "Let's start over with a fresh assessment."
            ),
            technical_message=f"Refinement limit exceeded: {limit}",
            retry_allowed=False,
            http_status=429,
        )
