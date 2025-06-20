from qtrax_sdk.models.agent import Agent

def test_agent_defaults():
    a = Agent(agent_id=1, start_node=10, goal_node=42) # type: ignore
    assert a.route == [10]
    assert a.current_node == 10
    assert a.status == "idle"