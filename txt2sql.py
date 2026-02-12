from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from langchain_ibm import WatsonxLLM
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from dotenv import load_dotenv
import os
import json
import mysql.connector
import re



from data import get_table_metadata

load_dotenv()
wx_api = os.getenv("APIKEY")
project_id = os.getenv("PROJECT_ID")

# ============================================================
# 1. GRAPH STATE
# ============================================================
class GraphState(BaseModel):
    question: str = ""
    full_metadata: list = []
    sql_query: str = ""
    sql_result: list | None = None
    attempts: int = 0

    
    valid: bool = False
    issues: list[str] = []
    regenerate_sql: bool = False
    previous_sql: str = ""




# ============================================================
# 2. CONFIGURE WATSONX LLM
# ============================================================
llm = WatsonxLLM(
    model_id="mistralai/mistral-medium-2505",
    url="https://us-south.ml.cloud.ibm.com",
    apikey=wx_api,
    project_id=project_id,
    params={
        GenParams.MAX_NEW_TOKENS: 3000,
        GenParams.TEMPERATURE: 0,
    },
)


def execute_sql_query(sql_query: str):
    try:
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASS"),
            database=os.getenv("MYSQL_DB"),
            port=os.getenv("MYSQL_PORT")
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        # Return list even on error
        return [{"error": str(e)}]


def extract_sql_block(text: str) -> str:
    """
    Extracts SQL code inside ```sql ... ``` or ``` ... ``` blocks.
    Returns the full content inside the block.
    If no block is found, returns the original string.
    """
    # Pattern that matches:
    # ```sql
    #   <content>
    # ```
    pattern = r"```(?:sql)?\s*(.*?)```"
    match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()
    return text.strip()


def extract_json_block(text: str):
    """Extract JSON enclosed inside ```json ... ``` or ``` ... ``` blocks."""
    pattern = r"```(?:json)?\s*(.*?)```"
    match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def route_validator(state: GraphState):
    if state.valid:
        return "done"
    if state.attempts >= 5:
        return "done"   # stop infinite loops
    return "retry"


# ============================================================
# SQL GENERATOR AGENT
# ============================================================
def sql_generator_agent(state: GraphState) -> dict:
    print("SQL Generator Agent generating SQL...")

    # If validator gave issues, show them to the LLM
    issues = state.issues or []

    issues_text = "\n".join(f"- {i}" for i in issues) if issues else "None"


    prompt = f"""
You are a senior SQL architect.

You are given:

1. USER QUERY:
{state.question}

2. FULL TABLE METADATA (JSON):
{json.dumps(state.full_metadata, indent=4)}

3. PREVIOUS SQL QUERY (Fix errors or improve it):
{state.previous_sql}

4. VALIDATION FEEDBACK (Fix ALL issues listed):
{issues_text}

IMPORTANT:
Based on the table and column descriptions You must deduce which tables are needed.
Do NOT assume all tables are required.

TABLE SELECTION RULES:
1. Select ONLY tables required to answer the question.
2. A table is relevant if:
   - It contains columns needed in the query.
   - It is required to join other needed tables.
   - It contains filtering information from the question.

3. Ignore unrelated tables.

SQL GENERATION RULES:
### SELECT
Pick columns which provide all the related values needed for the explanation of the question.

### JOIN
Use correct JOIN keys:
- product_id
- raw_material_id
- scenario_id
- record_id

### SUM + JOIN Rules
When summing across joined tables:
- Join the tables first
- Apply SUM() AFTER joining
- Group by the higher-level entity (scenario, product, etc.)


### WHERE
### 1. Fuzzy matching for categorical values
NEVER use exact matches (=) for text fields.

Whenever the user mentions category labels like product names, supplier names etc :
Use:
    column LIKE '%value%'
NOT EXACT MATCHES.

Examples:
- "Chem Alloy" →  column LIKE '%Chem Alloy%'
- "H1" → column LIKE '%H1%'
- "Ankara" → column LIKE '%Ankara%'

### OUTPUT FORMAT
Return ONLY valid SQL.
No explanation.
No comments.
No markdown.
;

### Example:
USER QUERY: Check all existing recipes. Are there any raw material inventory shortages?
SQL Query:
SELECT
    r.raw_material_id,
    m.raw_material_name,
    m.stock_quantity,
    SUM(r.recipe_quantity) AS total_required_quantity,
    (m.stock_quantity - SUM(r.recipe_quantity)) AS stock_balance
FROM
    opt_recipe AS r
JOIN
    opt_scenario AS s
 ON s.scenario_id = r.scenario_id
JOIN
    master_raw_material AS m 
    ON m.raw_material_id = r.raw_material_id
GROUP BY
	r.raw_material_id,
    m.raw_material_name,
    m.stock_quantity
HAVING
	m.stock_quantity < SUM(r.recipe_quantity);

    
GENERATE THE SQL NOW:
"""

    sql = llm.invoke(prompt).strip()
    sql = extract_sql_block(sql)

    print(sql)
    return {"sql_query": sql}



