from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from groq import Groq

FRONTEND_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "frontend"
)

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

DATABASE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "database",
    "database.db"
)


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def save_agent_run(task, agent_name, result):
    connection = get_db()

    connection.execute(
        """
        INSERT INTO agent_runs (task, agent_name, result)
        VALUES (?, ?, ?)
        """,
        (task, agent_name, result)
    )

    connection.commit()
    connection.close()


def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            agent_name TEXT,
            result TEXT,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    columns = connection.execute(
        "PRAGMA table_info(agent_runs)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "agent_name" not in column_names:
        connection.execute(
            "ALTER TABLE agent_runs ADD COLUMN agent_name TEXT"
        )

    connection.commit()
    connection.close()


@app.route("/")
def home():
    return send_from_directory(FRONTEND_FOLDER, "index.html")


@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(FRONTEND_FOLDER, filename)


@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "team": "ByteX"
    })


@app.route("/api/agent", methods=["POST"])
def agent():
    data = request.get_json()

    event = data.get("task", "").strip()

    if not event:
        return jsonify({
            "error": "No business event provided"
        }), 400

    try:
        # ---------------------------------------------------------
        # AGENT 1 — EVENT ANALYST
        # ---------------------------------------------------------

        analyst_prompt = f"""
You are the Event Analyst Agent of ByteX EventMind.

Analyze this real-time business event:

{event}

Return ONLY valid JSON matching the required schema.

Rules:
- Be concise.
- Do not invent facts.
- Use only information supported by the event.
- If information is missing, list it under missing_information.
- Keep each string short.
- Maximum 5 items in each array.
"""

        analyst_response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": analyst_prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "event_analysis",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "event_type": {
                                "type": "string"
                            },
                            "what_happened": {
                                "type": "string"
                            },
                            "entities_involved": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            },
                            "urgency": {
                                "type": "string",
                                "enum": [
                                    "LOW",
                                    "MEDIUM",
                                    "HIGH",
                                    "CRITICAL",
                                    "IMMEDIATE"
                                ]
                            },
                            "important_information": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            },
                            "possible_business_impact": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            },
                            "missing_information": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            },
                            "assumptions": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            }
                        },
                        "required": [
                            "event_type",
                            "what_happened",
                            "entities_involved",
                            "urgency",
                            "important_information",
                            "possible_business_impact",
                            "missing_information",
                            "assumptions"
                        ],
                        "additionalProperties": False
                    }
                }
            },
            include_reasoning=False
        )

        analyst_result = analyst_response.choices[0].message.content

        save_agent_run(
            event,
            "Event Analyst",
            analyst_result
        )

        save_agent_run(
            event,
            "Event Analyst",
            analyst_result
        )

        # ---------------------------------------------------------
        # AGENT 2 — IMPACT AGENT
        # ---------------------------------------------------------

        impact_prompt = f"""
You are the Impact Assessment Agent of ByteX EventMind.

Determine the potential business impact of this event.

BUSINESS EVENT:
{event}

EVENT ANALYST JSON:
{analyst_result}

Return ONLY valid JSON matching the required schema.

Rules:
- Be concise and practical.
- Do not invent unsupported facts.
- Base the assessment on the event and analyst JSON.
- Keep each string short.
- Maximum 5 items in each array.
"""

        impact_response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": impact_prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "impact_assessment",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "severity": {
                                "type": "string",
                                "enum": [
                                    "LOW",
                                    "MEDIUM",
                                    "HIGH",
                                    "CRITICAL"
                                ]
                            },
                            "urgency": {
                                "type": "string",
                                "enum": [
                                    "LOW",
                                    "MEDIUM",
                                    "HIGH",
                                    "CRITICAL",
                                    "IMMEDIATE"
                                ]
                            },
                            "affected_areas": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            },
                            "business_impact": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            },
                            "risk": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            }
                        },
                        "required": [
                            "severity",
                            "urgency",
                            "affected_areas",
                            "business_impact",
                            "risk"
                        ],
                        "additionalProperties": False
                    }
                }
            },
            include_reasoning=False
        )

        impact_result = impact_response.choices[0].message.content

        save_agent_run(
            event,
            "Impact Agent",
            impact_result
        )

        # ---------------------------------------------------------
        # AGENT 3 — DECISION AGENT
        # ---------------------------------------------------------

        decision_prompt = f"""
You are the Decision Agent of ByteX EventMind.

Your job is to decide what should happen next based on the
business event and the previous agents' structured analysis.

BUSINESS EVENT:
{event}

EVENT ANALYST JSON:
{analyst_result}

IMPACT ASSESSMENT JSON:
{impact_result}

Return ONLY valid JSON matching the required schema.

Rules:
- Recommend actions, do not claim execution.
- Prefer practical, automatable workflows.
- Consider safety and authorization.
- Require human approval for sensitive or irreversible actions.
- Keep every string concise.
- Maximum 5 items in each array.
"""

        decision_response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": decision_prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "business_decision",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "recommended_action": {
                                "type": "string"
                            },
                            "reasoning": {
                                "type": "string"
                            },
                            "priority": {
                                "type": "string",
                                "enum": [
                                    "LOW",
                                    "MEDIUM",
                                    "HIGH",
                                    "CRITICAL"
                                ]
                            },
                            "required_workflow": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            },
                            "human_approval_required": {
                                "type": "string",
                                "enum": [
                                    "YES",
                                    "NO"
                                ]
                            },
                            "actions_must_not_be_taken": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            }
                        },
                        "required": [
                            "recommended_action",
                            "reasoning",
                            "priority",
                            "required_workflow",
                            "human_approval_required",
                            "actions_must_not_be_taken"
                        ],
                        "additionalProperties": False
                    }
                }
            },
            include_reasoning=False
        )

        decision_result = decision_response.choices[0].message.content

        save_agent_run(
            event,
            "Decision Agent",
            decision_result
        )

        # ---------------------------------------------------------
        # AGENT 4 — CRITIC AGENT
        # ---------------------------------------------------------

        critic_prompt = f"""
You are the Critic Agent of ByteX EventMind.

Review the proposed decision and identify mistakes, risks,
missing information, unnecessary actions, or authorization concerns.

BUSINESS EVENT:
{event}

EVENT ANALYST JSON:
{analyst_result}

IMPACT ASSESSMENT JSON:
{impact_result}

PROPOSED DECISION JSON:
{decision_result}

Return ONLY valid JSON matching the required schema.

Rules:
- Check whether the proposed decision is justified.
- Identify safety and authorization risks.
- Consider missing information before sensitive actions.
- Do not invent unsupported facts.
- Keep every string concise.
- Maximum 5 items in each array.
- The final verdict MUST be exactly one of:
  APPROVED
  APPROVED WITH CAUTION
  REJECTED
"""

        critic_response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": critic_prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "decision_critique",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "decision_validity": {
                                "type": "string"
                            },
                            "safety_risks": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            },
                            "missing_information": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            },
                            "unnecessary_actions": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            },
                            "authorization_concerns": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "maxItems": 5
                            },
                            "final_verdict": {
                                "type": "string",                               
                            },
                            "reasoning": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "decision_validity",
                            "safety_risks",
                            "missing_information",
                            "unnecessary_actions",
                            "authorization_concerns",
                            "final_verdict",
                            "reasoning"
                        ],
                        "additionalProperties": False
                    }
                }
            },
            include_reasoning=False
        )

        critic_result = critic_response.choices[0].message.content

        save_agent_run(
            event,
            "Critic Agent",
            critic_result
        )

        # ---------------------------------------------------------
        # AGENT 5 — FINALIZER AGENT
        # ---------------------------------------------------------

        finalizer_prompt = f"""
You are the Finalizer Agent of ByteX EventMind.

Create the final safe response plan after reviewing all previous agents.

BUSINESS EVENT:
{event}

EVENT ANALYST JSON:
{analyst_result}

IMPACT ASSESSMENT JSON:
{impact_result}

DECISION JSON:
{decision_result}

CRITIC JSON:
{critic_result}

Return ONLY valid JSON matching the required schema.

Rules:
- Clearly distinguish recommendation from execution.
- Never claim an action was actually executed.
- If the Critic rejected the decision, recommend escalation or human review.
- Preserve important missing-information and approval requirements.
- Keep every string concise.
"""

        finalizer_response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": finalizer_prompt
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "final_response",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "final_status": {
                                "type": "string",
                                "enum": [
                                    "READY",
                                    "ESCALATE",
                                    "HUMAN_REVIEW_REQUIRED"
                                ]
                            },
                            "event_summary": {
                                "type": "string"
                            },
                            "severity": {
                                "type": "string",
                                "enum": [
                                    "LOW",
                                    "MEDIUM",
                                    "HIGH",
                                    "CRITICAL"
                                ]
                            },
                            "recommended_action": {
                                "type": "string"
                            },
                            "reason": {
                                "type": "string"
                            },
                            "human_approval": {
                                "type": "string",
                                "enum": [
                                    "REQUIRED",
                                    "NOT REQUIRED",
                                    "CONDITIONAL"
                                ]
                            },
                            "next_workflow_step": {
                                "type": "string"
                            },
                            "audit_summary": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "final_status",
                            "event_summary",
                            "severity",
                            "recommended_action",
                            "reason",
                            "human_approval",
                            "next_workflow_step",
                            "audit_summary"
                        ],
                        "additionalProperties": False
                    }
                }
            },
            include_reasoning=False
        )

        finalizer_result = finalizer_response.choices[0].message.content

        save_agent_run(
            event,
            "Finalizer Agent",
            finalizer_result
        )

        # ---------------------------------------------------------
        # RETURN COMPLETE AGENT PIPELINE
        # ---------------------------------------------------------

        return jsonify({
            "status": "success",
            "event": event,
            "analyst": analyst_result,
            "impact": impact_result,
            "decision": decision_result,
            "critic": critic_result,
            "finalizer": finalizer_result
        })

    except Exception as error:
        return jsonify({
            "status": "error",
            "error": str(error)
        }), 500


@app.route("/api/database-test")
def database_test():
    connection = get_db()

    connection.execute(
        """
        INSERT INTO agent_runs (task, result)
        VALUES (?, ?)
        """,
        ("Database test", "SQLite is working!")
    )

    connection.commit()

    cursor = connection.execute(
        "SELECT * FROM agent_runs ORDER BY id DESC LIMIT 1"
    )

    row = cursor.fetchone()

    connection.close()

    return jsonify({
        "database": "connected",
        "record": dict(row)
    })


@app.route("/api/history", methods=["GET"])
def history():
    admin_key = request.headers.get("X-Admin-Key")

    if admin_key != os.getenv("ADMIN_HISTORY_KEY"):
        return jsonify({"error": "Unauthorized"}), 401

    connection = get_db()

    rows = connection.execute("""
        SELECT id, task, agent_name, result, status, created_at
        FROM agent_runs
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return jsonify({
        "count": len(rows),
        "records": [dict(row) for row in rows]
    })


init_db()

if __name__ == "__main__":
    app.run(debug=True)