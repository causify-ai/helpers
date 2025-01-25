"""
Parent class for all lint actions.

About pedantic modes:

There are some lints that:
  A) we disagree with (e.g., too many functions in a class)
      - they are ignored all the times.
  B) are too hard to respect (e.g., each function has a docstring)
      - they are ignored unless we want to see them.

Pedantic=2 -> all lints, including a) and b)
Pedantic=1 -> discard lints from a), include b)
Pedantic=0 -> discard lints from a) and b)

- The default is to run with (-> pedantic=0)
- Sometimes we want to take a look at the lints that we would like to enforce.
  (-> pedantic=1)
- In rare occasions we want to see all the lints (-> pedantic=2)

Import as:

import linters.action as liaction
"""
import os
import sys
from typing import List, Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit

# TODO(gp): joblib asserts when using abstract classes:
#   AttributeError: '_BasicHygiene' object has no attribute '_executable'
## class Action(abc.ABC):
class Action:
    """
    Implemented as a Strategy pattern.
    """

    def __init__(self, executable: str = "") -> None:
        self._executable = executable

    ## @abc.abstractmethod
    def check_if_possible(self) -> bool:
        """
        Check if the action can be executed.
        """
        raise NotImplementedError

    def execute(self, file_name: str, pedantic: int) -> List[str]:
        """
        Execute the action.

        :param file_name: name of the file to process
        :param pendantic: True if it needs to be run in angry mode
        :return: list of strings representing the output
        """
        hdbg.dassert(file_name)
        hdbg.dassert_path_exists(file_name)
        # Store file ownership.
        file_uid, file_gid = self._get_ownership(file_name)
        output = self._execute(file_name, pedantic)
        hdbg.dassert_list_of_strings(output)
        # Ensure to restore ownership.
        self._ensure_ownership(file_name, file_uid, file_gid)
        return output

    def run(self, file_names: List[str], abort_on_change: bool = True) -> None:
        """
        Run the action on list of files.

        :param file_names: names of the files to process
        :param abort_on_change:
        :return:
        """
        full_output: List[str] = []
        for file_name in file_names:
            hdbg.dassert_path_exists(file_name)
            output = self.execute(file_name, pedantic=0)
            full_output.extend(output)
        # Print the output.
        hdbg.dassert_list_of_strings(full_output)
        print("\n".join(full_output))
        if abort_on_change:
            # Exit.
            rc = len(full_output)
            sys.exit(rc)
        else:
            # Stage all changed files.
            hgit.git_add_update(file_list=file_names)
            sys.exit(0)

    @staticmethod
    def _get_ownership(file_name: str) -> Tuple[int, int]:
        """
        Get a tuple with ownership ids (uid and gid) of the file.

        :param file_name: name of the file to process
        :return: a tuple [uid, gid]
        """
        file_stat = os.stat(file_name)
        file_uid = file_stat.st_uid
        file_gid = file_stat.st_gid
        return file_uid, file_gid

    @staticmethod
    def _ensure_ownership(file_name: str, file_uid: int, file_gid: int) -> None:
        """
        Ensure that file ownership is preserved as was prior to change.

        :param file_name: name of the file to process
        :param file_uid: id of the user owner of the file
        :param file_gid: id of the group owner of the file
        """
        changed_file_stat = os.stat(file_name)
        changed_file_uid = changed_file_stat.st_uid
        changed_file_gid = changed_file_stat.st_gid
        if changed_file_uid != file_uid or changed_file_gid != file_gid:
            os.chown(file_name, file_uid, file_gid)

    ## @abc.abstractmethod
    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        raise NotImplementedError


class CompositeAction(Action):
    def __init__(self, actions: List[Action]) -> None:
        super().__init__()
        self._actions = actions

    def check_if_possible(self) -> bool:
        """
        Check if all sub-actions could be run.

        :return: a boolean
        """
        for action in self._actions:
            if not action.check_if_possible():
                return False
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        """
        Execute all sub-actions.

        :param file_name: name of the file to process
        :param pendantic: configuration of angry mode
        """
        output: List[str] = []
        for action in self._actions:
            output.extend(action.execute(file_name, pedantic))
        return output
