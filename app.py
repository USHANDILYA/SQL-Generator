import streamlit as st
import google.generativeai as genai
import sqlite3

GOOGLE_API_KEY = st.secrets["API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# Sample DB for demo (optional - for Live SQL Execution)
def get_db_connection():
    conn = sqlite3.connect("sample.db")
    return conn

def main():
    st.set_page_config(page_title="SQL Query Generator", page_icon=":robot:", layout="wide")
    st.sidebar.title("Navigation")
    menu = ["Home", "Generate SQL", "How To Use"]
    choice = st.sidebar.radio("Go to", menu)

    # App theme (customize in .streamlit/config.toml for more)
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1rem; }
        .reportview-container .markdown-text-container { font-size: 1.2rem; }
        h1, h3, h4 { text-align: center; }
        </style>
        """,
        unsafe_allow_html=True
    )

    if choice == "Home":
        st.markdown("<h1>SQL Query Generator</h1>", unsafe_allow_html=True)
        st.markdown(
            """
            <h4>Generate SQL queries from plain English. Explain and preview output, then run them live!</h4>
            <ul>
                <li>Type what you want in English</li>
                <li>Get SQL code, sample output table, simple explanation</li>
                <li>Optionally run code on a demo database</li>
            </ul>
            """,
            unsafe_allow_html=True
        )
    elif choice == "Generate SQL":
        st.markdown("<h1>Generate and Explore SQL Queries</h1>", unsafe_allow_html=True)
        with st.expander("See Example Inputs & Tips"):
            st.info("Example: 'Get the total sales per country for 2023 ordered by sales descending.'\n\nTips: Be specific with fields, aggregations, filters, and ordering when possible.")

        col1, col2 = st.columns(2)
        with col1:
            text_input = st.text_area("Enter your query here in plain English", key="input", height=150)
            submit = st.button("Generate SQL Query & Explanation")

            if submit and text_input.strip():
                with st.spinner("Generating SQL query..."):
                    template = """
                    Create a SQL query snippet for this request:

                    '''
                    {text_input}
                    '''
                    Only return a SQL code snippet.
                    """
                    formatted_template = template.format(text_input=text_input)
                    response = model.generate_content(formatted_template)
                    sql_query = response.text.strip().lstrip("``````")

                    expected_output_template = """
                    What could be the expected output of this SQL query?

                    '''
                    {sql_query}
                    '''
                    Provide a small sample tabular response with no explanation.
                    """
                    eo_formatted = expected_output_template.format(sql_query=sql_query)
                    eoutput = model.generate_content(eo_formatted).text

                    explanation_template = """
                    Explain this SQL Query in one paragraph:

                    '''
                    {sql_query}
                    '''
                    """
                    expl_formatted = explanation_template.format(sql_query=sql_query)
                    explanation = model.generate_content(expl_formatted).text

                    # Display results
                    with col2:
                        st.success("SQL Query Generated:")
                        st.code(sql_query, language="sql")
                        st.button("Copy SQL Query", on_click=lambda: st.session_state.update({"copy_sql": sql_query}))
                        st.success("Expected Output (Example):")
                        st.markdown(eoutput)
                        st.success("Explanation:")
                        st.markdown(explanation)

                        # Optional: Execution on sample DB
                        if st.checkbox("Run on Sample Database (demo)", False):
                            try:
                                conn = get_db_connection()
                                df = pd.read_sql_query(sql_query, conn)
                                st.dataframe(df)
                                conn.close()
                            except Exception as e:
                                st.warning(f"Execution error: {e}")

                        # Downloads
                        st.download_button("Download SQL", sql_query, file_name="query.sql")
                        st.download_button("Download Output", eoutput, file_name="expected_output.txt")
                        st.download_button("Download Explanation", explanation, file_name="explanation.txt")
        st.markdown("**Query History:**")
        if "history" not in st.session_state:
            st.session_state["history"] = []
        if submit and text_input.strip():
            st.session_state["history"].append({"query": text_input, "sql": sql_query})
        for past in st.session_state["history"][-5:][::-1]:
            st.markdown(f"**Input:** {past['query']}  \n**SQL:** `{past['sql']}`")

    elif choice == "How To Use":
        st.markdown("<h1>How To Use SQL Generator</h1>", unsafe_allow_html=True)
        st.info("1. Write your question in plain English.\n2. Click generate.\n3. Review the SQL query, explanation, and fetch sample output.\n4. (Optional) Run SQL on demo database.")

if __name__ == "__main__":
    main()
