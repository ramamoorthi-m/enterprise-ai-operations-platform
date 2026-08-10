from app.workflow.graph import graph


def test_graph_planner_integration():

    initial_state = {
        "user_query": "Analyze the current project status and identify potential delivery blockers."
    }

    result = graph.invoke(initial_state)

    print("\nFinal graph state:")
    print(result)

    assert result["plan"]
    assert result["required_sources"]
    assert result["status"] == "report_generated"