from contextlib import contextmanager
from typing import Generator, List, Tuple
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from .handler import Handler
from .models import Player, Team, ShortEvent

DASH_URL = "https://go.teamsnap.com/team/dashboard"


class Teamsnap:
    def __init__(self, username: str, password: str) -> None:
        """
        Initialize the Teamsnap instance.

        Args:
        - username: User's email/username for Teamsnap.
        - password: User's password for Teamsnap.
        """
        self.username = username
        self.password = password

    @contextmanager
    def __init_ts(self) -> Generator[Handler, None, None]:
        """
        Context manager for initializing and cleaning up the web driver.

        Yields:
        - WebDriver: Initialized web driver.
        """
        try:
            handler = Handler(self.username, self.password)
            yield handler
        finally:
            handler.driver.quit()

    def parse_player_link(self, player_link: str) -> Tuple[int, int]:
        parsed = urlparse(player_link)

        team_id = int(parsed.path.split("/")[-1])
        roster_id = int(parse_qs(parsed.query)["roster_id"][0])

        return team_id, roster_id

    def teams(self) -> List[Team]:
        """
        Fetches the teams dashboard and extracts the team details.

        Returns:
        - List of Team objects.
        """
        teams: List[Team] = []

        with self.__init_ts() as ts:
            dash_html = ts.get_source(DASH_URL)
            soup = BeautifulSoup(dash_html, "html.parser")

            # Find the "Panel" div where it contains an "h3" tag with class
            # "Panel-title" and text "My Teams"
            my_teams_div = next(
                (
                    panel
                    for panel in soup.find_all("div", class_="Panel")
                    if panel.find("h3", class_="Panel-title", string="My Teams")
                ),
                None,
            )

            # If the correct "Panel" div is found, extract the data
            if my_teams_div:
                # Iterate through all the "Panel-row" divs within the "Panel" div
                for panel_row in my_teams_div.find_all("div", class_="Panel-row"):
                    team_name_tag = panel_row.find("b")

                    # Skip any rows without a team name
                    if not team_name_tag:
                        continue

                    # Extract team name
                    team_name = team_name_tag.get_text(strip=True)

                    # Extract player/link details
                    player_link = panel_row.find("a")
                    player_name = player_link.get_text(strip=True)
                    player_url = player_link["href"]

                    # Extract player's role/position
                    player_role = player_link.find_next_sibling("span").get_text(
                        strip=True
                    )

                    # Extract additional info, if available
                    additional_info = panel_row.find(
                        "div", class_="u-size1of3"
                    ).get_text(strip=True)

                    team_id, roster_id = self.parse_player_link(player_url)
                    teams.append(
                        Team(
                            id=team_id,
                            roster_id=roster_id,
                            team_name=team_name,
                            player_name=player_name,
                            player_link=player_url,
                            player_role=player_role,
                            additional_info=additional_info,
                        )
                    )

            return teams

    def roster(self, team_id: int) -> List[Player]:
        players = []

        with self.__init_ts() as ts:
            url = f"https://go.teamsnap.com/{team_id}/roster/list"
            team_html = ts.get_source(url, wait_for_xpath="//h1[text()='Roster']")

            soup = BeautifulSoup(team_html, "html.parser")
            root_div = soup.find("div", id="root")

            # Find all player rows inside the root div
            player_rows = root_div.select(".Panel-row.Panel-row--withCells")

            for row in player_rows:
                # Extract position
                position_element = row.select_one(".Panel-cell.u-size2of12")
                number_and_position = (
                    position_element.get_text(strip=True) if position_element else None
                )
                number_field = [x.strip() for x in number_and_position.split("-", 1)]
                number = number_field[0] if len(number_field) > 0 else None
                position = number_field[1] if len(number_field) > 1 else None

                # Extract name and associated link
                name_link = row.select_one(".Panel-cell.u-size3of12 a")
                if name_link:
                    name = name_link.get_text(strip=True)
                    link = name_link["href"]

                    # Extract image link
                    image_element = row.select_one(".Panel-cell.u-size1of8 img")
                    image_link = image_element["src"] if image_element else None

                    # Extract contact information
                    contacts = row.select(".Panel-cell.u-size5of12 .u-spaceEndsXs")
                    contact_details = []
                    for contact in contacts:
                        contact_name = (
                            contact.span.get_text(strip=True) if contact.span else None
                        )
                        email_element = contact.select_one('a[href^="mailto:"]')
                        email = (
                            email_element.get_text(strip=True)
                            if email_element
                            else None
                        )
                        relationship_element = contact.select_one("b")
                        relationship = (
                            relationship_element.get_text(strip=True)
                            if relationship_element
                            else None
                        )
                        contact_details.append(
                            {
                                "contact_name": contact_name,
                                "email": email,
                                "relationship": relationship,
                            }
                        )

                    players.append(
                        Player(
                            name=name,
                            link=link,
                            image=image_link,
                            number=number,
                            position=position,
                            contacts=contact_details,
                        )
                    )

            return players

    def schedule(self, team_id: int) -> List[ShortEvent]:
        url = f"https://go.teamsnap.com/{team_id}/schedule?mode=list&pageSize=30"
        events = []

        with self.__init_ts() as ts:
            schedule_html = ts.get_source(url, wait_for_xpath="//h1[text()='Schedule']")
            while (
                True
            ):  # Loop until there's no "Next" button or a stop condition is met
                soup = BeautifulSoup(schedule_html, "html.parser")
                root_div = soup.find("div", id="root")

                # Find all schedule rows inside the root div
                schedule_rows = root_div.select(".Panel-row.Panel-row--withCells")
                for row in schedule_rows:
                    event_cell = row.find(
                        "a", {"class": "u-textSemiBold u-spaceRightXs"}
                    )
                    if not event_cell:
                        continue

                    event_text = event_cell.span.text
                    event_link = row.find(
                        "a", {"class": "u-textSemiBold u-spaceRightXs"}
                    )["href"]
                    number = int(event_link.split("/")[-1])
                    event = ShortEvent(id=number, name=event_text, link=event_link)
                    events.append(event)

                # Break if the next button is disabled
                try:
                    next_button = ts.driver.find_element(
                        By.XPATH,
                        "//button[contains(@class, 'Button PaginateItemIsDisabled') and .//span[text()='Next']]",
                    )
                    break
                except (
                    NoSuchElementException
                ):  # Keep going if "Next" button is not disabled
                    pass

                # Navigate to the next page if "Next" button exists
                try:
                    next_button = ts.driver.find_element(
                        By.XPATH,
                        "//button[contains(@class, 'Button PaginateItem') and .//span[text()='Next']]",
                    )
                    next_button.click()
                    schedule_html = ts.driver.page_source
                except (
                    NoSuchElementException
                ):  # Exit loop if "Next" button is not found
                    break

        return events

    def event(self, link: str) -> List[Player] | None:
        with self.__init_ts() as ts:
            url = f"https://go.teamsnap.com/{link}"
            event_html = ts.get_source(url, wait_for_xpath="//div[text()='Date/Time']")

            soup = BeautifulSoup(event_html, "html.parser")
            table = soup.find("div", {"id": "root"})

            # soup = BeautifulSoup(event_html, "html.parser")

            # Extracting Date and Time
            date_time_div = table.select_one(
                '.Panel-cell:contains("Date/Time:") + .Panel-cell'
            )
            date_time = " ".join(
                [span.get_text() for span in date_time_div.find_all("span")]
            )
            arrival_time = date_time_div.select_one("small").get_text()

            # Extracting Location
            location_div = table.select_one(
                '.Panel-cell:contains("Location:") + .Panel-cell'
            )
            location = location_div.a.get_text()

            # Extracting Address
            address_div = table.select_one(
                '.Panel-cell:contains("Address:") + .Panel-cell'
            )
            address = " ".join(
                [span.get_text() for span in address_div.find_all("span")]
            )

            # Extracting players' information
            # players_div = table.select(".Panel-row.Panel-row--withCells")
            # players = []
            # for player_div in players_div:
            #     number = player_div.select_one(".Panel-cell.u-size1of4 span").get_text()
            #     name = player_div.select_one(".Panel-cell.u-size3of4 span").get_text()
            #     order = player_div.select_one(
            #         '.Panel-cell.u-size1of4[style*="rgb(122, 122, 122)"] span'
            #     ).get_text()
            #     players.append({"Number": number, "Name": name, "Order": order})

            print(f"Date and Time: {date_time}")
            print(f"Arrival Time: {arrival_time}")
            print(f"Location: {location}")
            print(f"Address: {address}")
            # print("Players:")
            # for player in players:
            #     print(
            #         f"Number: {player['Number']}, Name: {player['Name']}, Order: {player['Order']}"
            #     )
