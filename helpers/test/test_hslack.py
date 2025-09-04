import os
import unittest.mock as umock

import helpers.hslack as hslack
import helpers.hunit_test as hunitest


class TestSlackNotifier(hunitest.TestCase):

    def test1(self) -> None:
        """
        Check that `SlackNotifier` initializes with provided bot token.
        """
        # Create notifier with explicit token.
        notifier = hslack.SlackNotifier(bot_token="xoxb-test1-token")
        self.assertEqual(notifier.bot_token, "xoxb-test1-token")

    def test2(self) -> None:
        """
        Check that `SlackNotifier` initializes with environment variable token.
        """
        # Mock environment variable and create notifier.
        with umock.patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test2-token"}):
            notifier = hslack.SlackNotifier()
            self.assertEqual(notifier.bot_token, "xoxb-test2-token")

    def test3(self) -> None:
        """
        Check that `SlackNotifier` raises `ValueError` when no token is provided.
        """
        # Clear environment and verify initialization fails.
        with umock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as cm:
                hslack.SlackNotifier()
            self.assertIn("No bot token provided", str(cm.exception))

    def test4(self) -> None:
        """
        Check that `send_message()` successfully sends message to Slack channel.
        """
        # Mock successful Slack API response.
        with umock.patch("helpers.hslack.requests.post") as mock_post:
            mock_response = umock.MagicMock()
            mock_response.json.return_value = {"ok": True}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            # Send message and verify API call.
            notifier = hslack.SlackNotifier(bot_token="xoxb-test4-token")
            notifier.send_message("#test4", "test4 message content")
            # Verify request parameters.
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            self.assertEqual(kwargs["json"]["channel"], "#test4")
            self.assertEqual(kwargs["json"]["text"], "test4 message content")

    def test5(self) -> None:
        """
        Check that `send_message()` raises `ValueError` on Slack API error.
        """
        # Mock Slack API error response.
        with umock.patch("helpers.hslack.requests.post") as mock_post:
            mock_response = umock.MagicMock()
            mock_response.json.return_value = {"ok": False, "error": "channel_not_found"}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            # Verify error is raised with correct message.
            notifier = hslack.SlackNotifier(bot_token="xoxb-test5-token")
            with self.assertRaises(ValueError) as cm:
                notifier.send_message("#test5", "test5 message content")
            self.assertIn("channel_not_found", str(cm.exception))
