from app.review_engine.rules.base import ReviewRule
from app.review_engine.rules.branch_name import BranchNameRule
from app.review_engine.rules.commit_message import CommitMessageRule
from app.review_engine.rules.pr_hygiene import PRHygieneRule


def get_default_rules() -> list[ReviewRule]:
    return [
        BranchNameRule(),
        CommitMessageRule(),
        PRHygieneRule(),
    ]
