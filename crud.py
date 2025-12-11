from .models import User, Rule, Command
from .utils import is_valid_regex
import re
from sqlmodel import Session, select
def get_user_by_api_key(session, api_key: str):
    return session.exec(select(User).where(User.api_key == api_key)).first()

def create_rule(session, pattern: str, action: str, description: str = None):
    if not is_valid_regex(pattern):
        raise ValueError("Invalid regex pattern")
    rule = Rule(pattern=pattern, action=action, description=description)
    session.add(rule)
    session.commit()
    return rule

def match_command_against_rules(session, command_text: str):
    rules = session.exec(select(Rule)).all()
    for rule in rules:
        if re.search(rule.pattern, command_text):
            return rule.action
    return "AUTO_REJECT"  # default deny