import json
import os

import requests
import streamlit as st


# ============================================================
# Configuration
# ============================================================

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

INVESTIGATE_URL = f"{API_BASE_URL}/api/v1/investigate"
RESUME_URL = f"{API_BASE_URL}/api/v1/investigate/resume"

st.set_page_config(
    page_title="Enterprise AI Operations Platform",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Session state
# ============================================================

if "investigation_result" not in st.session_state:
    st.session_state["investigation_result"] = None

if "api_error" not in st.session_state:
    st.session_state["api_error"] = None


# ============================================================
# API helpers
# ============================================================

def save_api_error(message: str) -> None:
    st.session_state["api_error"] = message


def clear_api_error() -> None:
    st.session_state["api_error"] = None


def response_error(response: requests.Response) -> str:
    """Extract a useful error message from an HTTP response."""
    try:
        body = response.json()

        if isinstance(body, dict):
            detail = body.get("detail", body)
        else:
            detail = body

        return f"HTTP {response.status_code}: {detail}"

    except (ValueError, TypeError):
        return f"HTTP {response.status_code}: {response.text}"


def start_investigation(query: str, project: str) -> None:
    """Start an investigation using the existing FastAPI endpoint."""
    payload = {
        "query": query.strip(),
        "project": project.strip() or None,
    }

    st.session_state["investigation_result"] = None
    clear_api_error()

    try:
        with st.spinner(
            "Investigating Jira, GitHub, and available evidence..."
        ):
            response = requests.post(
                INVESTIGATE_URL,
                json=payload,
                timeout=300,
            )

        if response.status_code == 200:
            st.session_state["investigation_result"] = response.json()
        else:
            save_api_error(response_error(response))

    except requests.exceptions.Timeout:
        save_api_error(
            "The request timed out. Check the FastAPI terminal and "
            "workflow state before submitting another investigation."
        )

    except requests.exceptions.ConnectionError:
        save_api_error(
            "Cannot connect to FastAPI. Start the backend at "
            f"{API_BASE_URL}."
        )

    except requests.exceptions.RequestException as exc:
        save_api_error(f"Request failed: {exc}")

    except ValueError:
        save_api_error("FastAPI returned invalid JSON.")


def resume_investigation(decision: str) -> None:
    """Resume an investigation paused for human review."""
    result = st.session_state.get("investigation_result") or {}
    thread_id = result.get("thread_id")

    if not thread_id:
        save_api_error(
            "Cannot resume this investigation because its thread ID is missing."
        )
        return

    clear_api_error()

    try:
        with st.spinner(
            "Resuming the workflow. This may take a while..."
        ):
            response = requests.post(
                RESUME_URL,
                json={
                    "thread_id": thread_id,
                    "decision": decision,
                },
                timeout=300,
            )

        if response.status_code == 200:
            st.session_state["investigation_result"] = response.json()
        else:
            save_api_error(response_error(response))

    except requests.exceptions.Timeout:
        save_api_error(
            "The resume request timed out. Check the backend state "
            "before submitting the decision again."
        )

    except requests.exceptions.ConnectionError:
        save_api_error("Cannot connect to the FastAPI backend.")

    except requests.exceptions.RequestException as exc:
        save_api_error(f"Resume request failed: {exc}")

    except ValueError:
        save_api_error("FastAPI returned invalid JSON.")


# ============================================================
# Formatting helpers
# ============================================================

def display_value(value) -> str:
    """Format values for readable display."""
    if value is None:
        return "Not available"

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, ensure_ascii=False)

    return str(value)


def display_items(items, empty_message: str) -> None:
    """Render a list of findings, risks, or evidence gaps."""
    if not items:
        st.caption(empty_message)
        return

    if isinstance(items, str):
        st.write(items)
        return

    if not isinstance(items, list):
        st.write(display_value(items))
        return

    for item in items:
        if isinstance(item, dict):
            title = (
                item.get("title")
                or item.get("name")
                or item.get("description")
                or "Finding"
            )
            details = item.get("description") or item.get("details")

            st.markdown(f"- **{title}**")
            if details and details != title:
                st.caption(str(details))
        else:
            st.markdown(f"- {item}")


