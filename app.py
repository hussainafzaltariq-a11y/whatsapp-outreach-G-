"""
app.py - Gradio Version with ZeroGPU Support
WhatsApp Outreach Message Generator
"""

import os
import datetime
import pandas as pd
import gradio as gr

try:
    from spaces import GPU
except ImportError:
    # Define a dummy decorator if spaces is not available
    def GPU(func):
        return func

from message_generator import OutreachMessageGenerator
from utils.csv_handler import CSVHandler
from utils.validators import InputValidator
from utils.templates import get_available_styles

# Global generator instance
generator = None
api_key = os.getenv("OPENAI_API_KEY", None)

# Initialize generator
if api_key:
    try:
        generator = OutreachMessageGenerator(api_key=api_key)
    except Exception:
        generator = OutreachMessageGenerator(api_key=None)
else:
    generator = OutreachMessageGenerator(api_key=None)


@GPU
def generate_single_message_gpu(business_name, business_type, contact_name, pain_point, use_ai, style):
    """Generate a single message with GPU acceleration"""
    try:
        # Validate inputs
        valid, msg = InputValidator.validate_business_name(business_name)
        if not valid:
            return f"❌ {msg}", "", 0, 0.0
        
        valid, msg = InputValidator.validate_business_type(business_type)
        if not valid:
            return f"❌ {msg}", "", 0, 0.0
        
        valid, msg = InputValidator.validate_contact_name(contact_name)
        if not valid:
            return f"❌ {msg}", "", 0, 0.0
        
        valid, msg = InputValidator.validate_pain_point(pain_point)
        if not valid:
            return f"❌ {msg}", "", 0, 0.0
        
        # Sanitize
        lead = {
            "business_name": InputValidator.sanitize_text(business_name),
            "business_type": InputValidator.sanitize_text(business_type),
            "contact_name": InputValidator.sanitize_text(contact_name),
            "pain_point": InputValidator.sanitize_text(pain_point),
        }
        
        # Generate
        if use_ai and generator and generator.client:
            message, cost_info = generator.generate_ai_message(lead, style)
            used_ai = not cost_info.get("fallback", False)
        else:
            message = generator._generate_template_message(lead, style) if generator else "Generator not initialized"
            cost_info = {"total_tokens": 0, "cost_usd": 0.0}
            used_ai = False
        
        tokens = cost_info.get("total_tokens", 0)
        cost = cost_info.get("cost_usd", 0.0)
        source = "AI" if used_ai else "Template"
        
        return f"✅ Message generated!", message, tokens, cost, source
    
    except Exception as e:
        return f"❌ Error: {str(e)}", "", 0, 0.0, ""


@GPU
def generate_batch_messages_gpu(file, use_ai, style):
    """Generate messages for batch upload with GPU acceleration"""
    try:
        if file is None:
            return "❌ Please upload a CSV file.", None
        
        leads, note = CSVHandler.read_leads(file)
        if not leads:
            return f"❌ {note}", None
        
        if len(leads) > 100:
            return f"❌ Too many leads. Maximum 100 allowed. You have {len(leads)}.", None
        
        results = generator.generate_batch(
            leads=leads,
            style=style,
            use_ai=use_ai and generator and generator.client
        )
        
        # Create summary
        df = pd.DataFrame(results)
        summary = f"✅ Generated {len(results)} messages!"
        
        if len(results) > 0:
            return summary, df
        else:
            return "❌ No messages generated.", None
    
    except Exception as e:
        return f"❌ Error: {str(e)}", None


def get_analytics():
    """Get analytics data"""
    try:
        if not generator:
            return "Generator not initialized", None
        
        summary = generator.get_cost_summary()
        
        # Format summary
        lines = [
            f"📊 **Session Analytics**",
            f"",
            f"**Total Requests:** {summary.get('total_requests', 0)}",
            f"**Total Tokens:** {summary.get('total_tokens', 0):,}",
            f"**Total Cost:** ${summary.get('total_cost_usd', 0.0):.4f}",
            f"**Avg Cost/Message:** ${summary.get('avg_cost_per_message', 0.0):.5f}",
            f"",
            f"---",
            f"",
            f"📅 **Monthly Estimate**",
            f"",
            f"Enter daily leads and working days in the form below."
        ]
        
        return "\n".join(lines), summary
    
    except Exception as e:
        return f"❌ Error: {str(e)}", None