# ============================================================
# 5. SQL EXECUTOR NODE
# ============================================================
def sql_executor_node(state: GraphState):
    print("\nExecuting SQL...\n")

    sql_cleaned = (
        state.sql_query.replace("```sql", "")
                       .replace("```", "")
                       .strip()
    )

    result = execute_sql_query(sql_cleaned)
    print(result)
    return {"sql_result": result}




# ============================================================
# SQL VALIDATOR AGENT
# ============================================================

def validator_agent(state: GraphState) -> dict:
    print("\nValidator Agent checking results...\n")

    user_query = state.question
    sql = state.sql_query
    result = state.sql_result or []
    metadata = state.full_metadata

    prompt = f"""
You are an expert SQL validator.

You are given:
USER QUERY:
{user_query}

SQL QUERY:
{sql}

SQL RESULT:
{json.dumps(result, indent=4)}

TABLE METADATA:
{json.dumps(metadata, indent=4)}

You must check ALL of the following:

### 1. SQL SYNTAX / EXECUTION ISSUES
- Did MySQL return an error?
- Are any SQL keywords or clauses incorrect?
- Were invalid columns used?

### 2. RESULT RELEVANCE (VERY IMPORTANT)
Determine whether the returned rows contain the attributes needed to answer the question.

Examples:
- If user asks about "stock status" → must include stock_quantity or stock.
- If user asks about "density and moisture" → must include both properties density and moisture.
- If user asks about "recipe usage" → must include recipe_quantity or recipe_percentage.
- If user asks about "scenario" → must include scenario_id.
- If user asks about "cost" → must include unit_cost, total_cost, or related cost fields.

If any required fields are **missing**, you must mark SQL as invalid.

### 3. OUTPUT STRICT JSON ONLY:
{{
  "valid": true/false,
  "issues": ["..."],
  "regenerate_sql": true/false
}}

OUTPUT JSON:
"""

    response = llm.invoke(prompt)
    print("\n[Validator LLM raw response]\n", response)


    clean = extract_json_block(response)


    # Robust parsing and guaranteed keys in return
    try:
        parsed = json.loads(clean)
        valid = bool(parsed.get("valid", False))
        issues = parsed.get("issues", []) or []
        regenerate = bool(parsed.get("regenerate_sql", parsed.get("regenerate", False)))

    except Exception as e:
        print("Validator parse error:", e)
        print("Raw response:", response)

        # Force retry
        valid = False
        issues = ["Validator returned invalid JSON."]
        regenerate = True

    # ---------------------------
    # ALWAYS RETURN CLEAN KEYS
    # ---------------------------
    return {
        "valid": valid,
        "issues": issues,
        "regenerate_sql": regenerate,
        "attempts": state.attempts + 1,
        "previous_sql": state.sql_query

    }





# ============================================================
# 4. BUILD LANGGRAPH WORKFLOW
# ============================================================
workflow = StateGraph(GraphState)
workflow.add_node("sql_agent", sql_generator_agent)
workflow.add_node("executor", sql_executor_node)
workflow.add_node("validator", validator_agent)


workflow.set_entry_point("sql_agent")
workflow.add_edge("sql_agent", "executor")  
workflow.add_edge("executor", "validator")
# If invalid, loop back to SQL agent

workflow.add_conditional_edges(
    source="validator",
    path=route_validator,  
    path_map={
        "retry": "sql_agent",
        "done": END
    }
)

app = workflow.compile()



# ============================================================
# 5. RUN APP
# ============================================================
def run_agentic_app(question: str):
    print("\nRunning Agentic SQL Workflow...\n")

    # ----------------------------------------------------------
    # Load full table descriptions
    # ----------------------------------------------------------
    raw_metadata = get_table_metadata()
    table_desc = json.loads(raw_metadata) if isinstance(raw_metadata, str) else raw_metadata

    # ----------------------------------------------------------
    # Build combined metadata for all tables
    # ----------------------------------------------------------
    all_table_metadata = []

    for tbl, meta in table_desc.items():
        all_table_metadata.append({
            "table_name": tbl,
            "table_description": meta.get("description", ""),
            "columns": meta.get("columns", []),     # columns already included
            "relationships": meta.get("relationships", {}),
            "examples": meta.get("examples", []),
            "usuage": meta.get("usuage", [])

        })

    # ----------------------------------------------------------
    # RUN SQL AGENT
    # ----------------------------------------------------------
    final_state = app.invoke({"question": question,
        "full_metadata": all_table_metadata
    })

    print("\n==============================")
    print(" GENERATED SQL QUERY")
    print("==============================")
    sql=final_state["sql_query"]
    
    print("\n==============================")
    print(" SQL EXECUTION RESULT")
    print("==============================")
    print(final_state["sql_result"])

    print("\n==============================")
    print(" VALIDATION STATUS")
    print("==============================")
    print("Valid:", final_state["valid"])
    print("Issues:", final_state["issues"])

    print("\nDone.\n")


# ============================================================
# 6. EXECUTE
# ============================================================



if __name__ == "__main__":
    run_agentic_app("create an alert if CH-001 exceeds the price 20 dollar ")
