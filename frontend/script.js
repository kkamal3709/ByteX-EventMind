const button = document.getElementById("testButton");
const result = document.getElementById("result");
const problemInput = document.getElementById("problemInput");


button.addEventListener("click", async () => {

    const event = problemInput.value.trim();

    if (!event) {
        result.innerHTML = `
            <div class="empty-state">
                ⚠️ Please enter a business event first.
            </div>
        `;
        return;
    }


    button.disabled = true;
    button.textContent = "Processing...";


    result.innerHTML = `
        <div class="processing">
            <div class="spinner"></div>
            <h3>ByteX EventMind is thinking...</h3>
            <p>Running multi-agent analysis</p>
        </div>
    `;


    try {

        const response = await fetch(
            "/api/agent",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    task: event
                })
            }
        );


        const data = await response.json();


        if (!response.ok) {
            throw new Error(
                data.error || "Something went wrong."
            );
        }


        result.innerHTML = `

            ${createEventHeader(event)}

            ${createDecisionSummary(data)}

            ${createAgentCard(
                "01",
                "Event Analyst",
                "🔎",
                data.analyst
            )}

            ${createAgentCard(
                "02",
                "Impact Agent",
                "📊",
                data.impact
            )}

            ${createAgentCard(
                "03",
                "Decision Agent",
                "🧠",
                data.decision
            )}

            ${createAgentCard(
                "04",
                "Critic Agent",
                "🔴",
                data.critic
            )}

            ${createAgentCard(
                "05",
                "Finalizer Agent",
                "🏆",
                data.finalizer
            )}

        `;

    } catch (error) {

        result.innerHTML = `
            <div class="error-state">
                <h3>⚠️ ByteX could not process the event</h3>
                <p>${escapeHTML(error.message)}</p>
            </div>
        `;

    } finally {

        button.disabled = false;
        button.textContent = "Analyze Event";

    }

});


/* =========================
   EVENT HEADER
========================= */

function createEventHeader(event) {

    return `
        <div class="event-header">

            <span class="event-badge">
                LIVE EVENT
            </span>

            <h2>
                ${escapeHTML(event)}
            </h2>

        </div>
    `;
}


/* =========================
   DECISION SUMMARY
========================= */

function createDecisionSummary(data) {
    let finalizer = {};
    let impact = {};
    let decision = {};
    let critic = {};

    try {
        finalizer = JSON.parse(data.finalizer || "{}");
    } catch (e) {
        finalizer = {};
    }

    try {
        impact = JSON.parse(data.impact || "{}");
    } catch (e) {
        impact = {};
    }

    try {
        decision = JSON.parse(data.decision || "{}");
    } catch (e) {
        decision = {};
    }

    try {
        critic = JSON.parse(data.critic || "{}");
    } catch (e) {
        critic = {};
    }

    const severity =
        finalizer.severity
        || impact.severity
        || "—";

    const urgency =
        impact.urgency
        || "—";

    const verdict =
        critic.final_verdict
        || "—";

    const humanApproval =
        finalizer.human_approval
        || decision.human_approval_required
        || "—";

    const action =
        finalizer.recommended_action
        || decision.recommended_action
        || "Review the recommended workflow below.";

    return `
        <div class="decision-summary">

            <div class="summary-heading">
                <div>
                    <span class="summary-eyebrow">
                        BYTE X EVENTMIND
                    </span>

                    <h2>Decision Summary</h2>
                </div>

                <span class="summary-live">
                    ● ANALYSIS COMPLETE
                </span>
            </div>

            <div class="summary-grid">

                <div class="summary-stat severity-stat">
                    <span class="stat-label">
                        SEVERITY
                    </span>

                    <strong>
                        ${escapeHTML(severity)}
                    </strong>
                </div>

                <div class="summary-stat">
                    <span class="stat-label">
                        URGENCY
                    </span>

                    <strong>
                        ${escapeHTML(urgency)}
                    </strong>
                </div>

                <div class="summary-stat">
                    <span class="stat-label">
                        CRITIC VERDICT
                    </span>

                    <strong>
                        ${escapeHTML(verdict)}
                    </strong>
                </div>

                <div class="summary-stat">
                    <span class="stat-label">
                        HUMAN APPROVAL
                    </span>

                    <strong>
                        ${escapeHTML(humanApproval)}
                    </strong>
                </div>

            </div>

            <div class="summary-action">

                <span class="stat-label">
                    RECOMMENDED ACTION
                </span>

                <p>
                    ${escapeHTML(action)}
                </p>

            </div>

        </div>
    `;
}


function extractSeverity(text) {
    const match = String(text || "").match(
        /\b(LOW|MEDIUM|HIGH|CRITICAL)\b/i
    );

    return match ? match[1].toUpperCase() : null;
}


