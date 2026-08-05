"""
Import as:

import helpers.test.test_hselect_action as httehselac
"""

import argparse
import logging
from typing import List

import helpers.hselect_action as hselacti
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_add_action_arg
# #############################################################################


class Test_add_action_arg(hunitest.TestCase):
    """
    Test `hselect_action.add_action_arg()`.
    """

    def helper(self, argv: List[str]) -> argparse.Namespace:
        """
        Build a parser via `add_action_arg()` and parse `argv`.

        :param argv: command-line arguments to parse (excluding the prog
            name)
        :return: parsed namespace
        """
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        # Run test.
        parser = argparse.ArgumentParser()
        hselacti.add_action_arg(parser, valid_actions, default_actions)
        args = parser.parse_args(argv)
        return args

    def test1(self) -> None:
        """
        Test that no command-line flags produce the expected defaults.
        """
        # Prepare inputs.
        argv: List[str] = []
        # Prepare outputs.
        expected = (None, None, False, False)
        # Run test.
        args = self.helper(argv)
        # Check outputs.
        actual = (
            args.action,
            args.skip_action,
            args.all_actions,
            args.clear_actions,
        )
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that `--action` and `--skip_action` accept repeated values.
        """
        # Prepare inputs.
        argv = ["--action", "a", "--action", "c", "--skip_action", "b"]
        # Prepare outputs.
        expected = (["a", "c"], ["b"])
        # Run test.
        args = self.helper(argv)
        # Check outputs.
        actual = (args.action, args.skip_action)
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test that `--enable` is no longer a recognized flag.
        """
        # Prepare inputs.
        argv = ["--enable", "c"]
        # Run test and check output.
        with self.assertRaises(SystemExit):
            self.helper(argv)

    def test4(self) -> None:
        """
        Test that `--all_actions` and `--clear_actions` are mutually
        exclusive.
        """
        # Prepare inputs.
        argv = ["--all_actions", "--clear_actions"]
        # Run test and check output.
        with self.assertRaises(SystemExit):
            self.helper(argv)


# #############################################################################
# Test_actions_to_string
# #############################################################################


class Test_actions_to_string(hunitest.TestCase):
    """
    Test `hselect_action.actions_to_string()`.
    """

    def test1(self) -> None:
        """
        Test the string representation without a frame.
        """
        # Prepare inputs.
        actions = ["a", "c"]
        valid_actions = ["a", "b", "c"]
        # Prepare outputs.
        expected = "  a: Yes\n  b: -\n  c: Yes"
        # Run test.
        actual = hselacti.actions_to_string(
            actions, valid_actions, add_frame=False
        )
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that `add_frame=True` wraps the output in a frame.
        """
        # Prepare inputs.
        actions = ["a"]
        valid_actions = ["a", "b"]
        # Prepare outputs.
        border = "#" * 80
        # TODO(ai_gp): Use a """ and dedent
        expected = (
            f"{border}\n"
            "# Action selected:\n"
            f"{border}\n"
            "    a: Yes\n"
            "    b: -"
        )
        # Run test.
        actual = hselacti.actions_to_string(
            actions, valid_actions, add_frame=True
        )
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_select_actions
# #############################################################################


