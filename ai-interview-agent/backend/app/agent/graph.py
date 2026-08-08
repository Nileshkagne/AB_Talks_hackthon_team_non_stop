from langgraph.graph import END, StateGraph
from app.agent.state import InterviewState
from app.agent import nodes


def build_start_graph():
    builder = StateGraph(InterviewState)
    builder.add_node("load_or_create_session", nodes.load_or_create_session)
    builder.add_node("build_profile", nodes.build_profile)
    builder.add_node("select_topic", nodes.select_topic)
    builder.add_node("generate_question", nodes.generate_question)
    builder.add_node("persist_state", nodes.persist_state)

    builder.set_entry_point("load_or_create_session")
    builder.add_edge("load_or_create_session", "build_profile")
    builder.add_edge("build_profile", "select_topic")
    builder.add_edge("select_topic", "generate_question")
    builder.add_edge("generate_question", "persist_state")
    builder.add_edge("persist_state", END)

    return builder.compile()


def build_continue_graph():
    builder = StateGraph(InterviewState)
    builder.add_node("load_session", nodes.load_session)
    builder.add_node("save_candidate_answer", nodes.save_candidate_answer)
    builder.add_node("evaluate_answer", nodes.evaluate_answer)
    builder.add_node("update_state", nodes.update_state)
    builder.add_node("generate_question", nodes.generate_question)
    builder.add_node("generate_feedback", nodes.generate_feedback)
    builder.add_node("persist_state", nodes.persist_state)
    builder.add_node("persist_feedback", nodes.persist_feedback)

    builder.set_entry_point("load_session")
    builder.add_edge("load_session", "save_candidate_answer")
    builder.add_edge("save_candidate_answer", "evaluate_answer")
    builder.add_edge("evaluate_answer", "update_state")

    builder.add_conditional_edges(
        "update_state",
        nodes.decide_next_action,
        {
            "follow_up": "generate_question",
            "new_topic": "generate_question",
            "finish": "generate_feedback",
        },
    )

    builder.add_edge("generate_question", "persist_state")
    builder.add_edge("persist_state", END)

    builder.add_edge("generate_feedback", "persist_feedback")
    builder.add_edge("persist_feedback", END)

    return builder.compile()


start_graph = build_start_graph()
continue_graph = build_continue_graph()
