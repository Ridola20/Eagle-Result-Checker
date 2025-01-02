import requests

def send_simple_message():
    return requests.post(
        "https://api.mailgun.net/v3/sandboxae7349da4b674887beddb068e4b9f714.mailgun.org/messages",
        auth=("api", "33f678ed4aa713e446d0af703e615dd0-2e68d0fb-c5597279"),
        data={"from": "Excited User <mailgun@sandboxae7349da4b674887beddb068e4b9f714.mailgun.org>",
            "to": ["ridwansanusiessential@gmail.com"], #"YOU@sandboxae7349da4b674887beddb068e4b9f714.mailgun.org"
            "subject": "Hello",
            "text": "Testing some Mailgun awesomeness!"})

send_simple_message()

response = send_simple_message()
print(response.status_code)
print(response.text)