def calculate_estimate(daily_leads, working_days):
    """Calculate monthly cost estimate"""
    try:
        if not generator:
            return "Generator not initialized"
        
        estimate = generator.get_monthly_estimate(daily_leads, working_days)
        
        if estimate:
            return f"""
📅 **Monthly Cost Estimate**

**Average Cost/Message:** ${estimate.get('avg_cost_per_message', 0.0):.5f}
**Daily Cost:** ${estimate.get('daily_cost', 0.0):.2f}
**Monthly Cost:** ${estimate.get('monthly_cost', 0.0):.2f}
**Monthly Tokens:** {estimate.get('monthly_tokens', 0):,}

*Based on {daily_leads} leads/day for {working_days} working days*
"""
        else:
            return "Could not calculate estimate"
    
    except Exception as e:
        return f"❌ Error: {str(e)}"


def get_usage_history():
    """Get usage history"""
    try:
        if not generator:
            return "Generator not initialized", None
        
        history = generator.cost_tracker.get_usage_history()
        
        if history:
            df = pd.DataFrame(history)
            return f"📋 **Usage History** ({len(history)} records)", df
        else:
            return "No usage history yet. Generate some AI-powered messages to see logs here.", None
    
    except Exception as e:
        return f"❌ Error: {str(e)}", None


def test_connection(api_key_input):
    """Test OpenAI API connection"""
    try:
        if not api_key_input:
            return "❌ Please enter an API key", False
        
        test_gen = OutreachMessageGenerator(api_key=api_key_input)
        success, message = test_gen.test_api_connection()
        
        if success:
            global generator
            generator = test_gen
            return message, True
        else:
            return message, False
    
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}", False


def download_sample_csv():
    """Generate and return sample CSV as a downloadable file"""
    try:
        sample_df = CSVHandler.create_sample_csv()
        csv_bytes = sample_df.to_csv(index=False).encode("utf-8")
        return csv_bytes, "sample_leads.csv"
    except Exception as e:
        return f"Error: {str(e)}".encode("utf-8"), "error.csv"


# ============================================================================
# BUILD GRADIO UI
# ============================================================================

# Define style choices with proper capitalization
STYLE_CHOICES = [s.capitalize() for s in get_available_styles()]
STYLE_MAP = {s.capitalize(): s for s in get_available_styles()}

def get_style_value(choice):
    """Convert display value to internal value"""
    return STYLE_MAP.get(choice, "professional")

