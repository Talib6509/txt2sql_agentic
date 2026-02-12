# The system follows an **agentic loop**:
User Question -> SQL Generator Agent -> SQL Executor -> SQL Validator Agent -> (If invalid → Retry) -> END

The workflow continues until:
- SQL is valid, or
- Maximum retry attempts (5) are reached.

## Components

### 1️ Graph State (`GraphState`)

Maintains workflow state across nodes:

- `question` – User query
- `full_metadata` – All table descriptions
- `sql_query` – Generated SQL
- `sql_result` – Execution result
- `attempts` – Retry counter
- `valid` – Validation status
- `issues` – Validation feedback
- `regenerate_sql` – Retry flag
- `previous_sql` – Last generated SQL

---

### 2️ SQL Generator Agent

**Purpose:** Convert natural language into SQL.

Inputs:
- User question
- Full database metadata
- Previous SQL (if retry)
- Validation issues

Rules enforced:
- Select only required tables
- Correct JOIN keys
- SUM after JOIN
- Fuzzy matching (`LIKE '%value%'`)
- No explanations or markdown
- Strict SQL output only

Model: mistralai/mistral-medium-2505 (Watsonx)
---

### 3️ SQL Executor Node

- Cleans SQL
- Executes query on MySQL
- Returns results as list of dictionaries
- Captures errors as structured output

---

### 4️ SQL Validator Agent

Validates:

### Syntax & Execution
- MySQL errors
- Invalid columns
- Clause issues

### Result Relevance
Ensures required fields exist based on question intent:

Examples:
- Stock query → must include `stock_quantity`
- Cost query → must include `cost` fields
- Scenario query → must include `scenario_id`

Returns strict JSON:

```json
{
  "valid": true,
  "issues": [],
  "regenerate_sql": false
}
```

If invalid:
Issues passed back to SQL generator
SQL regenerated
Loop continues

## Retry Logic
route_validator()
Rules:

If valid = True → END
If attempts >= 5 → END
Else → Retry SQL generation
Prevents infinite loops.




