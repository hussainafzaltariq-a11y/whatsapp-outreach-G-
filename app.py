"""
app.py
------
WhatsApp Outreach Message Generator — main Streamlit application.

This app is designed to be used by non-technical users. Every user-facing
action is wrapped in try/except so a bad CSV, bad API key, or network
hiccup never crashes the whole app.
"""

import io
import datetime

import pandas as pd
import streamlit as st

from message_generator import OutreachMessageGenerator
from utils.csv_handler import CSVHandler
from utils.validators import InputValidator
from utils.templates import get_available_styles

# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="WhatsApp Outreach Generator",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# SESSION STATE INIT
# ----------------------------------------------------------------------
def init_session_state():
    defaults = {
        "generator": None,
        "api_key_valid": False,
        "api_connected": False,
        "batch_leads": [],
        "batch_results": [],
        "single_result": None,
        "session_cost": 0.0,
        "session_tokens": 0,
        "session_requests": 0,
        "csv_error": "",
        "csv_note": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()

# ----------------------------------------------------------------------
# CUSTOM CSS — WhatsApp-like green theme
# ----------------------------------------------------------------------
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #075E54 0%, #128C7E 50%, #25D366 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.2rem;
    }
    .main-header p {
        margin-top: 0.4rem;
        opacity: 0.9;
    }
    .message-card {
    background-color: #DCF8C6;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    border-left: 5px solid #25D366;
    color: #000000 !important;  /* Force black text */
}

