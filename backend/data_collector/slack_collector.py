import os
import json
from datetime import datetime
from dotenv import load_dotenv
import slack_sdk
import time
import pandas as pd
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("slack_data_collector.log"),
        logging.StreamHandler()
    ]
)

# Load variables from .env file
load_dotenv()

# Get the token from environment variables
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")

# Check if token was loaded successfully
if not SLACK_TOKEN:
    raise ValueError("SLACK_TOKEN not found in .env file")

# Initialize Slack client
client = slack_sdk.WebClient(token=SLACK_TOKEN)

# Create output directory if it doesn't exist
os.makedirs("slack_data", exist_ok=True)
def join_all_channels():
    channels = fetch_all_channels()
    for channel in channels:
        try:
            client.conversations_join(channel=channel["id"])
            print(f"Joined: {channel['name']}")
        except SlackApiError as e:
            print(f"Error joining {channel['name']}: {e.response['error']}")

def fetch_all_users():
    """Fetch and save all users in the workspace"""
    logging.info("Fetching users...")
    try:
        users = []
        cursor = None
        
        while True:
            response = client.users_list(limit=200, cursor=cursor) if cursor else client.users_list(limit=200)
            users.extend(response["members"])
            
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
                
            # Respect rate limits
            time.sleep(1)
        
        # Save users to file
        with open("slack_data/users.json", "w") as f:
            json.dump(users, f, indent=2)
            
        # Create a more readable CSV with key user information
        user_data = []
        for user in users:
            user_data.append({
                "id": user.get("id"),
                "name": user.get("name"),
                "real_name": user.get("real_name"),
                "display_name": user.get("profile", {}).get("display_name"),
                "email": user.get("profile", {}).get("email"),
                "title": user.get("profile", {}).get("title"),
                "phone": user.get("profile", {}).get("phone"),
                "is_admin": user.get("is_admin", False),
                "is_bot": user.get("is_bot", False),
                "updated": user.get("updated")
            })
            
        df = pd.DataFrame(user_data)
        df.to_csv("slack_data/users.csv", index=False)
            
        logging.info(f"Successfully fetched and saved {len(users)} users")
        return users
        
    except slack_sdk.errors.SlackApiError as e:
        logging.error(f"Error fetching users: {e}")
        return []

def fetch_all_channels():
    """Fetch and save all channels in the workspace"""
    logging.info("Fetching channels...")
    try:
        channels = []
        cursor = None
        
        # Get public channels
        while True:
            response = client.conversations_list(
                types="public_channel", 
                limit=200,
                cursor=cursor
            ) if cursor else client.conversations_list(types="public_channel", limit=200)
            
            channels.extend(response["channels"])
            
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
                
            # Respect rate limits
            time.sleep(1)
        
        # Save channels to file
        with open("slack_data/channels.json", "w") as f:
            json.dump(channels, f, indent=2)
            
        # Create a more readable CSV with key channel information
        channel_data = []
        for channel in channels:
            channel_data.append({
                "id": channel.get("id"),
                "name": channel.get("name"),
                "is_private": channel.get("is_private", False),
                "is_archived": channel.get("is_archived", False),
                "created": channel.get("created"),
                "creator": channel.get("creator"),
                "topic": channel.get("topic", {}).get("value", ""),
                "purpose": channel.get("purpose", {}).get("value", ""),
                "num_members": channel.get("num_members", 0)
            })
            
        df = pd.DataFrame(channel_data)
        df.to_csv("slack_data/channels.csv", index=False)
            
        logging.info(f"Successfully fetched and saved {len(channels)} channels")
        return channels
        
    except slack_sdk.errors.SlackApiError as e:
        logging.error(f"Error fetching channels: {e}")
        return []

    

def get_all_messages():
    messages = fetch_all_channels()
    # map each user id to their email
    user_map = {}
    for user in fetch_all_users():
        user_map[user["id"]] = user["profile"]["real_name"]
    
    # go through the messages and replace the user id with their email
    for message in messages:
        if "user" in message:
            message["user"] = user_map.get(message["user"], message["user"])
        if "replies" in message:
            for reply in message["replies"]:
                reply["user"] = user_map.get(reply["user"], reply["user"])
    
    return messages



