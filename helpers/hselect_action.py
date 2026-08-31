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
#
# The list of actions to execute is built as follows:
# 1) Select the starting list:
#    - `--all_actions`: start from all `valid_actions`
#    - `--clear_actions`: start from an empty list
#    - otherwise: start from `default_actions`
# 2) `--action <name>`: add `name` to the list (warn if already present)
# 3) `--skip_action <name>`: remove `name` from the list (warn if not
#    present)
# `--action` and `--skip_action` can be repeated and used together, but the
# same action can't be passed to both at the same time.
#
# `--only_action <name>` is a separate, exclusive idiom: it overrides all of
# the above and sets the list of actions to exactly `name` (can be repeated
# to select more than one action). It's incompatible with `--action`,
# `--skip_action`, `--all_actions`, and `--clear_actions`: passing any of
# them together with `--only_action` raises an assertion.
#
# TODO(gp): Rename `--action` to `--add_action` to make it symmetric with
# `--skip_action` and `--only_action` (i.e., "add" / "skip" / "only").
# TODO(gp): `--only_action` should override all the options and set the
# actions to only that value


def add_action_arg(
    parser: argparse.ArgumentParser,
    valid_actions: List[str],
    default_actions: List[str],
) -> argparse.ArgumentParser:
    """
    Add command line options to select the actions to execute.

    The starting list of actions is `default_actions`, unless overridden by
    `--all_actions` (start from `valid_actions`) or `--clear_actions` (start
    from an empty list).
    - `--all_actions` and `--clear_actions` are mutually exclusive since they
      both set the starting list.
    - `--action` and `--skip_action` then add / remove actions from that starting
      list and can be freely combined (see `select_actions()`)
    - `--only_action <name>` overrides all of the above and is incompatible
      with every other action-related option: it sets the list of actions to
      exactly `name` (can be repeated), asserting if `--action`,
      `--skip_action`, `--all_actions`, or `--clear_actions` is also passed

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
    hdbg.dassert_is_subset(default_actions, valid_actions)
    parser.add_argument(
        "--action",
        action="append",
        dest="action",
        help="Add an action to the list of actions to execute",
    )
    parser.add_argument(
        "--only_action",
        action="append",
        dest="only_action",
        help=(
            "Run only this action (can be repeated), overriding all other "
            "action options; incompatible with --action, --skip_action, "
            "--all_actions, and --clear_actions"
        ),
    )
    parser.add_argument(
        "--skip_action",
        action="append",
        dest="skip_action",
        help="Remove an action from the list of actions to execute",
    )
    # Create mutually exclusive group for the starting list of actions.
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--all_actions",
        action="store_true",
        dest="all_actions",
        help="Run all the valid actions",
    )
    group.add_argument(
        "--clear_actions",
        action="store_true",
        dest="clear_actions",
        help="Start from an empty list of actions",
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

    The starting list of actions is:
    - `valid_actions` if `--all_actions` is specified
    - an empty list if `--clear_actions` is specified
    - `default_actions` otherwise

    `--action` then adds actions to that list (warning if an action is
    already present) and `--skip_action` removes actions from it (warning if
    an action is not present). The same action can't be passed to both
    `--skip_action` and `--action`.

    `--only_action <name>` overrides all of the above: it sets the list of
    actions to exactly the specified action(s), regardless of
    `default_actions`, and it's incompatible with every other action-related
    option (`--action`, `--skip_action`, `--all_actions`, `--clear_actions`),
    which is enforced with an assertion.

    :param args: command line arguments
    :param valid_actions: list of valid actions
    :param default_actions: list of default actions to execute
    :return: list of selected actions
    """
    hdbg.dassert_is_subset(default_actions, valid_actions)
    hdbg.dassert(
        not (args.all_actions and args.clear_actions),
        "You can't specify together --all_actions and --clear_actions",
    )
    # Convert to lists since through some code paths they can be tuples.
    action = list(args.action) if args.action else []
    skip_action = list(args.skip_action) if args.skip_action else []
    only_action = (
        list(args.only_action) if getattr(args, "only_action", None) else []
    )
    if only_action:
        # `--only_action` overrides everything else and is incompatible with
        # any other action-related option.
        hdbg.dassert(
            not action,
            "You can't specify --action together with --only_action",
        )
        hdbg.dassert(
            not skip_action,
            "You can't specify --skip_action together with --only_action",
        )
        hdbg.dassert(
            not args.all_actions,
            "You can't specify --all_actions together with --only_action",
        )
        hdbg.dassert(
            not args.clear_actions,
            "You can't specify --clear_actions together with --only_action",
        )
        for curr_action in only_action:
            hdbg.dassert_in(
                curr_action,
                valid_actions,
                "Invalid action '%s'",
                curr_action,
            )
        # Reorder actions according to 'valid_actions'.
        actions = [a for a in valid_actions if a in only_action]
        return actions
    # Validate the actions specified by the user.
    for curr_action in action + skip_action:
        hdbg.dassert_in(
            curr_action,
            valid_actions,
            "Invalid action '%s'",
            curr_action,
        )
    # An action can't be added and removed at the same time.
    overlap = set(action) & set(skip_action)
    hdbg.dassert_eq(
        len(overlap),
        0,
        "The following actions are passed to both --action and "
        "--skip_action: %s",
        sorted(overlap),
    )
    # Select the starting list of actions.
    if args.all_actions:
        actions = list(valid_actions)
    elif args.clear_actions:
        actions = []
    else:
        actions = list(default_actions)
    hdbg.dassert_no_duplicates(actions)
    # Add the requested actions.
    for curr_action in action:
        if curr_action in actions:
            _LOG.warning(
                "Action '%s' is already in the list of actions='%s'",
                curr_action,
                actions,
            )
        else:
            actions.append(curr_action)
    # Remove the requested actions.
    for curr_action in skip_action:
        if curr_action not in actions:
            _LOG.warning(
                "Skipping action '%s' since it's already not in actions='%s'",
                curr_action,
                actions,
            )
        actions = [a for a in actions if a != curr_action]
    # Reorder actions according to 'valid_actions'.
    actions = [a for a in valid_actions if a in actions]
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
