"""
message_generator.py
---------------------
Core message generation logic: both AI-powered (OpenAI) and free
template-based generation, with integrated cost tracking.
"""

from cost_tracker import CostTracker
from utils.templates import MESSAGE_TEMPLATES, DEFAULT_STYLE


class OutreachMessageGenerator:
    """
    Generates WhatsApp outreach messages either via the OpenAI API
    (gpt-3.5-turbo) or via free local templates.
    """

    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.api_key = api_key
        self.client = None
        self.cost_tracker = CostTracker(model=model)

        if api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
            except Exception as e:
                # Client creation failure shouldn't crash the app; AI calls
                # will simply fail gracefully and fall back to templates.
                self.client = None
                self._init_error = str(e)

    # ------------------------------------------------------------------
    def test_api_connection(self):
        """
        Test that the API key is valid and the OpenAI endpoint is reachable.

        Returns:
            (bool, str): (success, message)
        """
        try:
            if not self.client:
                return False, "OpenAI client is not initialized. Please provide a valid API key."

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Reply with just the word: OK"}],
                max_tokens=5,
            )
            if response and response.choices:
                return True, "✅ Connection successful! API key is valid."
            return False, "Connected, but received an unexpected empty response."
        except Exception as e:
            error_str = str(e).lower()
            if "authentication" in error_str or "api key" in error_str or "401" in error_str:
                return False, "❌ Authentication failed. Please check your API key."
            if "rate limit" in error_str or "429" in error_str:
                return False, "❌ Rate limit reached. Your key is valid but currently throttled."
            if "insufficient_quota" in error_str or "quota" in error_str:
                return False, "❌ Your API key has no remaining quota/credits."
            return False, f"❌ Connection failed: {str(e)}"

    # ------------------------------------------------------------------
    def _build_prompt(self, lead: dict, style: str) -> str:
        """Build the prompt sent to the OpenAI model."""
        style_descriptions = {
            "professional": "professional, polished, and respectful",
            "friendly": "warm, friendly, and approachable, with light emoji use",
            "direct": "short, direct, and to the point",
            "casual": "casual, relaxed, and conversational, like a text to a peer",
        }
        tone = style_descriptions.get(style, style_descriptions["professional"])

        prompt = (
            f"Write a short WhatsApp outreach message (under 60 words) to a business contact.\n"
            f"Tone: {tone}.\n"
            f"Contact name: {lead.get('contact_name', 'there')}\n"
            f"Business name: {lead.get('business_name', 'the business')}\n"
            f"Business type: {lead.get('business_type', 'the industry')}\n"
            f"Their likely pain point: {lead.get('pain_point', 'growth challenges')}\n\n"
            f"The message should introduce a light-touch value proposition and invite a short reply, "
            f"without being pushy or overly salesy. Do not include a subject line. "
            f"Output only the message text."
        )
        return prompt

    # ------------------------------------------------------------------
    def generate_ai_message(self, lead: dict, style: str = DEFAULT_STYLE):
        """
        Generate a message via the OpenAI API. Falls back to a template
        message if the API call fails for any reason.

        Returns:
            (str, dict): (message_text, cost_info)
        """
        prompt = self._build_prompt(lead, style)

        if not self.client:
            message = self._generate_template_message(lead, style)
            return message, {
                "input_tokens": 0, "output_tokens": 0,
                "total_tokens": 0, "cost_usd": 0.0,
                "fallback": True,
                "fallback_reason": "No API client available."
            }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful outreach copywriter."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                temperature=0.7,
            )
            message = response.choices[0].message.content.strip()

            cost_info = self.cost_tracker.log_usage(
                lead_name=lead.get("business_name", "unknown"),
                input_text=prompt,
                output_text=message,
            )
            cost_info["fallback"] = False
            return message, cost_info

        except Exception as e:
            # Any API failure (auth, rate limit, network, etc.) triggers a
            # graceful fallback to the free template so the app never crashes
            # and the user still gets a usable message.
            message = self._generate_template_message(lead, style)
            return message, {
                "input_tokens": 0, "output_tokens": 0,
                "total_tokens": 0, "cost_usd": 0.0,
                "fallback": True,
                "fallback_reason": str(e),
            }

    # ------------------------------------------------------------------
    def _generate_template_message(self, lead: dict, style: str = DEFAULT_STYLE) -> str:
        """Generate a free, local, template-based message."""
        try:
            template = MESSAGE_TEMPLATES.get(style, MESSAGE_TEMPLATES[DEFAULT_STYLE])
            return template.format(
                contact_name=lead.get("contact_name", "there") or "there",
                business_name=lead.get("business_name", "your business") or "your business",
                business_type=lead.get("business_type", "your industry") or "your industry",
                pain_point=lead.get("pain_point", "growing your business") or "growing your business",
            )
        except Exception:
            # Absolute last-resort fallback if even formatting fails
            name = lead.get("contact_name", "there") if isinstance(lead, dict) else "there"
            return f"Hi {name}, I'd love to connect and share how we could help your business grow!"

    # ------------------------------------------------------------------
    def generate_batch(self, leads: list, style: str = DEFAULT_STYLE, use_ai: bool = False,
                        progress_callback=None):
        """
        Generate messages for a list of leads.

        Args:
            leads: list of lead dicts (business_name, business_type, pain_point, contact_name)
            style: template style key
            use_ai: whether to use the OpenAI API (falls back to templates on failure)
            progress_callback: optional callable(current_index, total, lead) invoked after
                                each message is generated, useful for progress bars.

        Returns:
            list[dict]: each original lead dict, plus generated_message, tokens_used, cost_usd
        """
        results = []
        total = len(leads) if leads else 0

        for i, lead in enumerate(leads or []):
            try:
                if use_ai and self.client:
                    message, cost_info = self.generate_ai_message(lead, style)
                else:
                    message = self._generate_template_message(lead, style)
                    cost_info = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost_usd": 0.0}

                record = dict(lead)
                record["generated_message"] = message
                record["tokens_used"] = cost_info.get("total_tokens", 0)
                record["cost_usd"] = cost_info.get("cost_usd", 0.0)
                record["used_ai"] = bool(use_ai and self.client and not cost_info.get("fallback", False))
                results.append(record)

            except Exception as e:
                # Never let a single bad lead crash the whole batch
                record = dict(lead) if isinstance(lead, dict) else {}
                record["generated_message"] = f"[Error generating message: {str(e)}]"
                record["tokens_used"] = 0
                record["cost_usd"] = 0.0
                record["used_ai"] = False
                results.append(record)

            if progress_callback:
                try:
                    progress_callback(i + 1, total, lead)
                except Exception:
                    pass

        return results

    # ------------------------------------------------------------------
    def get_cost_summary(self) -> dict:
        """Delegate to CostTracker for the current session summary."""
        return self.cost_tracker.get_session_summary()

    def get_monthly_estimate(self, daily_leads: int, working_days: int = 22) -> dict:
        """Delegate to CostTracker for a projected monthly cost estimate."""
        return self.cost_tracker.get_monthly_estimate(daily_leads, working_days)