.message-card p, .message-card div, .message-card span {
    color: #000000 !important;  /* Ensure all text inside is black */
}
    }
    .cost-box {
        background-color: #E8F5E9;
        border-radius: 8px;
        padding: 0.8rem;
        border: 1px solid #25D366;
        margin-bottom: 0.6rem;
    }
    div.stButton > button {
        background-color: #25D366;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    div.stButton > button:hover {
        background-color: #128C7E;
        color: white;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>💬 WhatsApp Outreach Message Generator</h1>
    <p>Create personalized outreach messages in seconds — free templates or AI-powered</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    generation_mode = st.radio(
        "Generation Mode",
        options=["Template Based (Free)", "AI Powered (OpenAI)"],
        index=0,
        help="Template mode is free and instant. AI mode uses your OpenAI API key and incurs a small cost per message.",
    )
    use_ai = generation_mode == "AI Powered (OpenAI)"

    api_key = None
    if use_ai:
        st.markdown("---")
        st.subheader("🔑 OpenAI API Key")
        api_key_input = st.text_input(
            "Enter your API key",
            type="password",
            placeholder="sk-...",
            help="Your key is only used in this session and is never stored permanently.",
        )

        if api_key_input:
            is_valid, msg = InputValidator.validate_api_key(api_key_input)
            st.session_state.api_key_valid = is_valid
            if is_valid:
                api_key = api_key_input.strip()
                st.success("✅ Key format looks valid")
            else:
                st.error(f"❌ {msg}")

        if st.button("🔌 Test Connection", disabled=not st.session_state.api_key_valid):
            try:
                with st.spinner("Testing connection..."):
                    test_gen = OutreachMessageGenerator(api_key=api_key)
                    success, message = test_gen.test_api_connection()
                if success:
                    st.session_state.generator = test_gen
                    st.session_state.api_connected = True
                    st.success(message)
                else:
                    st.session_state.api_connected = False
                    st.error(message)
            except Exception as e:
                st.session_state.api_connected = False
                st.error(f"Unexpected error testing connection: {str(e)}")

        if st.session_state.api_connected:
            st.info("🟢 Connected — AI generation is active")
        else:
            st.warning("🟡 Not connected — will fall back to templates until connected")

    st.markdown("---")
    st.subheader("🎨 Message Style")
    message_style = st.selectbox(
        "Choose a tone",
        options=get_available_styles(),
        index=0,
        format_func=lambda s: s.capitalize(),
    )

    # Ensure we always have a generator object available (template-mode fallback)
    if st.session_state.generator is None or (use_ai and not st.session_state.api_connected and api_key):
        try:
            st.session_state.generator = OutreachMessageGenerator(api_key=api_key if use_ai else None)
        except Exception as e:
            st.error(f"Could not initialize generator: {str(e)}")
            st.session_state.generator = OutreachMessageGenerator(api_key=None)

    generator = st.session_state.generator

    # Live cost display
    if use_ai and st.session_state.api_connected and generator:
        st.markdown("---")
        st.subheader("💰 Session Cost")
        try:
            summary = generator.get_cost_summary()
            col1, col2 = st.columns(2)
            col1.metric("Total Cost", f"${summary['total_cost_usd']:.4f}")
            col2.metric("Total Tokens", f"{summary['total_tokens']:,}")
            st.caption(f"{summary['total_requests']} message(s) generated this session")
        except Exception as e:
            st.caption(f"Cost data unavailable: {str(e)}")

    st.markdown("---")
    if st.button("🔄 Reset Session"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ----------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📁 Batch Processing", "✏️ Single Lead", "📊 Analytics"])

# ========================================================================
# TAB 1 — BATCH PROCESSING
# ========================================================================
with tab1:
    st.subheader("📁 Batch Message Generation")
    st.write("Upload a CSV of leads to generate personalized messages for up to 100 contacts at once.")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        uploaded_file = st.file_uploader("Upload leads CSV", type=["csv"], key="batch_uploader")
    with col_b:
        st.write("**Required columns:**")
        st.code("business_name\nbusiness_type\npain_point\ncontact_name", language="text")
        try:
            sample_df = CSVHandler.create_sample_csv()
            sample_csv_bytes = sample_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download sample CSV",
                data=sample_csv_bytes,
                file_name="sample_leads.csv",
                mime="text/csv",
            )
        except Exception as e:
            st.caption(f"Could not generate sample CSV: {str(e)}")

    if uploaded_file is not None:
        try:
            leads, note_or_error = CSVHandler.read_leads(uploaded_file)
            if not leads:
                st.error(f"❌ {note_or_error}")
                st.session_state.batch_leads = []
            else:
                st.session_state.batch_leads = leads
                st.success(f"✅ Loaded {len(leads)} valid lead(s).{note_or_error}")

                with st.expander("👀 Preview leads", expanded=True):
                    st.dataframe(pd.DataFrame(leads), use_container_width=True)
        except Exception as e:
            st.error(f"❌ Unexpected error processing file: {str(e)}")
            st.session_state.batch_leads = []

    if st.session_state.batch_leads:
        st.markdown("---")
        generate_batch_clicked = st.button(
            f"🚀 Generate Messages for {len(st.session_state.batch_leads)} Lead(s)",
            key="generate_batch_btn",
        )

        if generate_batch_clicked:
            try:
                progress_bar = st.progress(0, text="Starting generation...")

                def update_progress(current, total, lead):
                    pct = int((current / total) * 100) if total else 100
                    name = lead.get("business_name", "lead") if isinstance(lead, dict) else "lead"
                    progress_bar.progress(pct, text=f"Generating message {current}/{total} — {name}")

                results = generator.generate_batch(
                    leads=st.session_state.batch_leads,
                    style=message_style,
                    use_ai=use_ai and st.session_state.api_connected,
                    progress_callback=update_progress,
                )
                progress_bar.progress(100, text="Done!")
                st.session_state.batch_results = results
                st.success(f"✅ Generated {len(results)} message(s)!")
            except Exception as e:
                st.error(f"❌ Error during batch generation: {str(e)}")

    # ------------------------------------------------------------------
    # Show batch results
    # ------------------------------------------------------------------
    if st.session_state.batch_results:
        st.markdown("---")
        st.subheader(f"📨 Generated Messages ({len(st.session_state.batch_results)})")

        results_df = pd.DataFrame(st.session_state.batch_results)

        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            business_types = ["All"] + sorted(results_df["business_type"].dropna().unique().tolist()) \
                if "business_type" in results_df.columns else ["All"]
            selected_type = st.selectbox("Filter by business type", options=business_types)
        with filter_col2:
            search_term = st.text_input("🔍 Search by business or contact name")

        filtered = st.session_state.batch_results
        try:
            if selected_type != "All":
                filtered = [r for r in filtered if r.get("business_type") == selected_type]
            if search_term:
                term = search_term.lower().strip()
                filtered = [
                    r for r in filtered
                    if term in str(r.get("business_name", "")).lower()
                    or term in str(r.get("contact_name", "")).lower()
                ]
        except Exception as e:
            st.warning(f"Filter error: {str(e)}")

        for idx, record in enumerate(filtered):
            try:
                header = f"{record.get('business_name', 'Unknown')} — {record.get('contact_name', '')}"
                with st.expander(header):
                    st.markdown(f"**Business Type:** {record.get('business_type', '-')}")
                    st.markdown(f"**Pain Point:** {record.get('pain_point', '-')}")
                    st.markdown(f"""<div class="message-card">{record.get('generated_message', '')}</div>""",
                                unsafe_allow_html=True)

                    meta_col1, meta_col2, meta_col3 = st.columns(3)
                    meta_col1.caption(f"Tokens: {record.get('tokens_used', 0)}")
                    meta_col2.caption(f"Cost: ${record.get('cost_usd', 0.0):.5f}")
                    meta_col3.caption("Source: AI" if record.get("used_ai") else "Source: Template")

                    st.download_button(
                        "⬇️ Download this message (.txt)",
                        data=record.get("generated_message", "").encode("utf-8"),
                        file_name=f"{record.get('business_name', 'message').replace(' ', '_')}.txt",
                        mime="text/plain",
                        key=f"dl_single_{idx}",
                    )
            except Exception as e:
                st.warning(f"Could not display record {idx}: {str(e)}")

        st.markdown("---")
        st.subheader("📤 Export All")
        export_col1, export_col2 = st.columns(2)
        try:
            csv_bytes = CSVHandler.export_messages(st.session_state.batch_results)
            with export_col1:
                st.download_button(
                    "⬇️ Export all as CSV",
                    data=csv_bytes,
                    file_name=f"outreach_messages_{datetime.date.today().isoformat()}.csv",
                    mime="text/csv",
                )
        except Exception as e:
            st.warning(f"Could not prepare CSV export: {str(e)}")

        try:
            txt_content = "\n\n---\n\n".join(
                f"To: {r.get('contact_name', '')} ({r.get('business_name', '')})\n{r.get('generated_message', '')}"
                for r in st.session_state.batch_results
            )
            with export_col2:
                st.download_button(
                    "⬇️ Export all as TXT",
                    data=txt_content.encode("utf-8"),
                    file_name=f"outreach_messages_{datetime.date.today().isoformat()}.txt",
                    mime="text/plain",
                )
        except Exception as e:
            st.warning(f"Could not prepare TXT export: {str(e)}")

# ========================================================================
# TAB 2 — SINGLE LEAD
# ========================================================================
with tab2:
    st.subheader("✏️ Single Lead Message Generator")
    st.write("Manually enter a lead's details to generate one personalized message.")

    with st.form("single_lead_form"):
        col1, col2 = st.columns(2)
        with col1:
            s_business_name = st.text_input("Business Name *", placeholder="e.g. Golden Spoon Cafe")
            s_business_type = st.text_input("Business Type *", placeholder="e.g. restaurant")
        with col2:
            s_contact_name = st.text_input("Contact Name *", placeholder="e.g. Maria")
            s_pain_point = st.text_area("Pain Point *", placeholder="e.g. low online reservation numbers", height=100)

        submitted = st.form_submit_button("✨ Generate Single Message")

    if submitted:
        errors = []
        try:
            valid, msg = InputValidator.validate_business_name(s_business_name)
            if not valid:
                errors.append(msg)

            valid, msg = InputValidator.validate_business_type(s_business_type)
            if not valid:
                errors.append(msg)

            valid, msg = InputValidator.validate_contact_name(s_contact_name)
            if not valid:
                errors.append(msg)

            valid, msg = InputValidator.validate_pain_point(s_pain_point)
            if not valid:
                errors.append(msg)

            if errors:
                for e in errors:
                    st.error(f"❌ {e}")
            else:
                lead = {
                    "business_name": InputValidator.sanitize_text(s_business_name),
                    "business_type": InputValidator.sanitize_text(s_business_type),
                    "pain_point": InputValidator.sanitize_text(s_pain_point),
                    "contact_name": InputValidator.sanitize_text(s_contact_name),
                }

                with st.spinner("Generating message..."):
                    if use_ai and st.session_state.api_connected:
                        message, cost_info = generator.generate_ai_message(lead, message_style)
                        used_ai = not cost_info.get("fallback", False)
                    else:
                        message = generator._generate_template_message(lead, message_style)
                        cost_info = {"tokens_used": 0, "cost_usd": 0.0}
                        used_ai = False

                st.session_state.single_result = {
                    **lead,
                    "generated_message": message,
                    "tokens_used": cost_info.get("total_tokens", cost_info.get("tokens_used", 0)),
                    "cost_usd": cost_info.get("cost_usd", 0.0),
                    "used_ai": used_ai,
                }
        except Exception as e:
            st.error(f"❌ Unexpected error generating message: {str(e)}")

    if st.session_state.single_result:
        result = st.session_state.single_result
        st.markdown("---")
        st.subheader("📨 Generated Message")

        st.markdown(f"**To:** {result.get('contact_name', '')} — {result.get('business_name', '')}")
        st.markdown(f"""<div class="message-card">{result.get('generated_message', '')}</div>""",
                    unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.caption(f"Tokens: {result.get('tokens_used', 0)}")
        m2.caption(f"Cost: ${result.get('cost_usd', 0.0):.5f}")
        m3.caption("Source: AI" if result.get("used_ai") else "Source: Template")

        st.download_button(
            "⬇️ Download message (.txt)",
            data=result.get("generated_message", "").encode("utf-8"),
            file_name=f"{result.get('business_name', 'message').replace(' ', '_')}.txt",
            mime="text/plain",
        )

# ========================================================================
# TAB 3 — ANALYTICS
# ========================================================================
with tab3:
    st.subheader("📊 Analytics & Cost Estimation")

    try:
        summary = generator.get_cost_summary() if generator else {
            "total_requests": 0, "total_tokens": 0, "total_cost_usd": 0.0, "avg_cost_per_message": 0.0
        }
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Requests", summary.get("total_requests", 0))
        c2.metric("Total Tokens", f"{summary.get('total_tokens', 0):,}")
        c3.metric("Total Cost", f"${summary.get('total_cost_usd', 0.0):.4f}")
        c4.metric("Avg Cost / Message", f"${summary.get('avg_cost_per_message', 0.0):.5f}")
    except Exception as e:
        st.warning(f"Could not load session summary: {str(e)}")

    st.markdown("---")
    st.subheader("📅 Monthly Cost Estimator")
    st.write("Estimate your projected monthly OpenAI cost based on expected daily lead volume.")

    est_col1, est_col2 = st.columns(2)
    with est_col1:
        daily_leads = st.number_input("Leads per day", min_value=1, max_value=1000, value=50, step=1)
    with est_col2:
        working_days = st.number_input("Working days per month", min_value=1, max_value=31, value=22, step=1)

    try:
        estimate = generator.get_monthly_estimate(daily_leads, working_days) if generator else None
        if estimate:
            e1, e2, e3 = st.columns(3)
            e1.metric("Avg Cost / Message", f"${estimate['avg_cost_per_message']:.5f}")
            e2.metric("Estimated Daily Cost", f"${estimate['daily_cost']:.2f}")
            e3.metric("Estimated Monthly Cost", f"${estimate['monthly_cost']:.2f}")
            st.caption(
                f"Based on ~{estimate['monthly_tokens']:,} tokens/month. "
                "Estimate uses session averages when available, otherwise a typical default."
            )
    except Exception as e:
        st.warning(f"Could not calculate estimate: {str(e)}")

    st.markdown("---")
    st.subheader("🧾 Usage History")
    try:
        history = generator.cost_tracker.get_usage_history() if generator else []
        if history:
            hist_df = pd.DataFrame(history)
            st.dataframe(hist_df, use_container_width=True)
            st.download_button(
                "⬇️ Download usage log (.csv)",
                data=hist_df.to_csv(index=False).encode("utf-8"),
                file_name="usage_log.csv",
                mime="text/csv",
            )
        else:
            st.info("No usage history yet. Generate some AI-powered messages to see logs here.")
    except Exception as e:
        st.warning(f"Could not load usage history: {str(e)}")

# ----------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------
st.markdown("---")
st.caption("Built with ❤️ using Streamlit · Template mode is always free · AI mode requires your own OpenAI API key")
