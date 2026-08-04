import re
import structlog

logger = structlog.get_logger(__name__)


class SecretScrubber:
    """Security engine for detecting and redacting sensitive credentials and secrets from text."""

    SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
        "aws_access_key": re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        "aws_secret_key": re.compile(
            r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?"
        ),
        "jwt_token": re.compile(r"\b(eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})\b"),
        "bearer_token": re.compile(r"(?i)bearer\s+([A-Za-z0-9_.~+/-]{20,})"),
        "gitlab_token": re.compile(r"\b(glpat-[0-9a-zA-Z_-]{20,})\b"),
        "slack_token": re.compile(r"\b(xox[b|p|a|r]-[0-9a-zA-Z-]{10,})\b"),
        "rsa_private_key": re.compile(
            r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]+?-----END \1PRIVATE KEY-----"
        ),
        "database_url_password": re.compile(
            r"(postgres|mysql|mongodb|redis)://[^:]+:([^@]+)@"
        ),
    }

    def scrub(self, text: str) -> str:
        """Redact sensitive secrets from input text string.

        Args:
            text: Raw input text (logs, prompts, or code diffs).

        Returns:
            Sanitized text with credentials replaced by redaction placeholders.
        """
        if not text:
            return ""

        scrubbed = text
        redacted_count = 0

        for secret_type, pattern in self.SECRET_PATTERNS.items():
            matches = list(pattern.finditer(scrubbed))
            if matches:
                redacted_count += len(matches)
                if secret_type == "database_url_password":
                    scrubbed = pattern.sub(r"\1://[REDACTED_USER]:[REDACTED_PASSWORD]@", scrubbed)
                elif secret_type == "bearer_token":
                    scrubbed = pattern.sub("Bearer [REDACTED_BEARER_TOKEN]", scrubbed)
                elif secret_type == "aws_secret_key":
                    scrubbed = pattern.sub("aws_secret_access_key=[REDACTED_AWS_SECRET]", scrubbed)
                else:
                    scrubbed = pattern.sub(f"[REDACTED_{secret_type.upper()}]", scrubbed)

        if redacted_count > 0:
            logger.info("secrets_scrubbed_from_text", redacted_count=redacted_count)

        return scrubbed


# Global Secret Scrubber Instance
secret_scrubber = SecretScrubber()
