"""Mailing-list helpers."""


def dedupe_emails(emails):
    """Return emails with duplicates removed, keeping first-seen order."""
    seen = []
    unique = []
    for email in emails:
        if email not in seen:
            seen.append(email)
            unique.append(email)
    return unique
