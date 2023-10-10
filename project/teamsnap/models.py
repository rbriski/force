from pydantic import BaseModel
from typing import List


class Team(BaseModel):
    id: int
    roster_id: int
    team_name: str
    player_name: str
    player_link: str
    player_role: str
    additional_info: str


class Contact(BaseModel):
    contact_name: str | None
    email: str | None
    relationship: str | None


class Player(BaseModel):
    name: str
    link: str | None
    image: str | None
    number: str | None
    position: str | None
    contacts: List[Contact] | None


class ShortEvent(BaseModel):
    id: int
    name: str
    link: str