function extractUrgency(text) {
    const raw = String(text || "")
        .replace(/<br\s*\/?>/gi, "\n")
        .replace(/\r/g, "");

    // Find the URGENCY section.
    const match = raw.match(
        /(?:^|\n)\s*(?:\d+\.\s*)?URGENCY\s*[:\-–—]?\s*([\s\S]*?)(?=\n\s*(?:\d+\.\s*)?[A-Z][A-Z\s/&-]{2,}\s*[:\-–—]?\s*|\n\s*\d+\.\s|$)/i
    );

    if (!match) {
        // Fallback: search anywhere for a clear urgency word.
        if (/\bIMMEDIATE\b/i.test(raw)) return "IMMEDIATE";
        if (/\bHIGH\b/i.test(raw)) return "HIGH";
        if (/\bMEDIUM\b/i.test(raw)) return "MEDIUM";
        if (/\bLOW\b/i.test(raw)) return "LOW";
        return null;
    }

    const value = match[1]
        .replace(/[*_`|]/g, " ")
        .replace(/-{2,}/g, " ")
        .replace(/\s+/g, " ")
        .trim();

    if (/immediate|urgent|right away|as soon as possible|within the next few minutes/i.test(value)) {
        return "IMMEDIATE";
    }

    if (/\bHIGH\b/i.test(value)) {
        return "HIGH";
    }

    if (/\bMEDIUM\b/i.test(value)) {
        return "MEDIUM";
    }

    if (/\bLOW\b/i.test(value)) {
        return "LOW";
    }

    return null;
}


function extractVerdict(text) {
    const match = String(text || "").match(
        /\b(APPROVED WITH CAUTION|REJECTED|APPROVED)\b/i
    );

    return match ? match[1].toUpperCase() : null;
}


function extractHumanApproval(text) {
    const cleaned = String(text || "");

    const match = cleaned.match(
        /HUMAN APPROVAL(?: REQUIRED)?\s*:?\s*(YES|NO|REQUIRED|NOT REQUIRED|CONDITIONAL)/i
    );

    if (!match) {
        return null;
    }

    const value = match[1].toUpperCase();

    if (value === "YES" || value === "REQUIRED") {
        return "REQUIRED";
    }

    if (value === "NO" || value === "NOT REQUIRED") {
        return "NOT REQUIRED";
    }

    if (value === "CONDITIONAL") {
        return "CONDITIONAL";
    }

    return null;
}


function extractRecommendedAction(text) {
    let raw = String(text || "")
        .replace(/<br\s*\/?>/gi, "\n")
        .replace(/\r/g, "");

    const match = raw.match(
        /RECOMMENDED ACTION\s*:?\s*([\s\S]*?)(?=\n\s*(?:\d+\.\s*)?(?:REASON|HUMAN APPROVAL|NEXT WORKFLOW STEP|AUDIT SUMMARY)\b|$)/i
    );

    if (!match) {
        return null;
    }

    let action = match[1];

    // Remove markdown/table formatting.
    action = action
        .replace(/\|/g, " ")
        .replace(/[*_`]/g, "")
        .replace(/-{3,}/g, " ")
        .replace(/^\s*#\s*/gm, "")
        .trim();

    // Remove common generated workflow headers.
    action = action.replace(
        /^(?:Action\s*(?:\(to be automated\))?\s*)?/i,
        ""
    );

    action = action.replace(
        /^Conditions\s*\/\s*Notes\s*/i,
        ""
    );

    // Look for the first numbered workflow step.
    const numbered = action.match(
        /(?:^|\n)\s*1[\.\)]\s*(.+?)(?=\n\s*2[\.\)]|\n\s*\d+[\.\)]|$)/s
    );

    if (numbered) {
        action = numbered[1];
    }

    // Clean remaining table/header fragments.
    action = action
        .replace(/^(?:Step|Trigger\s*\/\s*Condition|Action)\s+/i, "")
        .replace(/\s+/g, " ")
        .trim();

    // Keep the summary short.
    if (action.length > 220) {
        action = action.substring(0, 217).trim();

        const lastSpace = action.lastIndexOf(" ");
        if (lastSpace > 150) {
            action = action.substring(0, lastSpace);
        }

        action += "...";
    }

    return action || null;
}


/* =========================
   AGENT CARD
========================= */

