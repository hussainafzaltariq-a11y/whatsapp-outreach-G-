"""
templates.py
------------
Free, no-API-key-required message templates used by "Template Based" mode.

Each template is a Python format string using these placeholders:
    {contact_name}, {business_name}, {business_type}, {pain_point}
"""

MESSAGE_TEMPLATES = {
    "professional": (
        "Hi {contact_name}, 👋\n\n"
        "I came across {business_name} and noticed you're doing great work in the "
        "{business_type} space. I understand that {pain_point} can be a real challenge "
        "for businesses like yours.\n\n"
        "I'd love to share how we've helped similar businesses solve this exact problem. "
        "Would you be open to a quick 15-minute chat this week?\n\n"
        "Looking forward to connecting.\n"
        "Best regards"
    ),
    "friendly": (
        "Hey {contact_name}! 😊\n\n"
        "Hope you're having a great day! I've been following {business_name} and love what "
        "you're doing in {business_type}. I know dealing with {pain_point} isn't easy, "
        "and I think I might have something that could really help.\n\n"
        "Mind if I send over a quick idea? No pressure at all, just thought it might be "
        "useful for you! 🙌"
    ),
    "direct": (
        "Hi {contact_name},\n\n"
        "Quick question — is {pain_point} still an issue for {business_name}?\n\n"
        "We work with {business_type} businesses to solve exactly this. If you're interested, "
        "reply here and I'll send over the details.\n\n"
        "Talk soon."
    ),
    "casual": (
        "Yo {contact_name}! 👋\n\n"
        "Saw {business_name} and thought it was pretty cool what you're doing in "
        "{business_type}. Just curious — is {pain_point} something you're still dealing with? "
        "Got a simple fix that might help if you're up for a chat 😄"
    ),
}

DEFAULT_STYLE = "professional"


def get_available_styles():
    """Return the list of available template style names."""
    return list(MESSAGE_TEMPLATES.keys())
