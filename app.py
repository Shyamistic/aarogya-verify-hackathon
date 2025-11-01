import streamlit as st
import pandas as pd
from agents import validation_agent, enrichment_agent, qa_agent, npi_tool, pdf_tool
from crewai import Task, Crew, Process
import json

st.set_page_config(layout="wide")
st.title("Aarogya-Verify 🩺: Agentic AI Provider Validation")
st.info("Upload the `mock_providers.csv` to demo the validation workflow.")

uploaded_csv = st.file_uploader("1. Upload Provider CSV", type="csv")

if uploaded_csv:
    input_df = pd.read_csv(uploaded_csv)
    st.subheader("Input Data (From CSV)")
    st.dataframe(input_df)

    st.subheader("2. Select a Provider to Validate")
    selected_index = st.selectbox("Select Provider", input_df.index, format_func=lambda x: input_df.iloc[x]['Provider_Name'])
    
    provider = input_df.iloc[selected_index]
    
    # Simulate finding the associated PDF
    # In a real app, this path would come from a database
    pdf_path = provider['License_PDF']
    st.write(f"**Associated License File:** `{pdf_path}`")

    if st.button(f"Validate Dr. {provider['Provider_Name']}", type="primary"):
        
        # --- Create Tasks Dynamically ---
        
        # 1. Validation Task
        task_validate = Task(
            description=(
                f"Look up the provider with NPI number: {provider['NPI']}. "
                "Return the full JSON data you receive."
            ),
            expected_output="A JSON object with the provider's data from the NPI registry.",
            agent=validation_agent,
            tools=[npi_tool]
        )

        # 2. Enrichment Task
        task_enrich = Task(
            description=(
                f"Process the PDF file located at '{pdf_path}'. "
                "Extract its full text and find the provider's license number."
            ),
            expected_output=(
                "A JSON object with 'full_text' and 'extracted_license'."
            ),
            agent=enrichment_agent,
            tools=[pdf_tool]
        )

        # 3. QA Task (The Synthesizer)
        task_qa = Task(
            description=(
                f"You have been given three sources of data for provider: {provider['Provider_Name']}.\n"
                "1. **Input CSV Data**:\n"
                f"{provider.to_json()}\n\n"
                "2. **NPI API Data**: (from task_validate's output)\n"
                "3. **PDF OCR Data**: (from task_enrich's output)\n\n"
                "Your job is to:\n"
                "a) Compare 'Phone', 'Address', and 'License' from all sources.\n"
                "b) Create a 'Final Verified Profile' using the NPI/PDF data as the source of truth.\n"
                "c) List all discrepancies you found.\n"
                "d) Calculate a 'Confidence Score' based on how many fields matched the input CSV."
            ),
            expected_output=(
                "A final JSON object containing:\n"
                "- `final_profile`: {name, phone, address, license}\n"
                "- `discrepancies`: A list of strings (e.g., 'Phone mismatch: CSV(555-1234) vs API(555-1233)')\n"
                "- `confidence_score`: A percentage string (e.g., '66%')"
            ),
            agent=qa_agent,
            context=[task_validate, task_enrich] # This task depends on the first two
        )

        # --- Create and Run the Crew ---
        with st.spinner("🚀 Agents are validating..."):
            
            # Re-instantiate crew for each run to avoid state issues
            provider_crew = Crew(
                agents=[validation_agent, enrichment_agent, qa_agent],
                tasks=[task_validate, task_enrich, task_qa],
                process=Process.sequential,
                verbose=True  # <-- This was the fix for verbose=2
            )
            
            result = provider_crew.kickoff()

            # --- Display Results ---
            st.subheader("✅ Validation Complete!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("Input Data (Recap)")
                st.json(provider.to_json())

                st.warning("NPI API Result (Source of Truth)")
                st.json(task_validate.output.raw) # <-- This was the fix for .output()

            with col2:
                # This is the new, cleanly indented block
                st.success("Final Validation Report (from QA Agent)")
                try:
                    # Parse the raw JSON string from the agent's output
                    clean_result = json.loads(result.raw)
                    st.json(clean_result)
                except Exception as e:
                    # If parsing fails, just show the raw text
                    st.error(f"Failed to parse agent output: {e}")
                    st.text(result.raw)

            st.subheader("Differentiator: PDF OCR Result")
            with st.expander("Show extracted text from PDF"):
                st.text(task_enrich.output.raw) # <-- This was the fix for .output()
