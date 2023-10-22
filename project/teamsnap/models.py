from pydantic import BaseModel


class Team(BaseModel):
    id: int
    roster_id: int
    team_name: str
    player_name: str
    player_link: str
    player_role: str
    additional_info: str


class Contact(BaseModel):
    contact_name: str | None = None
    email: str | None = None
    relationship: str | None = None


class Player(BaseModel):
    name: str
    link: str | None = None
    image: str | None = None
    number: str | None = None
    position: str | None = None
    contacts: list[Contact] | None = None


class ShortEvent(BaseModel):
    id: int
    name: str
    link: str


class EventTime(BaseModel):
    datetime: str
    arrival_time: str | None = None


class Event(BaseModel):
    date_time: EventTime
    location: str | None = None
    location_details: str | None = None
    opponent: str | None = None
    home_or_away: str | None = None
    uniform: str | None = None
    address: str | None = None
    link: str | None = None
    notes: str | None = None
    availability: list[Player] | None = None
    result: str | None = None
