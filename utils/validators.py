"""
validators.py
--------------
Centralized input validation and sanitization utilities.

All methods are defensive by design: they never raise uncaught exceptions
for malformed input. They always return a predictable (bool, message) or
sanitized value so the calling code (app.py) never crashes on bad input.
"""

import re
import pandas as pd


class InputValidator:
    """Static utility methods for validating and sanitizing user input."""

    REQUIRED_CSV_COLUMNS = ["business_name", "business_type", "pain_point", "contact_name"]
    MAX_BATCH_SIZE = 100

    # ------------------------------------------------------------------
    # CSV validation
    # ------------------------------------------------------------------
    @staticmethod
    def validate_csv(df: pd.DataFrame):
        """
        Validate a leads DataFrame.

        Returns:
            (bool, str): (is_valid, error_message). error_message is empty
            when is_valid is True.
        """
        try:
            if df is None or df.empty:
                return False, "The uploaded CSV is empty. Please upload a file with at least one lead."

            # Normalize column names (strip whitespace, lowercase for comparison)
            normalized_cols = [str(c).strip().lower() for c in df.columns]
            missing_cols = [
                col for col in InputValidator.REQUIRED_CSV_COLUMNS
                if col not in normalized_cols
            ]
            if missing_cols:
                return False, (
                    f"CSV is missing required column(s): {', '.join(missing_cols)}. "
                    f"Required columns are: {', '.join(InputValidator.REQUIRED_CSV_COLUMNS)}"
                )

            if len(df) > InputValidator.MAX_BATCH_SIZE:
                return False, (
                    f"CSV contains {len(df)} rows, which exceeds the maximum batch size of "
                    f"{InputValidator.MAX_BATCH_SIZE}. Please split your file into smaller batches."
                )

            # Check for fully empty required cells
            df_check = df.copy()
            df_check.columns = normalized_cols
            for col in InputValidator.REQUIRED_CSV_COLUMNS:
                empty_count = df_check[col].isna().sum() + (df_check[col].astype(str).str.strip() == "").sum()
                if empty_count == len(df_check):
                    return False, f"Column '{col}' is completely empty. Please fill in values."

            return True, ""
        except Exception as e:
            return False, f"Unexpected error while validating CSV: {str(e)}"

    # ------------------------------------------------------------------
    # API key validation
    # ------------------------------------------------------------------
    @staticmethod
    def validate_api_key(key: str):
        """
        Validate the basic format of an OpenAI API key.

        Returns:
            (bool, str): (is_valid, message)
        """
        try:
            if not key or not isinstance(key, str):
                return False, "API key cannot be empty."

            key = key.strip()

            if not key.startswith("sk-"):
                return False, "Invalid API key format. OpenAI keys start with 'sk-'."

            if len(key) < 20:
                return False, "API key looks too short to be valid."

            # Only allow expected character set (letters, numbers, dashes, underscores)
            if not re.match(r"^sk-[A-Za-z0-9_\-]+$", key):
                return False, "API key contains unexpected characters."

            return True, "API key format looks valid."
        except Exception as e:
            return False, f"Error validating API key: {str(e)}"

    # ------------------------------------------------------------------
    # Text sanitization
    # ------------------------------------------------------------------
    @staticmethod
    def sanitize_text(text) -> str:
        """
        Remove potentially dangerous or unwanted characters from free text.
        Always returns a string, even if input is None or non-string.
        """
        try:
            if text is None:
                return ""
            text = str(text)

            # Strip control characters and other risky characters
            text = re.sub(r"[\x00-\x1f\x7f]", "", text)
            # Remove characters commonly used in injection/formula attacks
            text = re.sub(r"[<>{}$`]", "", text)
            # Prevent CSV formula injection (leading =, +, -, @)
            text = text.strip()
            if text and text[0] in ("=", "+", "-", "@"):
                text = "'" + text

            # Collapse excessive whitespace
            text = re.sub(r"\s+", " ", text).strip()

            return text
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # Field-level validation
    # ------------------------------------------------------------------
    @staticmethod
    def validate_business_type(text: str):
        """Validate business type: 2-100 chars."""
        try:
            text = InputValidator.sanitize_text(text)
            if len(text) < 2:
                return False, "Business type must be at least 2 characters."
            if len(text) > 100:
                return False, "Business type must be under 100 characters."
            return True, ""
        except Exception as e:
            return False, f"Error validating business type: {str(e)}"

    @staticmethod
    def validate_pain_point(text: str):
        """Validate pain point: 5-500 chars."""
        try:
            text = InputValidator.sanitize_text(text)
            if len(text) < 5:
                return False, "Pain point must be at least 5 characters."
            if len(text) > 500:
                return False, "Pain point must be under 500 characters."
            return True, ""
        except Exception as e:
            return False, f"Error validating pain point: {str(e)}"

    @staticmethod
    def validate_business_name(text: str):
        """Validate business name: 1-150 chars."""
        try:
            text = InputValidator.sanitize_text(text)
            if len(text) < 1:
                return False, "Business name is required."
            if len(text) > 150:
                return False, "Business name must be under 150 characters."
            return True, ""
        except Exception as e:
            return False, f"Error validating business name: {str(e)}"

    @staticmethod
    def validate_contact_name(text: str):
        """Validate contact name: 1-100 chars."""
        try:
            text = InputValidator.sanitize_text(text)
            if len(text) < 1:
                return False, "Contact name is required."
            if len(text) > 100:
                return False, "Contact name must be under 100 characters."
            return True, ""
        except Exception as e:
            return False, f"Error validating contact name: {str(e)}"
