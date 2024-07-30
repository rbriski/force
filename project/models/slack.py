from typing import Any, List

from pydantic import BaseModel


class Event(BaseModel):
    user: str
    type: str
    ts: str | None = None
    client_msg_id: str | None = None
    text: str | None = None
    team: str | None = None
    _blocks: List[Any] | None = None
    channel: str
    event_ts: str
    channel_type: str | None = None
    tab: str | None = None
    _view: Any | None = None


class Authorization(BaseModel):
    enterprise_id: Any
    team_id: str
    user_id: str
    is_bot: bool
    is_enterprise_install: bool


class Message(BaseModel):
    token: str | None = None
    team_id: str | None = None
    context_team_id: str | None = None
    context_enterprise_id: str | None = None
    api_app_id: str | None = None
    event: Event | None = None
    type: str | None = None
    event_id: str | None = None
    event_time: int | None = None
    authorizations: List[Authorization] | None = None
    is_ext_shared_channel: bool | None = None
    event_context: str | None = None
