from telemetry import langfuse_tracing as tracing


def test_build_callbacks_disabled() -> None:
    from config import Settings

    settings = Settings(enable_langfuse=False)
    assert (
        tracing.build_langfuse_callbacks(
            settings,
            session_id="s",
            user_id="u",
            request_id="r",
            prompt_name="relay/system",
            prompt_version=1,
            roles="admin",
        )
        == []
    )


def test_log_tool_span_noop_without_client(monkeypatch) -> None:
    monkeypatch.setattr(tracing, "get_langfuse_client", lambda settings=None: None)
    tracing.log_tool_span(
        request_id="r1",
        tool_name="get_open_issues",
        arguments={"customer_name": "VaultLedger"},
        result={"ok": True},
        latency_ms=12,
        user_sub="bob",
        roles=["support_user"],
    )


def test_finalize_run_noop_without_client(monkeypatch) -> None:
    monkeypatch.setattr(tracing, "get_langfuse_client", lambda settings=None: None)
    tracing.finalize_agent_run_trace(
        request_id="r1",
        query="q",
        answer="a",
        tools_used=["get_open_issues"],
        latency_ms=10,
        prompt_name="relay/system",
        prompt_version=1,
        user_sub="bob",
        session_id="s",
        roles=["support_user"],
        pending_approvals=0,
    )