class Test_select_actions(hunitest.TestCase):
    """
    Test `hselect_action.select_actions()`.
    """

    def helper(
        self,
        argv: List[str],
        valid_actions: List[str],
        default_actions: List[str],
    ) -> List[str]:
        """
        Parse `argv` through `add_action_arg()` and return the selected
        actions.

        :param argv: command-line arguments to parse (excluding the prog
            name)
        :param valid_actions: list of valid actions
        :param default_actions: list of default actions
        :return: list of selected actions
        """
        # Run test.
        parser = argparse.ArgumentParser()
        hselacti.add_action_arg(parser, valid_actions, default_actions)
        args = parser.parse_args(argv)
        actions = hselacti.select_actions(args, valid_actions, default_actions)
        return actions

    def test1(self) -> None:
        """
        Test that no flags select the default actions.
        """
        # Prepare inputs.
        argv: List[str] = []
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        # Prepare outputs.
        expected = ["a", "b"]
        # Run test.
        actual = self.helper(argv, valid_actions, default_actions)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test that `--all_actions` selects every valid action.
        """
        # Prepare inputs.
        argv = ["--all_actions"]
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        # Prepare outputs.
        expected = ["a", "b", "c"]
        # Run test.
        actual = self.helper(argv, valid_actions, default_actions)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test that `--clear_actions` alone selects no actions.
        """
        # Prepare inputs.
        argv = ["--clear_actions"]
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        # Prepare outputs.
        expected: List[str] = []
        # Run test.
        actual = self.helper(argv, valid_actions, default_actions)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test that `--clear_actions` combined with `--action` selects only
        the specified actions.
        """
        # Prepare inputs.
        argv = ["--clear_actions", "--action", "c"]
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        # Prepare outputs.
        expected = ["c"]
        # Run test.
        actual = self.helper(argv, valid_actions, default_actions)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test5(self) -> None:
        """
        Test that `--action` adds an action on top of the defaults.
        """
        # Prepare inputs.
        argv = ["--action", "c"]
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        # Prepare outputs.
        expected = ["a", "b", "c"]
        # Run test.
        actual = self.helper(argv, valid_actions, default_actions)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test6(self) -> None:
        """
        Test that `--action` on an action already in the defaults doesn't
        create a duplicate.
        """
        # Prepare inputs.
        argv = ["--action", "a"]
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        # Prepare outputs.
        expected = ["a", "b"]
        # Run test.
        actual = self.helper(argv, valid_actions, default_actions)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test7(self) -> None:
        """
        Test that `--skip_action` removes an action from the defaults.
        """
        # Prepare inputs.
        argv = ["--skip_action", "b"]
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        # Prepare outputs.
        expected = ["a"]
        # Run test.
        actual = self.helper(argv, valid_actions, default_actions)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test8(self) -> None:
        """
        Test that `--skip_action` on an action not in the current list is a
        no-op.
        """
        # Prepare inputs.
        argv = ["--skip_action", "c"]
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        # Prepare outputs.
        expected = ["a", "b"]
        # Run test.
        actual = self.helper(argv, valid_actions, default_actions)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test9(self) -> None:
        """
        Test that `--action` and `--skip_action` can be combined for
        different actions.
        """
        # Prepare inputs.
        argv = ["--action", "c", "--skip_action", "a"]
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        # Prepare outputs.
        expected = ["b", "c"]
        # Run test.
        actual = self.helper(argv, valid_actions, default_actions)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test10(self) -> None:
        """
        Test that actions are reordered according to `valid_actions`
        regardless of the order they were passed on the command line.
        """
        # Prepare inputs.
        argv = ["--clear_actions", "--action", "c", "--action", "a"]
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        # Prepare outputs.
        expected = ["a", "c"]
        # Run test.
        actual = self.helper(argv, valid_actions, default_actions)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test11(self) -> None:
        """
        Test that passing the same action to both `--action` and
        `--skip_action` raises.
        """
        # Prepare inputs.
        argv = ["--action", "c", "--skip_action", "c"]
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        # Run test and check output.
        with self.assertRaises(AssertionError):
            self.helper(argv, valid_actions, default_actions)

    def test12(self) -> None:
        """
        Test that an invalid action passed to `--action` raises.
        """
        # Prepare inputs.
        argv = ["--action", "invalid"]
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        # Run test and check output.
        with self.assertRaises(AssertionError):
            self.helper(argv, valid_actions, default_actions)

    def test13(self) -> None:
        """
        Test that `--all_actions` and `--clear_actions` together raise even
        when bypassing the parser's mutually exclusive group.
        """
        # Prepare inputs.
        valid_actions = ["a", "b", "c"]
        default_actions = ["a", "b"]
        args = argparse.Namespace(
            action=None,
            skip_action=None,
            all_actions=True,
            clear_actions=True,
        )
        # Run test and check output.
        with self.assertRaises(AssertionError):
            hselacti.select_actions(args, valid_actions, default_actions)


# #############################################################################
# Test_mark_action
# #############################################################################


class Test_mark_action(hunitest.TestCase):
    """
    Test `hselect_action.mark_action()`.
    """

    def test1(self) -> None:
        """
        Test that an action present in the list is marked for execution and
        removed from the list.
        """
        # Prepare inputs.
        action = "b"
        actions = ["a", "b", "c"]
        # Prepare outputs.
        expected_to_execute = True
        expected_actions = ["a", "c"]
        # Run test.
        to_execute, actions_out = hselacti.mark_action(action, actions)
        # Check outputs.
        self.assertEqual(to_execute, expected_to_execute)
        self.assertEqual(actions_out, expected_actions)

    def test2(self) -> None:
        """
        Test that an action absent from the list is not marked for
        execution and the list is unchanged.
        """
        # Prepare inputs.
        action = "d"
        actions = ["a", "b", "c"]
        # Prepare outputs.
        expected_to_execute = False
        expected_actions = ["a", "b", "c"]
        # Run test.
        to_execute, actions_out = hselacti.mark_action(action, actions)
        # Check outputs.
        self.assertEqual(to_execute, expected_to_execute)
        self.assertEqual(actions_out, expected_actions)

    def test3(self) -> None:
        """
        Test that `actions=None` always marks the action for execution.
        """
        # Prepare inputs.
        action = "a"
        actions = None
        # Prepare outputs.
        expected_to_execute = True
        expected_actions = None
        # Run test.
        to_execute, actions_out = hselacti.mark_action(action, actions)
        # Check outputs.
        self.assertEqual(to_execute, expected_to_execute)
        self.assertEqual(actions_out, expected_actions)
