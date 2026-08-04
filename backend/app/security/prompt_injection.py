from dataclasses import dataclass, field
import re
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class InjectionScanResult:
    """Dataclass representing the result of a prompt injection security scan.

    Attributes:
        is_safe: True if no prompt injection patterns detected, else False.
        risk_score: Numerical risk score between 0.0 (safe) and 1.0 (malicious).
        detected_patterns: List of rule names triggered by the input text.
    """

    is_safe: bool
    risk_score: float
    detected_patterns: list[str] = field(default_factory=list)


class PromptInjectionFilter:
    """Security filter to detect and neutralize prompt injection attacks in code diffs and PR metadata."""

    # Compiled regex patterns for common prompt injection attack vectors
    INJECTION_PATTERNS: dict[str, re.Pattern[str]] = {
        "instruction_override": re.compile(
            r"(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|rules|prompts)",
            re.IGNORECASE,
        ),
        "system_role_hijack": re.compile(
            r"you\s+are\s+now\s+(an?\s+)?(admin|root|unrestricted|unfiltered|jailbroken|system)",
            re.IGNORECASE,
        ),
        "safety_bypass": re.compile(
            r"(bypass|disable|override)\s+(safety|security|review|scoring)\s+(gates|rules|checks)",
            re.IGNORECASE,
        ),
        "prompt_leak": re.compile(
            r"(output|print|reveal|show)\s+(your\s+)?(system\s+prompt|initial\s+instructions)",
            re.IGNORECASE,
        ),
        "jailbreak_keyword": re.compile(
            r"\[(DAN|JAILBREAK|DEVELOPER MODE|UNFILTERED)\]",
            re.IGNORECASE,
        ),
    }

    def scan(self, text: str) -> InjectionScanResult:
        """Scan input text for prompt injection attack signatures.

        Args:
            text: Raw input text (code diff, MR title, or description).

        Returns:
            InjectionScanResult indicating safety status, risk score, and matched patterns.
        """
        if not text or not text.strip():
            return InjectionScanResult(is_safe=True, risk_score=0.0, detected_patterns=[])

        detected: list[str] = []
        for rule_name, pattern in self.INJECTION_PATTERNS.items():
            if pattern.search(text):
                detected.append(rule_name)

        is_safe = len(detected) == 0
        risk_score = min(1.0, len(detected) * 0.4)

        if not is_safe:
            logger.warning(
                "prompt_injection_attempt_detected",
                detected_patterns=detected,
                risk_score=risk_score,
            )

        return InjectionScanResult(
            is_safe=is_safe,
            risk_score=risk_score,
            detected_patterns=detected,
        )

    def sanitize(self, text: str) -> str:
        """Sanitize text by neutralizing detected injection attempts while preserving code context.

        Args:
            text: Input text containing potential injection blocks.

        Returns:
            Sanitized text string.
        """
        sanitized = text
        for rule_name, pattern in self.INJECTION_PATTERNS.items():
            sanitized = pattern.sub(f"[REDACTED_PROMPT_INJECTION:{rule_name.upper()}]", sanitized)

        return sanitized


# Global Prompt Injection Filter Instance
prompt_injection_filter = PromptInjectionFilter()
