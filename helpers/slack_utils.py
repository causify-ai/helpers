"""
Slack Analytics Utility Extracts channels, groups, and user activity metrics
from Slack workspace.

Import as:

import helpers.slack_utils as hslautil
"""

import collections
import datetime
import logging
import os
from typing import Any, Dict, List, Optional

import pandas as pd
import slack_sdk

_LOG = logging.getLogger(__name__)


# #############################################################################
# SlackAnalytics
# #############################################################################


class SlackAnalytics:

    def __init__(self, token: Optional[str] = None):
        """
        Initialize Slack client.

        :param token: Slack bot token
        """
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError(
                "Slack token required via parameter or SLACK_BOT_TOKEN env var"
            )
        self.client = slack_sdk.WebClient(token=self.token)
        self._verify_connection()

    def get_all_channels(self) -> List[Dict[str, Any]]:
        """
        Get all public channels in the workspace.

        :return: channel dictionaries with metadata
        """
        channels = []
        cursor = None
        while True:
            response = self.client.conversations_list(
                types="public_channel",
                exclude_archived=False,
                limit=200,
                cursor=cursor,
            )
            for channel in response["channels"]:
                channels.append(
                    {
                        "id": channel["id"],
                        "name": channel["name"],
                        "is_channel": channel["is_channel"],
                        "is_archived": channel["is_archived"],
                        "is_general": channel.get("is_general", False),
                        "num_members": channel.get("num_members", 0),
                        "created": channel["created"],
                        "creator": channel.get("creator", ""),
                        "topic": channel.get("topic", {}).get("value", ""),
                        "purpose": channel.get("purpose", {}).get("value", ""),
                    }
                )
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        _LOG.info("Retrieved %d public channels", len(channels))
        return channels

    def get_all_groups(self) -> List[Dict[str, Any]]:
        """
        Get all private channels (groups) in the workspace.

        :return: private channel dictionaries with metadata
        """
        groups = []
        cursor = None
        while True:
            response = self.client.conversations_list(
                types="private_channel",
                exclude_archived=False,
                limit=200,
                cursor=cursor,
            )
            for group in response["channels"]:
                groups.append(
                    {
                        "id": group["id"],
                        "name": group["name"],
                        "is_private": group.get("is_private", True),
                        "is_archived": group["is_archived"],
                        "num_members": group.get("num_members", 0),
                        "created": group["created"],
                        "creator": group.get("creator", ""),
                        "topic": group.get("topic", {}).get("value", ""),
                        "purpose": group.get("purpose", {}).get("value", ""),
                    }
                )
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        _LOG.info("Retrieved %d private channels", len(groups))
        return groups

    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users in the workspace.

        :return: user dictionaries with metadata
        """
        users = []
        cursor = None
        while True:
            response = self.client.users_list(cursor=cursor, limit=200)
            for user in response["members"]:
                if not user["deleted"] and not user["is_bot"]:
                    users.append(
                        {
                            "id": user["id"],
                            "name": user.get("name", ""),
                            "real_name": user.get("real_name", ""),
                            "display_name": user.get("profile", {}).get(
                                "display_name", ""
                            ),
                            "email": user.get("profile", {}).get("email", ""),
                            "is_admin": user.get("is_admin", False),
                            "is_owner": user.get("is_owner", False),
                            "is_primary_owner": user.get(
                                "is_primary_owner", False
                            ),
                            "timezone": user.get("tz", ""),
                        }
                    )
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        _LOG.info("Retrieved %d active users", len(users))
        return users

    def get_channel_messages(
        self, channel_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a specific channel.

        :param channel_id: channel ID to fetch messages from
        :param days: number of days to look back
        :return: message dictionaries
        """
        messages = []
        oldest = (
            datetime.datetime.now() - datetime.timedelta(days=days)
        ).timestamp()
        cursor = None
        while True:
            response = self.client.conversations_history(
                channel=channel_id, oldest=str(oldest), limit=200, cursor=cursor
            )
            messages.extend(response["messages"])
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        return messages

    def calculate_user_activity(
        self, days: int = 30
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate activity metrics per user across all accessible channels.

        :param days: number of days to analyze
        :return: dictionary with user_id as key and activity metrics as
            value
        """
        user_activity = collections.defaultdict(
            lambda: {
                "message_count": 0,
                "channels_active": set(),
                "reactions_given": 0,
                "files_shared": 0,
                "threads_started": 0,
                "replies_count": 0,
            }
        )
        # Get all channels (public and private that bot has access to).
        all_channels = self.get_all_channels()
        _LOG.info(
            "Analyzing activity across %d channels for last %d days",
            len(all_channels),
            days,
        )
        accessible_channels = 0
        skipped_channels = 0
        for channel in all_channels:
            channel_id = channel["id"]
            channel_name = channel["name"]
            try:
                messages = self.get_channel_messages(channel_id, days)
            except slack_sdk.errors.SlackApiError as e:
                if e.response.get("error") == "not_in_channel":
                    _LOG.debug("Bot not in channel %s, skipping", channel_id)
                    skipped_channels += 1
                    continue
                raise
            if not messages:
                skipped_channels += 1
                continue
            accessible_channels += 1
            _LOG.info(
                "Processing channel: %s (%d messages)",
                channel_name,
                len(messages),
            )
            for msg in messages:
                user_id = msg.get("user")
                if not user_id:
                    continue
                # Count messages.
                user_activity[user_id]["message_count"] += 1
                user_activity[user_id]["channels_active"].add(channel_id)
                # Count reactions given.
                if "reactions" in msg:
                    for reaction in msg["reactions"]:
                        if user_id in reaction.get("users", []):
                            user_activity[user_id]["reactions_given"] += 1
                # Count files shared.
                if "files" in msg:
                    user_activity[user_id]["files_shared"] += len(msg["files"])
                # Count threads started.
                if "thread_ts" in msg and msg.get("thread_ts") == msg.get("ts"):
                    user_activity[user_id]["threads_started"] += 1
                # Count replies.
                if "thread_ts" in msg and msg.get("thread_ts") != msg.get("ts"):
                    user_activity[user_id]["replies_count"] += 1
        _LOG.info(
            "Analysis complete: %d accessible channels, %d skipped (bot not member)",
            accessible_channels,
            skipped_channels,
        )
        # Convert sets to counts.
        result = {}
        for user_id, metrics in user_activity.items():
            result[user_id] = {
                "user_id": user_id,
                "message_count": metrics["message_count"],
                "channels_active_count": len(metrics["channels_active"]),
                "reactions_given": metrics["reactions_given"],
                "files_shared": metrics["files_shared"],
                "threads_started": metrics["threads_started"],
                "replies_count": metrics["replies_count"],
                "total_activity_score": (
                    metrics["message_count"]
                    + metrics["reactions_given"] * 0.5
                    + metrics["files_shared"] * 2
                    + metrics["threads_started"] * 1.5
                    + metrics["replies_count"]
                ),
            }
        _LOG.info("Calculated activity for %d users", len(result))
        return result

    def get_workspace_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive workspace statistics.

        :param days: number of days to analyze for activity metrics
        :return: dictionary with workspace statistics
        """
        channels = self.get_all_channels()
        groups = self.get_all_groups()
        users = self.get_all_users()
        activity = self.calculate_user_activity(days)
        data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "analysis_period_days": days,
            "channels": {
                "total": len(channels),
                "active": len([c for c in channels if not c["is_archived"]]),
                "archived": len([c for c in channels if c["is_archived"]]),
                "list": channels,
            },
            "groups": {
                "total": len(groups),
                "active": len([g for g in groups if not g["is_archived"]]),
                "archived": len([g for g in groups if g["is_archived"]]),
                "list": groups,
            },
            "users": {
                "total": len(users),
                "admins": len([u for u in users if u["is_admin"]]),
                "list": users,
            },
            "user_activity": activity,
        }
        return data

    def get_user_activity_dataframe(self, days: int = 30):
        """
        Get user activity as a pandas DataFrame with user names.

        :param days: number of days to analyze
        :return: pandas DataFrame with user activity and names
        """
        # Get users and activity.
        users = self.get_all_users()
        activity = self.calculate_user_activity(days)
        # Create user lookup dictionary.
        user_lookup = {user["id"]: user for user in users}
        # Build DataFrame rows.
        rows = []
        for user_id, metrics in activity.items():
            user_info = user_lookup.get(user_id, {})
            rows.append(
                {
                    "user_id": user_id,
                    "name": user_info.get("name", "Unknown"),
                    "real_name": user_info.get("real_name", "Unknown"),
                    "display_name": user_info.get("display_name", ""),
                    "email": user_info.get("email", ""),
                    "is_admin": user_info.get("is_admin", False),
                    "message_count": metrics["message_count"],
                    "channels_active_count": metrics["channels_active_count"],
                    "reactions_given": metrics["reactions_given"],
                    "files_shared": metrics["files_shared"],
                    "threads_started": metrics["threads_started"],
                    "replies_count": metrics["replies_count"],
                    "total_activity_score": metrics["total_activity_score"],
                }
            )
        df = pd.DataFrame(rows)
        # Sort by activity score.
        df = df.sort_values("total_activity_score", ascending=False).reset_index(
            drop=True
        )
        _LOG.info("Created DataFrame with %d users", len(df))
        return df

    def _verify_connection(self):
        """
        Verify Slack API connection.
        """
        response = self.client.auth_test()
        _LOG.info("Connected to Slack workspace: %s", response["team"])
