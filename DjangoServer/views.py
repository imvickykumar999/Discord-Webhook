import requests
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os

# Bot Token (Keep it secure in ENV variables)
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")  

if not BOT_TOKEN:
    raise ValueError("❌ ERROR: Discord bot token is missing!")

# Discord API URLs
DISCORD_DM_URL = "https://discord.com/api/v10/users/@me/channels"  # Create DM channel
DISCORD_MESSAGE_URL = "https://discord.com/api/v10/channels/{channel_id}/messages"  # Send message

@csrf_exempt
def send_reply(request):
    """Django API to send a message via Discord DM (automatically fetches channel ID)"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")  # Get Discord User ID
            message_content = data.get("message")  # Get Message

            if not user_id or not message_content:
                return JsonResponse({"error": "Missing user_id or message"}, status=400)

            # Step 1: Get the DM Channel ID for the user
            url = DISCORD_DM_URL
            headers = {
                "Authorization": f"Bot {BOT_TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {
                "recipient_id": user_id  # Discord User ID
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                dm_channel = response.json()
                channel_id = dm_channel.get("id")

                if not channel_id:
                    return JsonResponse({"error": "Could not retrieve DM channel ID"}, status=500)

                # Step 2: Send Message to the DM Channel
                message_url = DISCORD_MESSAGE_URL.format(channel_id=channel_id)
                message_payload = {
                    "content": message_content
                }
                message_response = requests.post(message_url, headers=headers, json=message_payload)

                if message_response.status_code in [200, 201]:
                    return JsonResponse({"status": "Message sent successfully!"})
                else:
                    return JsonResponse({"error": f"Failed to send message. Discord API Response: {message_response.text}"}, status=message_response.status_code)

            else:
                return JsonResponse({"error": f"Failed to fetch DM channel ID. Discord API Response: {response.text}"}, status=response.status_code)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
