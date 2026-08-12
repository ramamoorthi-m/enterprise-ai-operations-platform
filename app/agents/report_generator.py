from app.state.state import EnterpriseState


class ReportGeneratorAgent:

    def generate(self, state: EnterpriseState):

        project = state.get("project", "Unknown Project")
        user_query = state.get("user_query", "")

        analysis = state.get("analysis", {})
        findings = state.get("findings", [])

        summary = analysis.get(
            "summary",
            "No summary was available."
        )

        key_findings = analysis.get("key_findings") or findings

        risks = analysis.get(
            "risks",
            []
        )

        evidence_gaps = analysis.get(
            "evidence_gaps",
            []
        )

        confidence = analysis.get(
            "confidence",
            state.get("confidence", 0.0)
        )

        report_lines = [
            f"# Enterprise Project Investigation Report",
            "",
            f"Project: {project}",
            "",
            "## Investigation Request",
            user_query,
            "",
            "## Executive Summary",
            summary,
            "",
            "## Key Findings",
        ]

        if key_findings:
            for finding in key_findings:
                report_lines.append(f"- {finding}")
        else:
            report_lines.append("- No significant findings were identified.")

        report_lines.extend([
            "",
            "## Risks",
        ])

        if risks:
            for risk in risks:
                report_lines.append(f"- {risk}")
        else:
            report_lines.append("- No significant risks were identified.")

        report_lines.extend([
            "",
            "## Evidence Gaps",
        ])

        if evidence_gaps:
            for gap in evidence_gaps:
                report_lines.append(f"- {gap}")
        else:
            report_lines.append("- No significant evidence gaps were identified.")

        report_lines.extend([
            "",
            "## Confidence",
            f"{confidence:.2f}",
        ])

        report = "\n".join(report_lines)

        return {
            "report": report,
            "status": "report_generated",
        }