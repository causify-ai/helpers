"""
Slack notification utilities for sending messages to Slack channels.

Import as:

import helpers.hslack as hslack
"""

import logging
import os
from typing import Optional

import requests

_LOG = logging.getLogger(__name__)


# #############################################################################
# SlackNotifier
# #############################################################################


class SlackNotifier:
    """
    Send notifications to Slack channels using bot tokens.
    """

    def __init__(self, bot_token: Optional[str] = None) -> None:
        """
        Initialize Slack notifier.

        :param bot_token: Slack bot token (starts with 'xoxb-')
        """
        self.bot_token = bot_token or os.environ.get("SLACK_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError(
                "No bot token provided via parameter or SLACK_BOT_TOKEN env var"
            )

    def send_message(
        self,
        message: str,
        channel_id: str,
        title: Optional[str] = None,
    ) -> None:
        """
        Send a message to a Slack channel.

        :param message: Message text to send
        :param channel_id: Slack channel ID (e.g., 'C1234567890'),
            channel name (e.g., '#notifications')
        :param title: Optional title for the message (will be formatted
            in bold)
        """
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json",
        }
        if title:
            # Format message with title if provided.
            formatted_message = f"*{title}*\n{message}"
        else:
            formatted_message = message
        payload = {
            "channel": channel_id,
            "text": formatted_message,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        if not result.get("ok"):
            raise ValueError(f"Slack API error: {result.get('error')}")
        _LOG.info("Message sent successfully to %s", channel_id)