with gr.Blocks(title="WhatsApp Outreach Generator") as demo:
    gr.Markdown("""
    # 💬 WhatsApp Outreach Message Generator
    ### Create personalized outreach messages in seconds — free templates or AI-powered
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## ⚙️ Settings")
            
            use_ai = gr.Checkbox(label="Use AI Mode (OpenAI)", value=False)
            
            api_key_input = gr.Textbox(
                label="OpenAI API Key",
                placeholder="sk-...",
                type="password",
                visible=False
            )
            
            def toggle_api_key(use_ai):
                return gr.update(visible=use_ai)
            
            use_ai.change(
                toggle_api_key,
                inputs=[use_ai],
                outputs=[api_key_input]
            )
            
            test_btn = gr.Button("🔌 Test Connection", visible=False)
            connection_status = gr.Textbox(label="Connection Status", interactive=False, visible=False)
            
            def show_test_button(use_ai):
                return gr.update(visible=use_ai), gr.update(visible=use_ai)
            
            use_ai.change(
                show_test_button,
                inputs=[use_ai],
                outputs=[test_btn, connection_status]
            )
            
            test_btn.click(
                test_connection,
                inputs=[api_key_input],
                outputs=[connection_status, gr.State()]
            )
            
            style = gr.Dropdown(
                label="🎨 Message Style",
                choices=STYLE_CHOICES,
                value="Professional",
            )
            
            gr.Markdown("---")
            gr.Markdown("### 📊 Cost Tracking")
            cost_display = gr.Textbox(label="Session Summary", interactive=False, lines=8)
            
            refresh_btn = gr.Button("🔄 Refresh Cost")
            refresh_btn.click(get_analytics, outputs=[cost_display, gr.State()])
        
        with gr.Column(scale=2):
            with gr.Tabs():
                # ============================================================
                # TAB 1: BATCH PROCESSING
                # ============================================================
                with gr.TabItem("📁 Batch Processing"):
                    gr.Markdown("## 📁 Batch Message Generation")
                    gr.Markdown("Upload a CSV of leads to generate personalized messages for up to 100 contacts at once.")
                    
                    with gr.Row():
                        with gr.Column(scale=2):
                            batch_file = gr.File(
                                label="Upload leads CSV",
                                file_types=[".csv"],
                                type="filepath"
                            )
                        
                        with gr.Column(scale=1):
                            gr.Markdown("**Required columns:**")
                            gr.Markdown("""
                                            business_name
                                            business_type
                                            pain_point
                                            contact_name

                                                      """)
                            
                            sample_btn = gr.Button("⬇️ Download Sample CSV")
                            sample_output = gr.File(label="")
                            
                            sample_btn.click(
                                download_sample_csv,
                                outputs=[sample_output]
                            )
                    
                    batch_generate_btn = gr.Button("🚀 Generate Messages", variant="primary")
                    batch_status = gr.Textbox(label="Status", interactive=False)
                    batch_results = gr.Dataframe(
                        label="Generated Messages",
                        interactive=False
                    )
                    
                    # Use GPU-accelerated function
                    batch_generate_btn.click(
                        generate_batch_messages_gpu,
                        inputs=[batch_file, use_ai, style],
                        outputs=[batch_status, batch_results]
                    )
                
                # ============================================================
                # TAB 2: SINGLE LEAD
                # ============================================================
                with gr.TabItem("✏️ Single Lead"):
                    gr.Markdown("## ✏️ Single Lead Message Generator")
                    gr.Markdown("Manually enter a lead's details to generate one personalized message.")
                    
                    with gr.Row():
                        with gr.Column():
                            s_business_name = gr.Textbox(
                                label="Business Name *",
                                placeholder="e.g. Golden Spoon Cafe"
                            )
                            s_business_type = gr.Textbox(
                                label="Business Type *",
                                placeholder="e.g. restaurant"
                            )
                        
                        with gr.Column():
                            s_contact_name = gr.Textbox(
                                label="Contact Name *",
                                placeholder="e.g. Maria"
                            )
                            s_pain_point = gr.Textbox(
                                label="Pain Point *",
                                placeholder="e.g. low online reservation numbers",
                                lines=3
                            )
                    
                    single_generate_btn = gr.Button("✨ Generate Single Message", variant="primary")
                    
                    with gr.Row():
                        single_status = gr.Textbox(label="Status", interactive=False, scale=1)
                    
                    with gr.Row():
                        single_message = gr.Textbox(
                            label="Generated Message",
                            interactive=False,
                            lines=10,
                            scale=3
                        )
                    
                    with gr.Row():
                        tokens_display = gr.Number(label="Tokens Used", value=0, interactive=False, scale=1)
                        cost_display_single = gr.Number(label="Cost (USD)", value=0.0, interactive=False, scale=1)
                        source_display = gr.Textbox(label="Source", value="", interactive=False, scale=1)
                    
                    def generate_wrapper(business_name, business_type, contact_name, pain_point, use_ai, style):
                        internal_style = get_style_value(style)
                        return generate_single_message_gpu(business_name, business_type, contact_name, pain_point, use_ai, internal_style)
                    
                    # Use GPU-accelerated function
                    single_generate_btn.click(
                        generate_wrapper,
                        inputs=[s_business_name, s_business_type, s_contact_name, s_pain_point, use_ai, style],
                        outputs=[single_status, single_message, tokens_display, cost_display_single, source_display]
                    )
                
                # ============================================================
                # TAB 3: ANALYTICS
                # ============================================================
                with gr.TabItem("📊 Analytics"):
                    gr.Markdown("## 📊 Analytics & Cost Estimation")
                    
                    with gr.Row():
                        with gr.Column():
                            refresh_analytics_btn = gr.Button("🔄 Refresh Analytics", variant="primary")
                            analytics_display = gr.Textbox(label="Session Summary", interactive=False, lines=10)
                        
                        with gr.Column():
                            gr.Markdown("### 📅 Monthly Cost Estimator")
                            gr.Markdown("Estimate your projected monthly OpenAI cost based on expected daily lead volume.")
                            
                            daily_leads_input = gr.Number(label="Leads per day", value=50, minimum=1, maximum=1000)
                            working_days_input = gr.Number(label="Working days per month", value=22, minimum=1, maximum=31)
                            estimate_btn = gr.Button("Calculate Estimate", variant="primary")
                            estimate_display = gr.Textbox(label="Estimate", interactive=False, lines=8)
                    
                    gr.Markdown("---")
                    gr.Markdown("### 🧾 Usage History")
                    
                    with gr.Row():
                        history_btn = gr.Button("📋 Load History", variant="secondary")
                        history_status = gr.Textbox(label="Status", interactive=False, scale=1)
                    
                    history_data = gr.Dataframe(
                        label="Usage History",
                        interactive=False
                    )
                    
                    refresh_analytics_btn.click(
                        get_analytics,
                        outputs=[analytics_display, gr.State()]
                    )
                    
                    estimate_btn.click(
                        calculate_estimate,
                        inputs=[daily_leads_input, working_days_input],
                        outputs=[estimate_display]
                    )
                    
                    history_btn.click(
                        get_usage_history,
                        outputs=[history_status, history_data]
                    )
    
    # Initialize cost display
    demo.load(get_analytics, outputs=[cost_display, gr.State()])


# ============================================================================
# RUN THE APP
# ============================================================================
if __name__ == "__main__":
    # Keep share=True for ZeroGPU to work
    demo.launch(share=True)
