import datetime
import logging
import uuid

import pandas as pd

import helpers.hpandas as hpandas
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

_AWS_PROFILE = "ck"


# #############################################################################
# TestDataframeToJson
# #############################################################################


class TestDataframeToJson(hunitest.TestCase):
    def test_dataframe_to_json(self) -> None:
        """
        Verify correctness of dataframe to JSON transformation.
        """
        # Initialize a dataframe.
        test_dataframe = pd.DataFrame(
            {
                "col_1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
                "col_2": [1, 2, 3, 4, 5, 6, 7],
            }
        )
        # Convert dataframe to JSON.
        output_str = hpandas.convert_df_to_json_string(
            test_dataframe, n_head=3, n_tail=3
        )
        self.check_string(output_str)

    def test_dataframe_to_json_uuid(self) -> None:
        """
        Verify correctness of UUID-containing dataframe transformation.
        """
        # Initialize a dataframe.
        test_dataframe = pd.DataFrame(
            {
                "col_1": [
                    uuid.UUID("421470c7-7797-4a94-b584-eb83ff2de88a"),
                    uuid.UUID("22cde381-1782-43dc-8c7a-8712cbdf5ee1"),
                ],
                "col_2": [1, 2],
            }
        )
        # Convert dataframe to JSON.
        output_str = hpandas.convert_df_to_json_string(
            test_dataframe, n_head=None, n_tail=None
        )
        self.check_string(output_str)

    def test_dataframe_to_json_timestamp(self) -> None:
        """
        Verify correctness of transformation of a dataframe with Timestamps.
        """
        # Initialize a dataframe.
        test_dataframe = pd.DataFrame(
            {
                "col_1": [
                    pd.Timestamp("2020-01-01"),
                    pd.Timestamp("2020-05-12"),
                ],
                "col_2": [1.0, 2.0],
            }
        )
        # Convert dataframe to JSON.
        output_str = hpandas.convert_df_to_json_string(
            test_dataframe, n_head=None, n_tail=None
        )
        self.check_string(output_str)

    def test_dataframe_to_json_datetime(self) -> None:
        """
        Verify correctness of transformation of a dataframe with datetime.
        """
        # Initialize a dataframe.
        test_dataframe = pd.DataFrame(
            {
                "col_1": [
                    datetime.datetime(2020, 1, 1),
                    datetime.datetime(2020, 5, 12),
                ],
                "col_2": [1.0, 2.0],
            }
        )
        # Convert dataframe to JSON.
        output_str = hpandas.convert_df_to_json_string(
            test_dataframe, n_head=None, n_tail=None
        )
        self.check_string(output_str)


# #############################################################################
# Test_list_to_str
# #############################################################################


class Test_list_to_str(hunitest.TestCase):
    def test1(self) -> None:
        """
        Check that a list is converted to string correctly.
        """
        # Prepare inputs.
        input = [1, "two", 3, 4, "five"]
        # Run.
        actual = hprint.list_to_str2(input, enclose_str_char="|", sep_char=" ; ")
        # Check.
        expected = "5 [|1| ; |two| ; |3| ; |4| ; |five|]"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Check that a list is converted to string and truncated correctly.
        """
        # Prepare inputs.
        input = list(range(15))
        # Run.
        actual = hprint.list_to_str2(input, enclose_str_char="", sep_char=" - ")
        # Check.
        expected = "15 [0 - 1 - 2 - 3 - 4 - ... - 10 - 11 - 12 - 13 - 14]"
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Check that a list is converted to string correctly, without additional
        parameters.
        """
        # Prepare inputs.
        input = [1, 2, 3, 4, "five"]
        # Run.
        actual = hprint.list_to_str2(input)
        # Check.
        expected = "5 ['1', '2', '3', '4', 'five']"
        self.assert_equal(actual, expected)
