"""
Resource Verifier Tool — HTTP HEAD checks for URL liveness.

Used by:
    - Scout agent (runtime spot-checks)
    - Curator Lambda (weekly full verification)

Returns True if URL responds with 2xx/3xx, False otherwise.
Timeout: 5 seconds per URL to avoid blocking.
"""

import logging
import time
import urllib.request
import urllib.error

logger = logging.getLogger("clew.tool.verifier")

DEFAULT_TIMEOUT = 5  # seconds
DEFAULT_RETRIES = 2  # number of retries
RETRY_BACKOFF = 1  # seconds between retries
USER_AGENT = "ClewDirective/1.0 (resource-verification)"


def verify_url(url: str, timeout: int = DEFAULT_TIMEOUT, retries: int = DEFAULT_RETRIES) -> bool:
    """
    Check if a URL is live via HTTP HEAD request with retry logic.

    Args:
        url: The URL to verify.
        timeout: Request timeout in seconds.
        retries: Number of retry attempts on failure.

    Returns:
        True if the URL responds with a 2xx or 3xx status code.
        False if the URL is dead, redirects to an error, or times out after retries.
    """
    if not url or not url.startswith(("http://", "https://")):
        logger.warning("[tool:verifier] Invalid URL: %s", url[:100])
        return False

    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": USER_AGENT},
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.getcode()
                is_live = 200 <= status < 400
                if not is_live:
                    logger.info("[tool:verifier] Non-OK status %d for %s", status, url[:100])
                return is_live
        except urllib.error.HTTPError as e:
            logger.info("[tool:verifier] HTTP %d for %s (attempt %d/%d)", e.code, url[:100], attempt + 1, retries + 1)
            if attempt < retries:
                time.sleep(RETRY_BACKOFF * (attempt + 1))  # Exponential backoff
                continue
            return False
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            logger.info("[tool:verifier] Connection error for %s (attempt %d/%d): %s", url[:100], attempt + 1, retries + 1, str(e)[:100])
            if attempt < retries:
                time.sleep(RETRY_BACKOFF * (attempt + 1))  # Exponential backoff
                continue
            return False
        except Exception:
            logger.warning("[tool:verifier] Unexpected error for %s", url[:100], exc_info=True)
            return False
    
    return False
