"""Offline component tests for the real session command handler.

NoneBot transport, permission checks and persistence are replaced at the boundary.
No bot initialization, live model, QQ connection or database is used.
"""

import asyncio
import importlib.util
import sys
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


class Finish(Exception):
    pass


class Skip(Exception):
    pass


class Matcher:
    def __init__(self):
        self.messages = []

    async def finish(self, text):
        self.messages.append(text)
        raise Finish

    async def send(self, text):
        self.messages.append(text)

    def skip(self):
        raise Skip


@dataclass
class Memory:
    messages: list = field(default_factory=list)
    time: float = 0.0


@dataclass
class State:
    memory: Memory = field(default_factory=Memory)
    sessions: list = field(default_factory=list)
    timestamp: float = 1.0
    saves: int = 0
    save_error: Exception | None = None

    async def save(self, event):
        if self.save_error:
            raise self.save_error
        self.saves += 1


def message(content):
    return SimpleNamespace(content=content)


@pytest.fixture
def handler(monkeypatch):
    """Load the complete production module without plugin startup side effects."""
    state = State()
    control = SimpleNamespace(allowed=True, enabled=True, reads=0)

    async def allowed(event, bot):
        return control.allowed

    async def load(event):
        control.reads += 1
        return state

    def module(name, **attrs):
        result = ModuleType(name)
        result.__dict__.update(attrs)
        monkeypatch.setitem(sys.modules, name, result)
        return result

    for name in (
        "nonebot",
        "nonebot.adapters",
        "nonebot.adapters.onebot",
        "miniagent_session_test",
        "miniagent_session_test.handlers",
        "miniagent_session_test.utils",
    ):
        module(name, __path__=[])
    module(
        "nonebot.adapters.onebot.v11", Bot=object, Message=object, MessageEvent=object
    )
    module("nonebot.exception", NoneBotException=Finish)
    module("nonebot.matcher", Matcher=Matcher)
    module("nonebot.params", CommandArg=lambda: None)
    module("miniagent_session_test.check_rule", is_group_admin_if_is_in_group=allowed)
    config = SimpleNamespace(session=SimpleNamespace(session_control=True))
    module(
        "miniagent_session_test.config", config_manager=SimpleNamespace(config=config)
    )
    module(
        "miniagent_session_test.utils.memory",
        Memory=Memory,
        MemoryModel=State,
        get_memory_data=load,
    )
    path = Path(__file__).parents[1] / "amrita/plugins/chat/handlers/sessions.py"
    spec = importlib.util.spec_from_file_location(
        "miniagent_session_test.handlers.sessions", path
    )
    target = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)

    def run(command):
        config.session.session_control = control.enabled
        matcher = Matcher()
        args = SimpleNamespace(extract_plain_text=lambda: command)
        try:
            asyncio.run(target.sessions(object(), object(), matcher, args))
        except (Finish, Skip):
            pass
        return matcher.messages

    return state, control, run


@pytest.mark.parametrize("operation", ["set", "del"])
@pytest.mark.parametrize(
    "argument", ["", "-1", "2", "nope", "1.0", "0 extra", "9" * 5000]
)
def test_invalid_index_does_not_change_or_save_history(handler, operation, argument):
    state, _, run = handler
    state.memory = Memory([message("current")])
    state.sessions = [Memory([message("first")]), Memory([message("second")])]
    before = deepcopy(state)
    replies = run(f"{operation} {argument}")
    assert state == before
    assert replies == ["请输入正确编号"]


@pytest.mark.parametrize("operation", ["set", "del"])
def test_empty_history_rejects_index(handler, operation):
    state, _, run = handler
    assert run(f"{operation} 0") == ["请输入正确编号"]
    assert state.saves == 0


def test_delete_uses_position_even_when_sessions_compare_equal(handler):
    state, _, run = handler
    first = Memory([message("same")], time=12)
    second = deepcopy(first)
    state.sessions = [first, second]
    run("del 1")
    assert len(state.sessions) == 1
    assert state.sessions[0] is first
    assert state.saves == 1


def test_restore_copies_messages_without_mutating_archive(handler):
    state, _, run = handler
    archived = Memory([message([SimpleNamespace(type="text", text="hello")])])
    state.sessions = [archived]
    assert run("set 0") == ["完成记忆覆盖。"]
    assert state.memory.messages == archived.messages
    assert state.memory.messages is not archived.messages
    state.memory.messages[0].content[0].text = "changed"
    assert archived.messages[0].content[0].text == "hello"
    assert state.saves == 1
    assert state.timestamp > 1


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("short text", "short text"),
        ("hello\nworld", "hello world"),
        (None, "[工具调用]"),
        (
            [SimpleNamespace(type="image_url", image_url="private-image-url")],
            "[多模态消息]",
        ),
        (
            [
                SimpleNamespace(type="text", text="中文预览"),
                SimpleNamespace(type="image_url", image_url="private-image-url"),
            ],
            "中文预览",
        ),
    ],
)
def test_list_displays_text_multimodal_and_tool_messages(handler, content, expected):
    state, _, run = handler
    state.sessions = [Memory([message(content)])]
    replies = run("")
    assert expected in replies[0]
    assert "编号：0" in replies[0]
    assert "private-image-url" not in replies[0]
    assert state.saves == 0


def test_list_includes_empty_archives_and_bounds_preview(handler):
    state, _, run = handler
    state.sessions = [Memory(), Memory([message("x" * 1000)])]
    reply = run("")[0]
    assert "编号：0" in reply
    assert "[空会话]" in reply
    assert "编号：1" in reply
    assert "x" * 48 + "..." in reply
    assert "x" * 49 not in reply


def test_no_history_finishes_without_dispatch(handler):
    assert handler[2]("") == ["没有历史会话"]


def test_archive_then_restore_preserves_nested_contents(handler):
    state, _, run = handler
    state.memory.messages = [message([SimpleNamespace(type="text", text="hello")])]
    assert run("archive") == ["当前会话已归档。"]
    assert state.memory.messages == []
    assert len(state.sessions) == 1
    run("set 0")
    assert state.memory.messages[0].content[0].text == "hello"
    assert state.saves == 2


def test_empty_archive_does_not_save(handler):
    assert handler[2]("archive") == ["当前对话为空！"]
    assert handler[0].saves == 0


def test_clear_leaves_current_conversation_intact(handler):
    state, _, run = handler
    state.memory.messages = [message("current")]
    state.sessions = [Memory([message("archive")])]
    assert run("clear") == ["会话已清空。"]
    assert state.sessions == []
    assert state.memory.messages[0].content == "current"
    assert state.saves == 1


@pytest.mark.parametrize(("allowed", "enabled"), [(False, True), (True, False)])
def test_permission_and_disabled_guards_do_not_load_or_save(handler, allowed, enabled):
    state, control, run = handler
    control.allowed = allowed
    control.enabled = enabled
    run("clear")
    assert control.reads == 0
    assert state.saves == 0


@pytest.mark.parametrize(
    ("command", "expected"),
    [("set 0", "覆盖记忆文件失败"), ("del 0", "删除指定编号会话失败")],
)
def test_save_errors_are_reported(handler, command, expected):
    state, _, run = handler
    state.sessions = [Memory([message("archive")])]
    state.save_error = OSError("offline fixture")
    assert expected in run(command)[0]
    assert state.saves == 0
