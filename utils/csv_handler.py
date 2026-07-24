"""
csv_handler.py
--------------
Handles reading, validating, and exporting lead CSV files.
"""

import io
import pandas as pd

from utils.validators import InputValidator


class CSVHandler:
    """Utility class for all CSV-related operations on lead data."""

    REQUIRED_COLUMNS = ["business_name", "business_type", "pain_point", "contact_name"]
    MAX_BATCH_SIZE = 100

    # ------------------------------------------------------------------
    @staticmethod
    def validate_csv_structure(file):
        """
        Validate the structure of an uploaded file object (e.g. Streamlit
        UploadedFile) without fully processing it.

        Returns:
            (bool, str): (is_valid, error_message)
        """
        try:
            if file is None:
                return False, "No file was uploaded."

            try:
                file.seek(0)
                df = pd.read_csv(file)
                file.seek(0)
            except pd.errors.EmptyDataError:
                return False, "The uploaded CSV file is empty."
            except pd.errors.ParserError:
                return False, "Could not parse the CSV file. Please check the formatting."
            except Exception as e:
                return False, f"Could not read the CSV file: {str(e)}"

            is_valid, message = InputValidator.validate_csv(df)
            return is_valid, message
        except Exception as e:
            return False, f"Unexpected error validating file: {str(e)}"

    # ------------------------------------------------------------------
    @staticmethod
    def read_leads(file_path):
        """
        Read leads from a CSV file (path or file-like object) and return a
        cleaned list of lead dictionaries.

        Returns:
            (list[dict], str): (leads, error_message). leads is an empty
            list when an error occurs.
        """
        try:
            if hasattr(file_path, "seek"):
                file_path.seek(0)

            try:
                df = pd.read_csv(file_path)
            except pd.errors.EmptyDataError:
                return [], "The uploaded CSV file is empty."
            except pd.errors.ParserError:
                return [], "Could not parse the CSV file. Please check the formatting."
            except Exception as e:
                return [], f"Could not read the CSV file: {str(e)}"

            # Normalize column names
            df.columns = [str(c).strip().lower() for c in df.columns]

            is_valid, message = InputValidator.validate_csv(df)
            if not is_valid:
                return [], message

            # Limit to MAX_BATCH_SIZE rows
            if len(df) > CSVHandler.MAX_BATCH_SIZE:
                df = df.head(CSVHandler.MAX_BATCH_SIZE)

            leads = []
            skipped = 0
            for _, row in df.iterrows():
                try:
                    business_name = InputValidator.sanitize_text(row.get("business_name", ""))
                    business_type = InputValidator.sanitize_text(row.get("business_type", ""))
                    pain_point = InputValidator.sanitize_text(row.get("pain_point", ""))
                    contact_name = InputValidator.sanitize_text(row.get("contact_name", ""))

                    if not business_name or not contact_name:
                        skipped += 1
                        continue

                    leads.append({
                        "business_name": business_name or "Your Business",
                        "business_type": business_type or "your industry",
                        "pain_point": pain_point or "growing your customer base",
                        "contact_name": contact_name or "there",
                    })
                except Exception:
                    skipped += 1
                    continue

            if not leads:
                return [], "No valid leads found in the CSV after cleaning. Please check your data."

            note = f" ({skipped} row(s) skipped due to missing data)" if skipped else ""
            return leads, note  # note is informational, not necessarily an error
        except Exception as e:
            return [], f"Unexpected error reading leads: {str(e)}"

    # ------------------------------------------------------------------
    @staticmethod
    def export_messages(messages, output_path=None):
        """
        Export a list of message dicts to CSV.

        Args:
            messages: list of dicts (each representing a generated message record)
            output_path: optional file path to save to. If None, returns CSV bytes.

        Returns:
            bytes (CSV content) if output_path is None, else the output_path string.
        """
        try:
            df = pd.DataFrame(messages)
            if output_path:
                df.to_csv(output_path, index=False)
                return output_path
            else:
                buffer = io.StringIO()
                df.to_csv(buffer, index=False)
                return buffer.getvalue().encode("utf-8")
        except Exception as e:
            raise RuntimeError(f"Failed to export messages: {str(e)}")

    # ------------------------------------------------------------------
    @staticmethod
    def create_sample_csv() -> pd.DataFrame:
        """Return a small sample leads DataFrame that matches the required format."""
        sample_data = {
            "business_name": [
                "Golden Spoon Cafe", "Bright Smile Dental", "Urban Fit Gym",
                "Sunrise Realty", "TechNest Solutions",
            ],
            "business_type": [
                "restaurant", "dental clinic", "fitness studio",
                "real estate agency", "IT consulting",
            ],
            "pain_point": [
                "low online reservation numbers",
                "too many missed appointment reminders",
                "difficulty retaining new members",
                "slow response time to buyer inquiries",
                "lack of qualified inbound leads",
            ],
            "contact_name": [
                "Maria", "Dr. Ahmed", "Jake", "Linda", "Farhan",
            ],
        }
        return pd.DataFrame(sample_data)
