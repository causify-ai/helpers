"""
Select and manage action execution based on command-line arguments.

Import as:

import helpers.hselect_action as hselacti
"""

import argparse
import logging
from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# Use the following idiom to process actions:
#
#  ```
#  import helpers.hselect_action as hselacti
#  import helpers.hparser as hparser
#
#  _VALID_ACTIONS = ["download", "process", "upload", "cleanup"]
#  _DEFAULT_ACTIONS = ["download", "process", "upload"]
#
#  def _parse() -> argparse.ArgumentParser:
#      parser = argparse.ArgumentParser(...)
#      # Define valid and default actions.
#      hselacti.add_action_arg(parser, VALID_ACTIONS, _DEFAULT_ACTIONS)
#      hparser.add_verbosity_arg(parser)
#      return parser
#
#  def _main(args: argparse.Namespace) -> None:
#      # Select which actions to execute.
#      actions = hselacti.select_actions(
#          args,
#          valid_actions=VALID_ACTIONS,
#          default_actions=_DEFAULT_ACTIONS,
#      )
#      print(hselacti.actions_to_string(actions, VALID_ACTIONS, add_frame=True))
#      # Execute selected actions.
#      while actions:
#          action = actions[0]
#          to_execute, actions = hselacti.mark_action(action, actions)
#          if not to_execute:
#            continue
#          if action == "download":
#              data = _download()
#          elif action == "process":
#              data = _process(...)
#          elif action == "upload":
#              _upload(...)
#          elif action == "cleanup":
#              _cleanup()
#          else:
#              raise ValueError(f"Invalid action='{action}'")
#       hdbg.dassert_eq(len(actions), 0,
#         "There are unprocessed actions: %s", str(actions))
#   ```

def add_action_arg(
    parser: argparse.ArgumentParser,
    valid_actions: List[str],
    default_actions: List[str],
) -> argparse.ArgumentParser:
    """
    Add command line options to select actions to execute, skip, or enable.

    The function creates a mutually exclusive group with three options:
    - `-a/--action`: specify exact actions to execute
    - `-sa/--skip_action`: skip specific actions from default set
    - `-e/--enable`: enable additional actions on top of defaults

    Available actions are listed once in the help epilog to avoid repetition.

    :param parser: parser to add the option to
    :param valid_actions: list of valid actions
    :param default_actions: list of default actions to execute
    :return: parser with the option added
    """
    # Add epilog with list of available actions to avoid repeating them.
    actions_list = "\n".join([f"- {action}" for action in valid_actions])
    if parser.epilog:
        parser.epilog += "\n\n"
    epilog = f"## Available actions:\n{actions_list}"
    default_list = "\n".join([f"- {action}" for action in default_actions])
    epilog += f"\n\n## Default actions:\n{default_list}"
    parser.epilog = epilog
    # Create mutually exclusive group for action selection.
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--action",
        action="append",
        dest="action",
        help="Actions to execute (see available actions below)",
    )
    group.add_argument(
        "--skip_action",
        action="append",
        dest="skip_action",
        help="Actions to skip from default set (see available actions below)",
    )
    group.add_argument(
        "-e",
        "--enable",
        action="append",
        dest="enable_action",
        help="Enable additional actions on top of defaults (see available actions below)",
    )
    hdbg.dassert_is_subset(default_actions, valid_actions)
    parser.add_argument(
        "--all_actions",
        action="store_true",
        dest="all_actions",
        help=f"Run all the actions ({' '.join(default_actions)})",
    )
    return parser


def actions_to_string(
    actions: List[str], valid_actions: List[str], add_frame: bool
) -> str:
    """
    Convert a list of actions to a string.

    :param actions: list of actions to convert
    :param valid_actions: list of valid actions
    :param add_frame: if `True`, add a frame around the actions
    :return: string of the actions
    """
    space = max(len(a) for a in valid_actions) + 2
    format_ = "%" + str(space) + "s: %s"
    actions = [
        format_ % (a, "Yes" if a in actions else "-") for a in valid_actions
    ]
    actions_as_str = "\n".join(actions)
    if add_frame:
        ret = hprint.frame("# Action selected:") + "\n"
        ret += hprint.indent(actions_as_str)
    else:
        ret = actions_as_str
    return ret  # type: ignore


def select_actions(
    args: argparse.Namespace,
    valid_actions: List[str],
    default_actions: List[str],
) -> List[str]:
    """
    Select actions based on the command line arguments.

    Supports three mutually exclusive modes:
    - `--action`: run only specified actions
    - `--skip_action`: run default actions minus specified ones
    - `--enable`: run default actions plus specified additional ones

    :param args: command line arguments
    :param valid_actions: list of valid actions
    :param default_actions: list of default actions to execute
    :return: list of selected actions
    """
    hdbg.dassert(
        not (args.action and args.all_actions),
        "You can't specify together --action and --all_actions",
    )
    hdbg.dassert(
        not (args.action and args.skip_action),
        "You can't specify together --action and --skip_action",
    )
    # Check for enable_action attribute (added for backward compatibility).
    has_enable = hasattr(args, "enable_action")
    if has_enable:
        hdbg.dassert(
            not (args.action and args.enable_action),
            "You can't specify together --action and --enable",
        )
        hdbg.dassert(
            not (args.skip_action and args.enable_action),
            "You can't specify together --skip_action and --enable",
        )
    # Select actions.
    if not args.action or args.all_actions:
        hdbg.dassert_is_subset(default_actions, valid_actions)
        # Convert it into list since through some code paths it can be a tuple.
        actions = list(default_actions)
    else:
        # Validate actions specified by user.
        for action in args.action:
            hdbg.dassert_in(
                action,
                valid_actions,
                "Invalid action '%s'",
                action,
            )
        actions = args.action[:]
    hdbg.dassert_isinstance(actions, list)
    hdbg.dassert_no_duplicates(actions)
    # Remove actions, if needed.
    if args.skip_action:
        hdbg.dassert_isinstance(args.skip_action, list)
        for skip_action in args.skip_action:
            # Validate that skip_action is a valid action.
            hdbg.dassert_in(
                skip_action,
                valid_actions,
                "Invalid action '%s'",
                skip_action,
            )
            # Validate that skip_action is in the current action list.
            if skip_action not in actions:
                _LOG.warning(
                    "Skipping action '%s' since it's already not in actions='%s'",
                    skip_action,
                    actions,
                )
            actions = [a for a in actions if a != skip_action]
    # Add enabled actions on top of defaults.
    if has_enable and args.enable_action:
        hdbg.dassert_isinstance(args.enable_action, list)
        for enable_action in args.enable_action:
            hdbg.dassert_in(
                enable_action,
                valid_actions,
                "Invalid action '%s'",
                enable_action,
            )
            if enable_action not in actions:
                actions.append(enable_action)
    # Reorder actions according to 'valid_actions'.
    actions = [action for action in valid_actions if action in actions]
    return actions


def mark_action(
    action: str,
    actions: Optional[List[str]],
    *,
    verbosity_level: int = logging.INFO,
) -> Tuple[bool, Optional[List[str]]]:
    """
    Mark an action as to be executed or skipped.

    :param action: action to mark
    :param actions: list of actions, or None to execute all actions
    :return: tuple of (to_execute, actions)
    """
    if actions is None:
        # If actions is None, execute all actions.
        to_execute = True
    else:
        to_execute = action in actions
    _LOG.log(verbosity_level, "\n%s", hprint.frame(f"action={action}"))
    if to_execute:
        if actions is not None:
            actions = [a for a in actions if a != action]
    else:
        _LOG.warning("Skip action='%s'", action)
    return to_execute, actions
