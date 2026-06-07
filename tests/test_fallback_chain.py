from types import SimpleNamespace

from src.agents import LearnerProfilerAgent
from src.ai_cache import build_ai_call_cache_key, delete_cached_ai_call
from src.config import AZURE_AI_MODEL_DEPLOYMENT
from src.iq_integration import FabricIQ, WorkIQ
from src.profile_cache import build_profile_cache_key, delete_cached_profile


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


class _FailingCompletions:
    def create(self, **kwargs):
        raise AssertionError("AI provider should not be called when the AI call cache is warm")


class _FailingAzureOpenAIClient:
    chat = SimpleNamespace(completions=_FailingCompletions())


def test_tier2_azure_openai_json_mode_can_profile(monkeypatch):
    import src.agents as agents_module

    def fake_azure_openai(**kwargs):
        return _FakeAzureOpenAIClient()

    monkeypatch.setattr(agents_module, "FORCE_MOCK_MODE", False)
    monkeypatch.setattr(agents_module, "AZURE_AI_PROJECT_ENDPOINT", "")
    monkeypatch.setattr(agents_module, "AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setattr(agents_module, "AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(agents_module, "AzureOpenAI", fake_azure_openai)

    work_iq = WorkIQ()
    cache_key = build_profile_cache_key(
        mode="live",
        model=agents_module.AZURE_AI_MODEL_DEPLOYMENT,
        employee_id="EMP-999",
        target_certification="AZ-900",
        text_input="I am a founder preparing for AZ-900.",
        work_signals=work_iq.get_signals_by_employee("EMP-999"),
    )
    delete_cached_profile(cache_key)

    agent = LearnerProfilerAgent()
    profile = agent.execute(
        "I am a founder preparing for AZ-900.",
        "EMP-999",
        work_iq,
        FabricIQ(),
    )

    assert profile.learner_id == "L-FAKE"
    assert profile.name == "Cloud Tester"
    assert profile.certification_target == "AZ-900"
    assert any("Tier 2: Successfully profiled" in trace for trace in agent.get_traces())


def test_chat_json_ai_call_results_are_cached():
    agent = LearnerProfilerAgent()
    work_signals = WorkIQ().get_signals_by_employee("EMP-998")
    request_payload = {
        "messages": agent._profile_schema_prompt(
            "I am a founder preparing for AZ-900.",
            "EMP-998",
            "AZ-900",
            work_signals,
        ),
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 500,
    }
    cache_key = build_ai_call_cache_key(
        call_type="chat_json",
        model=AZURE_AI_MODEL_DEPLOYMENT,
        request_payload=request_payload,
    )
    delete_cached_ai_call(cache_key)

    first = agent._call_chat_json(
        _FakeAzureOpenAIClient(),
        "I am a founder preparing for AZ-900.",
        "EMP-998",
        "AZ-900",
        work_signals,
    )
    second = agent._call_chat_json(
        _FailingAzureOpenAIClient(),
        "I am a founder preparing for AZ-900.",
        "EMP-998",
        "AZ-900",
        work_signals,
    )

    assert first == second
    assert any("AI call cache hit" in trace for trace in agent.get_traces())
