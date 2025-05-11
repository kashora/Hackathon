from simplegmail import Gmail
from simplegmail.query import construct_query



def get_gmail_messages():
    gmail = Gmail(
        client_secret_file = "../../../client_secret.json",
        creds_file = "../../../gmail_token.json",
    )

    query_params = {
        "newer_than": (1, "week"),
        "older_than": (0, "year")
    }

    messages = gmail.get_messages()
    return messages


if __name__ == "__main__":
    messages = get_gmail_messages()
    #print(messages)
    for message in messages:
        print("To: " + message.recipient)
        print("From: " + message.sender)
        print("Subject: " + message.subject)
        print("Date: " + message.date)
        print("Preview: " + message.snippet)
        
        with open("email_samples.txt", "a") as f:
            if message.plain:
                if len(message.plain) < 1000:
                    f.write(message.plain)
        # print("Message Body: " + message.plain)  # or message.html