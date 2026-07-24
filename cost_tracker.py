"""
cost_tracker.py
----------------
Tracks token usage and cost for OpenAI API calls, and logs usage history
to a CSV file for later analysis (Analytics tab).
"""

import os
import csv
import datetime

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except Exception:
    TIKTOKEN_AVAILABLE = False


class CostTracker:
    """
    Tracks token usage and USD cost for gpt-3.5-turbo calls.

    Pricing (USD per 1K tokens) as of general OpenAI gpt-3.5-turbo pricing.
    NOTE: Prices can change — verify against https://openai.com/pricing
    before relying on this for financial reporting.
    """

    PRICING = {
        "gpt-3.5-turbo": {
            "input": 0.0015,   # per 1K input tokens
            "output": 0.002,   # per 1K output tokens
        }
    }

    def __init__(self, model: str = "gpt-3.5-turbo", log_dir: str = "logs"):
        self.model = model
        self.log_dir = log_dir
        self.log_file = os.path.join(self.log_dir, "usage_log.csv")

        # In-memory session totals
        self.session_history = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

        self._ensure_log_file()

    # ------------------------------------------------------------------
    def _ensure_log_file(self):
        """Create the log directory/file with headers if they don't exist."""
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            if not os.path.exists(self.log_file):
                with open(self.log_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "timestamp", "lead_name", "model",
                        "input_tokens", "output_tokens", "total_tokens", "cost_usd"
                    ])
        except Exception:
            # If we can't create logs (e.g. read-only filesystem), fail silently.
            # Session-level tracking will still work in memory.
            pass

    # ------------------------------------------------------------------
    def count_tokens(self, text: str) -> int:
        """Count tokens in a string using tiktoken, with a safe fallback."""
        try:
            if not text:
                return 0
            if TIKTOKEN_AVAILABLE:
                try:
                    encoding = tiktoken.encoding_for_model(self.model)
                except Exception:
                    encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            else:
                # Rough fallback estimate: ~4 characters per token
                return max(1, len(text) // 4)
        except Exception:
            return max(1, len(str(text)) // 4)

    # ------------------------------------------------------------------
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate USD cost for given input/output token counts."""
        try:
            pricing = self.PRICING.get(self.model, self.PRICING["gpt-3.5-turbo"])
            input_cost = (input_tokens / 1000) * pricing["input"]
            output_cost = (output_tokens / 1000) * pricing["output"]
            return round(input_cost + output_cost, 6)
        except Exception:
            return 0.0

    # ------------------------------------------------------------------
    def log_usage(self, lead_name: str, input_text: str, output_text: str):
        """
        Count tokens for input/output text, calculate cost, log it to the
        session history and the CSV log file.

        Returns:
            dict: cost info for this single call
                  {input_tokens, output_tokens, total_tokens, cost_usd}
        """
        try:
            input_tokens = self.count_tokens(input_text)
            output_tokens = self.count_tokens(output_text)
            cost = self.calculate_cost(input_tokens, output_tokens)
            total_tokens = input_tokens + output_tokens
            timestamp = datetime.datetime.now().isoformat(timespec="seconds")

            record = {
                "timestamp": timestamp,
                "lead_name": lead_name or "unknown",
                "model": self.model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost,
            }

            # Update in-memory session state
            self.session_history.append(record)
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_cost += cost

            # Append to CSV log file (best-effort; never raise)
            try:
                with open(self.log_file, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp, record["lead_name"], self.model,
                        input_tokens, output_tokens, total_tokens, cost
                    ])
            except Exception:
                pass

            return record
        except Exception:
            return {
                "input_tokens": 0, "output_tokens": 0,
                "total_tokens": 0, "cost_usd": 0.0
            }

    # ------------------------------------------------------------------
    def get_session_summary(self) -> dict:
        """Return a summary of the current session's usage."""
        try:
            total_requests = len(self.session_history)
            avg_cost = (self.total_cost / total_requests) if total_requests else 0.0
            return {
                "total_requests": total_requests,
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_tokens": self.total_input_tokens + self.total_output_tokens,
                "total_cost_usd": round(self.total_cost, 6),
                "avg_cost_per_message": round(avg_cost, 6),
            }
        except Exception:
            return {
                "total_requests": 0, "total_input_tokens": 0,
                "total_output_tokens": 0, "total_tokens": 0,
                "total_cost_usd": 0.0, "avg_cost_per_message": 0.0
            }

    # ------------------------------------------------------------------
    def get_monthly_estimate(self, daily_leads: int, working_days: int = 22) -> dict:
        """
        Estimate monthly cost based on average tokens/cost per lead observed
        in the current session. If no session data exists, uses a reasonable
        default estimate (~350 total tokens per message).

        Returns:
            dict: {avg_cost_per_message, daily_cost, monthly_cost, monthly_tokens}
        """
        try:
            summary = self.get_session_summary()
            if summary["total_requests"] > 0:
                avg_cost = summary["avg_cost_per_message"]
                avg_tokens = summary["total_tokens"] / summary["total_requests"]
            else:
                # Reasonable default: ~200 input + ~150 output tokens per message
                avg_tokens = 350
                avg_cost = self.calculate_cost(200, 150)

            daily_cost = avg_cost * daily_leads
            monthly_cost = daily_cost * working_days
            monthly_tokens = avg_tokens * daily_leads * working_days

            return {
                "avg_cost_per_message": round(avg_cost, 6),
                "daily_cost": round(daily_cost, 4),
                "monthly_cost": round(monthly_cost, 2),
                "monthly_tokens": int(monthly_tokens),
            }
        except Exception:
            return {
                "avg_cost_per_message": 0.0, "daily_cost": 0.0,
                "monthly_cost": 0.0, "monthly_tokens": 0
            }

    # ------------------------------------------------------------------
    def get_usage_history(self):
        """
        Read the full usage history from the CSV log file.

        Returns:
            list[dict]: rows from the log file, or an empty list on error.
        """
        try:
            if not os.path.exists(self.log_file):
                return []
            history = []
            with open(self.log_file, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    history.append(row)
            return history
        except Exception:
            return []

    # ------------------------------------------------------------------
    def reset_session(self):
        """Clear in-memory session totals (does not touch the log file)."""
        self.session_history = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