function createAgentCard(
    number,
    name,
    icon,
    content
) {

    let data;

    try {
        data = JSON.parse(content || "{}");
    } catch (error) {
        return `
            <div class="agent-card">

                <div class="agent-header">
                    <div class="agent-title">

                        <span class="agent-number">
                            ${number}
                        </span>

                        <span class="agent-icon">
                            ${icon}
                        </span>

                        <div>
                            <h3>${name}</h3>

                            <span class="agent-status">
                                COMPLETED
                            </span>
                        </div>

                    </div>

                    <span class="agent-check">
                        ✓
                    </span>
                </div>

                <div class="agent-content">
                    ${markdownToHTML(content)}
                </div>

            </div>
        `;
    }

    const labels = {
        event_type: "Event Type",
        what_happened: "What Happened",
        entities_involved: "Entities Involved",
        urgency: "Urgency",
        important_information: "Important Information",
        possible_business_impact: "Possible Business Impact",
        missing_information: "Missing Information",
        assumptions: "Assumptions",

        severity: "Severity",
        affected_areas: "Affected Areas",
        business_impact: "Business Impact",
        risk: "Risk",

        recommended_action: "Recommended Action",
        reasoning: "Reasoning",
        priority: "Priority",
        required_workflow: "Required Workflow",
        human_approval_required: "Human Approval",
        actions_must_not_be_taken: "Actions Not Allowed",

        decision_validity: "Decision Validity",
        safety_risks: "Safety Risks",
        unnecessary_actions: "Unnecessary Actions",
        authorization_concerns: "Authorization Concerns",
        final_verdict: "Final Verdict",

        final_status: "Final Status",
        event_summary: "Event Summary",
        reason: "Reason",
        human_approval: "Human Approval",
        next_workflow_step: "Next Workflow Step",
        audit_summary: "Audit Summary"
    };

    function formatValue(value) {

        if (Array.isArray(value)) {

            if (value.length === 0) {
                return "<span>None identified</span>";
            }

            return `
                <ul class="agent-list">
                    ${value.map(item => `
                        <li>${escapeHTML(item)}</li>
                    `).join("")}
                </ul>
            `;
        }

        if (typeof value === "boolean") {
            return escapeHTML(String(value));
        }

        return escapeHTML(String(value ?? "—"));
    }

    const fields = Object.entries(data)
        .map(([key, value]) => {

            if (value === null || value === undefined) {
                return "";
            }

            return `
                <div class="agent-field">

                    <div class="agent-field-label">
                        ${labels[key] || key.replace(/_/g, " ")}
                    </div>

                    <div class="agent-field-value">
                        ${formatValue(value)}
                    </div>

                </div>
            `;

        })
        .join("");

    return `
        <div class="agent-card">

            <div class="agent-header">

                <div class="agent-title">

                    <span class="agent-number">
                        ${number}
                    </span>

                    <span class="agent-icon">
                        ${icon}
                    </span>

                    <div>
                        <h3>${name}</h3>

                        <span class="agent-status">
                            COMPLETED
                        </span>
                    </div>

                </div>

                <span class="agent-check">
                    ✓
                </span>

            </div>

            <div class="agent-content">
                ${fields}
            </div>

        </div>
    `;
}


/* =========================
   MARKDOWN RENDERER
========================= */

function markdownToHTML(text) {
    let html = escapeHTML(text);

    // Remove literal HTML line-break tags produced by the model
    html = html.replace(/&lt;br\s*\/?&gt;/gi, "<br>");

    // Convert markdown tables into readable blocks
    const lines = html.split("<br>");
    let output = "";
    let inTable = false;

    for (let line of lines) {
        const trimmed = line.trim();

        // Skip table separator rows such as |------|------|
        if (/^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$/.test(trimmed)) {
            continue;
        }

        // Table row
        if (trimmed.includes("|")) {
            const cells = trimmed
                .replace(/^\|/, "")
                .replace(/\|$/, "")
                .split("|")
                .map(cell => cell.trim())
                .filter(cell => cell.length > 0);

            if (cells.length >= 2) {
                if (!inTable) {
                    output += '<div class="markdown-table">';
                    inTable = true;
                }

                output += `
                    <div class="markdown-table-row">
                        ${cells.map(cell => `<div class="markdown-table-cell">${cell}</div>`).join("")}
                    </div>
                `;

                continue;
            }
        }

        if (inTable) {
            output += "</div>";
            inTable = false;
        }

        if (trimmed === "") {
            output += "<br>";
        } else {
            output += line + "<br>";
        }
    }

    if (inTable) {
        output += "</div>";
    }

    html = output;

    // Headings
    html = html.replace(/^### (.*?)$/gm, "<h4>$1</h4>");
    html = html.replace(/^## (.*?)$/gm, "<h3>$1</h3>");
    html = html.replace(/^# (.*?)$/gm, "<h3>$1</h3>");

    // Bold and italic
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/__(.*?)__/g, "<strong>$1</strong>");
    html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");

    // Inline code
    html = html.replace(/`(.*?)`/g, "<code>$1</code>");

    // Bullet lists
    html = html.replace(
        /^\s*[-*]\s+(.*?)$/gm,
        "<li>$1</li>"
    );

    html = html.replace(
        /(<li>.*?<\/li>\s*)+/gs,
        "<ul>$&</ul>"
    );

    // Numbered lists
    html = html.replace(
        /^\s*\d+\.\s+(.*?)$/gm,
        "<li>$1</li>"
    );

    // Clean excessive line breaks
    html = html.replace(/(<br>\s*){3,}/g, "<br><br>");

    return html;
}


/* =========================
   HTML SAFETY
========================= */

function escapeHTML(text) {

    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}