def confidence_text(value) -> str:
    """Format confidence without assuming every value is a fraction."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if 0 <= value <= 1:
            return f"{value:.0%}"

        return f"{value:g}%"

    return "Not available"


def find_metric_value(findings: list, *keywords: str):
    """Find a matching evidence statement without inventing a metric."""
    for finding in findings:
        if not isinstance(finding, str):
            continue

        lowered = finding.lower()

        if all(keyword in lowered for keyword in keywords):
            return finding

    return None


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    st.title("AI Operations")
    st.caption("Enterprise investigation workspace")

    st.divider()

    st.markdown("**Capabilities**")
    st.markdown("- Jira investigation")
    st.markdown("- GitHub evidence collection")
    st.markdown("- AI-powered analysis")
    st.markdown("- Evaluation and human review")

    st.divider()

    if st.button("Clear displayed results", use_container_width=True):
        st.session_state["investigation_result"] = None
        clear_api_error()
        st.rerun()

    st.caption("Backend API: {API_BASE_URL}")


# ============================================================
# Header
# ============================================================

st.title("Enterprise AI Operations Platform")
st.write(
    "Investigate project delays, identify risks, and generate "
    "evidence-based operational reports."
)

st.divider()


# ============================================================
# Investigation form
# ============================================================

st.subheader("New investigation")

with st.form("investigation_form"):
    project = st.text_input(
        "Jira project key",
        value="SCRUM",
        help="The project to investigate.",
    )

    query = st.text_area(
        "Investigation question",
        placeholder=(
            "Why is the current project delayed? "
            "Investigate overdue Jira tasks and recent GitHub activity."
        ),
        height=120,
    )

    submitted = st.form_submit_button(
        "Start investigation",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if len(query.strip()) < 3:
        st.warning("Enter a question containing at least 3 characters.")
    elif len(query.strip()) > 2000:
        st.warning("The question cannot exceed 2000 characters.")
    elif project.strip() and len(project.strip()) > 100:
        st.warning("The project key cannot exceed 100 characters.")
    else:
        start_investigation(query, project)
        st.rerun()


# ============================================================
# API errors
# ============================================================

api_error = st.session_state.get("api_error")

if api_error:
    st.error(api_error)


# ============================================================
# Results dashboard
# ============================================================

result = st.session_state.get("investigation_result")

if not result:
    st.divider()
    st.subheader("Investigation workspace")
    st.info(
        "Start an investigation to view its evidence, analysis, "
        "evaluation, and final report."
    )

else:
    analysis = result.get("analysis") or {}

    if not isinstance(analysis, dict):
        analysis = {"summary": str(analysis)}

    findings = analysis.get("key_findings") or []
    if not isinstance(findings, list):
        findings = [findings]

    status = result.get("status", "unknown")
    passed = result.get("evaluation_passed")
    api_confidence = result.get("confidence")
    analysis_confidence = analysis.get("confidence")

    awaiting_review = (
        status == "awaiting_human_review"
        or result.get("human_review_required", False)
    )

    st.divider()
    st.subheader("Investigation overview")

    st.caption(
        f"Thread ID: {result.get('thread_id', 'Not available')}"
    )

    metric1, metric2, metric3 = st.columns(3)

    with metric1:
        st.metric(
            "Workflow status",
            status.replace("_", " ").title(),
        )

    with metric2:
        if passed is True:
            evaluation_label = "Passed"
        elif passed is False:
            evaluation_label = "Not passed"
        else:
            evaluation_label = "Pending"

        st.metric("Evaluation", evaluation_label)

    with metric3:
        st.metric(
            "API confidence",
            confidence_text(api_confidence),
        )

    if analysis_confidence is not None:
        st.caption(
            "Analysis confidence: "
            f"{confidence_text(analysis_confidence)}. "
            "This is shown separately from API confidence."
        )

    # --------------------------------------------------------
    # Human review
    # --------------------------------------------------------

    if awaiting_review:
        st.warning(
            result.get("human_review_reason")
            or "This investigation requires human review."
        )

        review_payload = result.get("review_payload") or {}

        if review_payload:
            with st.expander("Review context", expanded=True):
                st.json(review_payload)

        st.markdown("#### Human decision")

        st.write(
            "Approve to continue the workflow, or request a retry "
            "according to the workflow's existing retry policy."
        )

        approve_col, retry_col = st.columns(2)

        with approve_col:
            if st.button(
                "Approve investigation",
                type="primary",
                use_container_width=True,
                key="approve_investigation",
            ):
                resume_investigation("approve")
                st.rerun()

        with retry_col:
            if st.button(
                "Request retry",
                use_container_width=True,
                key="retry_investigation",
            ):
                resume_investigation("retry")
                st.rerun()

    # --------------------------------------------------------
    # Evidence metrics
    # --------------------------------------------------------

    st.divider()
    st.subheader("Evidence collected")

    overdue = find_metric_value(findings, "overdue", "jira")
    blocked = find_metric_value(findings, "blocked", "jira")
    open_issues = find_metric_value(findings, "open", "github", "issue")
    deployment = find_metric_value(findings, "workflow", "github")

    evidence_cols = st.columns(4)

    evidence_items = [
        ("Overdue tasks", overdue),
        ("Blocked tasks", blocked),
        ("Open GitHub issues", open_issues),
        ("CI/CD activity", deployment),
    ]

    for column, (label, value) in zip(evidence_cols, evidence_items):
        with column:
            if value is None:
                st.metric(label, "N/A")
            elif label == "CI/CD activity":
                if "no workflow runs" in value.lower():
                    st.metric(label, "No runs found")
                else:
                    st.metric(label, "Evidence found")
                with st.expander("Details"):
                    st.write(value)
            else:
                # Show the complete evidence statement instead of
                # guessing a number from arbitrary text.
                with st.container(border=True):
                    st.caption(label)
                    st.write(value)

    # --------------------------------------------------------
    # Analysis
    # --------------------------------------------------------

    st.divider()
    st.subheader("AI analysis")

    summary = analysis.get("summary")

    if summary:
        st.markdown("#### Executive summary")
        st.write(summary)

    assessment = analysis.get("assessment")

    if assessment:
        st.markdown("#### Assessment")
        st.write(assessment)

    findings_tab, risks_tab, gaps_tab = st.tabs(
        ["Key findings", "Risks", "Evidence gaps"]
    )

    with findings_tab:
        display_items(
            findings,
            "No key findings were returned.",
        )

    with risks_tab:
        display_items(
            analysis.get("risks"),
            "No risks were returned.",
        )

    with gaps_tab:
        display_items(
            analysis.get("evidence_gaps"),
            "No evidence gaps were returned.",
        )

    # --------------------------------------------------------
    # Investigation plan
    # --------------------------------------------------------

    plan = result.get("plan") or []

    st.divider()
    st.subheader("Investigation plan")

    if isinstance(plan, list) and plan:
        for index, step in enumerate(plan, start=1):
            if isinstance(step, dict):
                description = step.get(
                    "description",
                    "No description provided.",
                )
                source = step.get("source", "unspecified")

                with st.container(border=True):
                    st.markdown(f"**Step {index}: {source.title()}**")
                    st.write(description)
            else:
                st.markdown(f"{index}. {step}")
    elif plan:
        st.json(plan)
    else:
        st.caption("No investigation plan was returned.")

    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    st.divider()
    st.subheader("Final investigation report")

    final_report = result.get("final_report")

    if final_report:
        st.markdown(final_report)

        st.download_button(
            label="Download report",
            data=final_report,
            file_name="investigation_report.md",
            mime="text/markdown",
        )
    elif awaiting_review:
        st.info("The final report is pending human review.")
    else:
        st.info("No final report was returned.")

    # --------------------------------------------------------
    # Errors and technical details
    # --------------------------------------------------------

    errors = result.get("errors") or []

    if errors:
        st.divider()
        st.subheader("Workflow warnings and errors")
        display_items(errors, "No workflow errors were returned.")

    with st.expander("Technical details"):
        st.json(result)