def fetch_channel_messages(channel_id, channel_name):
    """Fetch and save messages from a specific channel"""
    logging.info(f"Fetching messages for channel: {channel_name} ({channel_id})")
    
    try:
        # Create folder for this channel if it doesn't exist
        channel_dir = f"slack_data/channels/{channel_name}"
        os.makedirs(channel_dir, exist_ok=True)
        
        messages = []
        cursor = None
        
        while True:
            # Get conversation history
            response = client.conversations_history(
                channel=channel_id,
                limit=100,
                cursor=cursor
            ) if cursor else client.conversations_history(channel=channel_id, limit=100)
            
            messages.extend(response["messages"])
            
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
                
            # Respect rate limits
            time.sleep(1)
        
        # Save messages to file
        with open(f"{channel_dir}/messages.json", "w") as f:
            json.dump(messages, f, indent=2)
            
        # Create a more readable CSV with key message information
        message_data = []
        for msg in messages:
            message_data.append({
                "ts": msg.get("ts"),
                "datetime": datetime.fromtimestamp(float(msg.get("ts", 0))).strftime('%Y-%m-%d %H:%M:%S'),
                "user": msg.get("user"),
                "text": msg.get("text"),
                "thread_ts": msg.get("thread_ts"),
                "reply_count": msg.get("reply_count", 0),
                "reactions": json.dumps(msg.get("reactions", [])),
                "has_files": "files" in msg,
                "has_attachments": "attachments" in msg
            })
            
        df = pd.DataFrame(message_data)
        df.to_csv(f"{channel_dir}/messages.csv", index=False)
            
        logging.info(f"Successfully fetched and saved {len(messages)} messages from {channel_name}")
        
        # Fetch replies to threaded messages
        threads = {}
        for msg in messages:
            if msg.get("thread_ts") and msg.get("thread_ts") == msg.get("ts"):
                # This is a parent message with replies
                fetch_thread_replies(channel_id, msg["ts"], channel_dir, threads)
        
        # Save all threads
        if threads:
            with open(f"{channel_dir}/threads.json", "w") as f:
                json.dump(threads, f, indent=2)
        
        return messages
        
    except slack_sdk.errors.SlackApiError as e:
        logging.error(f"Error fetching messages for {channel_name}: {e}")
        return []

def fetch_thread_replies(channel_id, thread_ts, channel_dir, threads_dict):
    """Fetch replies for a specific thread"""
    try:
        replies = []
        cursor = None
        
        while True:
            response = client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                limit=100,
                cursor=cursor
            ) if cursor else client.conversations_replies(channel=channel_id, ts=thread_ts, limit=100)
            
            replies.extend(response["messages"])
            
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
                
            # Respect rate limits
            time.sleep(1)
        
        # Store replies in the dictionary
        threads_dict[thread_ts] = replies
        
        logging.info(f"Successfully fetched {len(replies)} replies for thread {thread_ts}")
        
    except slack_sdk.errors.SlackApiError as e:
        logging.error(f"Error fetching thread replies for {thread_ts}: {e}")

def generate_summary_report(users, channels):
    """Generate a summary report of the data collected"""
    try:
        report = {
            "workspace_name": client.auth_test()["team"],
            "collection_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "num_users": len(users),
            "num_channels": len(channels),
            "user_types": {
                "regular_users": len([u for u in users if not u.get("is_bot") and not u.get("deleted")]),
                "bots": len([u for u in users if u.get("is_bot")]),
                "deleted_users": len([u for u in users if u.get("deleted")])
            },
            "channel_types": {
                "active_channels": len([c for c in channels if not c.get("is_archived")]),
                "archived_channels": len([c for c in channels if c.get("is_archived")])
            }
        }
        
        # Save report
        with open("slack_data/summary_report.json", "w") as f:
            json.dump(report, f, indent=2)
            
        logging.info("Generated summary report")
        
        # Print summary to console
        print("\n===== Slack Data Collection Summary =====")
        print(f"Workspace: {report['workspace_name']}")
        print(f"Collection Date: {report['collection_date']}")
        print(f"Total Users: {report['num_users']}")
        print(f"Total Channels: {report['num_channels']}")
        print("\nUser Breakdown:")
        print(f"  Regular Users: {report['user_types']['regular_users']}")
        print(f"  Bots: {report['user_types']['bots']}")
        print(f"  Deleted Users: {report['user_types']['deleted_users']}")
        print("\nChannel Breakdown:")
        print(f"  Active Channels: {report['channel_types']['active_channels']}")
        print(f"  Archived Channels: {report['channel_types']['archived_channels']}")
        print("========================================\n")
        
    except Exception as e:
        logging.error(f"Error generating summary report: {e}")

def main():
    try:
        # Test the connection
        response = client.auth_test()
        logging.info(f"Connected to Slack workspace: {response['team']}")

        # join all channels
        join_all_channels()

        # Fetch all users
        users = fetch_all_users()
        
        # Fetch all channels
        channels = fetch_all_channels()
        
        # Create directory for channel data
        os.makedirs("slack_data/channels", exist_ok=True)
        
        # Fetch messages for each channel
        for channel in channels:
            # Skip archived channels (optional)
            if channel.get("is_archived"):
                logging.info(f"Skipping archived channel: {channel['name']}")
                continue
                
            fetch_channel_messages(channel["id"], channel["name"])
            # Add a delay between channel fetches to respect rate limits
            time.sleep(2)
        
        # Generate summary report
        generate_summary_report(users, channels)
        
        logging.info("Data collection complete!")
        
    except slack_sdk.errors.SlackApiError as e:
        logging.error(f"Error connecting to Slack API: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == "__main__":

    start_time = time.time()
    main()
    end_time = time.time()
    logging.info(f"Script execution completed in {end_time - start_time:.2f} seconds")

    msg = get_all_messages()
    print()
    print('finish')
    print(msg)