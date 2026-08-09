from app.state.state import EnterpriseState


def report_generator(state: EnterpriseState):
    findings = state.get("findings", [])
    confidence = state.get("confidence", 0.0)

    if not findings:
        report = (
            "No sufficient evidence was collected to generate "
            "an operational report."
        )
    else:
        report_lines = [
            "Enterprise AI Operations Report",
            "",
            "Summary:",
            "The workflow collected evidence from the required enterprise sources.",
            "",
            "Findings:",
        ]

        for index, finding in enumerate(findings, start=1):
            report_lines.append(f"{index}. {finding}")

        report_lines.extend(
            [
                "",
                f"Confidence: {confidence:.2f}",
                "",
                "Status: Report generated successfully.",
            ]
        )

        report = "\n".join(report_lines)

    return {
        "report": report,
        "status": "report_generated",
    }