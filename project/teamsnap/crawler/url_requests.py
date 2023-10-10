import requests
from bs4 import BeautifulSoup

# # Initialize a session to keep cookies
# session = requests.Session()

# # URL of the page where the login form resides
# login_url = "https://go.teamsnap.com/login/signin"

# # First, get the login page to extract the authenticity_token
# response = session.get(login_url)
# soup = BeautifulSoup(response.text, "html.parser")

# # Extract the authenticity_token value
# authenticity_token = soup.find("input", {"name": "authenticity_token"})["value"]
# print(authenticity_token)

# # Collecting form data
# form_data = {
#     "authenticity_token": "cJiFMTYFn7RF43T/S1UxzPongus2DOziHh3Xu5+TYDo=",  # This might be dynamic; you might need to retrieve it from the page source
#     "login": "rbriski@gmail.com",
#     "password": "2cd9Zs6pWLur&i2t[QjWB)Vg",
#     "keep_logged_in": "1",  # Optional; only if you want the "Keep me logged in" option
#     "submit": "Log In",
# }

# # Send the post request to log in
# response = session.post(login_url, data=form_data)

# # Optionally, save cookies to a file for later use
# with open("cookies.txt", "w") as file:
#     for cookie in session.cookies:
#         file.write(f"{cookie.name} {cookie.value}\n")

# ... Later on, you can load these cookies back into a new session

session = requests.Session()

with open("cookies.txt", "r") as file:
    for line in file:
        name, value = line.strip().split(" ")
        session.cookies.set(name, value)

url = "https://go.teamsnap.com/team/dashboard"
response = session.get(url)
print(response.text)

# Now the new_session has the cookies loaded from the file
