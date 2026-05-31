from types import SimpleNamespace

from src.agents import LearnerProfilerAgent
from src.iq_integration import FabricIQ, WorkIQ


class _FakeCompletions:
    def create(self, **kwargs):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=(
                            '{"learner_id":"L-FAKE","name":"Cloud Tester","role":"Founder",'
                            '"practice_score_avg":72,"hours_studied":11,'
                            '"exam_outcome":"None","status":"IN PROGRESS"}'
                        )
                    )
                )
            ]
        )


class _FakeAzureOpenAIClient:
    chat = SimpleNamespace(completions=_FakeCompletions())


def test_tier2_azure_openai_json_mode_can_profile(monkeypatch):
    import src.agents as agents_module

    def fake_azure_openai(**kwargs):
        return _FakeAzureOpenAIClient()

    monkeypatch.setattr(agents_module, "FORCE_MOCK_MODE", False)
    monkeypatch.setattr(agents_module, "AZURE_AI_PROJECT_ENDPOINT", "")
    monkeypatch.setattr(agents_module, "AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setattr(agents_module, "AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(agents_module, "AzureOpenAI", fake_azure_openai)

    agent = LearnerProfilerAgent()
    profile = agent.execute(
        "I am a founder preparing for AZ-900.",
        "EMP-999",
        WorkIQ(),
        FabricIQ(),
    )

    assert profile.learner_id == "L-FAKE"
    assert profile.name == "Cloud Tester"
    assert profile.certification_target == "AZ-900"
    assert any("Tier 2: Successfully profiled" in trace for trace in agent.get_traces())
