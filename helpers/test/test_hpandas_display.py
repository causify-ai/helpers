import datetime
import logging
import unittest.mock
import uuid
from typing import Optional, Union

import pandas as pd

import helpers.hpandas as hpandas
import helpers.hpandas_display as hpandisp
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

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
        self.assert_equal(actual, expected, fuzzy_match=True)

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
        self.assert_equal(actual, expected, fuzzy_match=True)

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
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test_display_df
# #############################################################################


class Test_display_df(hunitest.TestCase):
    """
    Test the display_df function.
    """

    def helper_test_display_df(
        self,
        df: Union[pd.DataFrame, pd.Series],
        **kwargs,
    ) -> str:
        """
        Test helper for display_df.

        :param df: Input dataframe or series
        :param kwargs: Keyword arguments to pass to display_df
        :return: Captured output from display_df
        """
        # Capture the output from print_or_display and logging.
        outputs = []
        tag = kwargs.get("tag")

        def mock_print_or_display(
            mock_df: pd.DataFrame,
            *,
            index: bool = True,
            as_txt: bool = False,
            log_level: int = logging.INFO,
        ) -> None:
            """
            Capture the dataframe string representation.
            """
            if as_txt or not index:
                output = mock_df.to_string(index=index)
            else:
                output = mock_df.to_html(index=index)
            outputs.append(output)

        # Run test.
        with unittest.mock.patch(
            "helpers.hpandas_display.print_or_display",
            side_effect=mock_print_or_display,
        ):
            with unittest.mock.patch(
                "helpers.hpandas_display._LOG.log"
            ) as mock_log:
                hpandisp.display_df(
                    df,
                    log_level=logging.DEBUG,
                    **kwargs,
                )
                # Capture tag logging if present.
                if tag is not None and mock_log.called:
                    for call in mock_log.call_args_list:
                        if "tag=" in str(call):
                            outputs.append(f"tag={tag}")
        # Return captured output.
        return "\n".join(outputs)

    def test1(self) -> None:
        """
        Test display_df with small dataframe.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "col_1": [1, 2, 3],
                "col_2": ["a", "b", "c"],
            }
        )
        # Prepare outputs.
        expected = """
        <table border="1" class="dataframe">
          <thead>
            <tr style="text-align: right;">
              <th></th>
              <th>col_1</th>
              <th>col_2</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th>0</th>
              <td>1</td>
              <td>a</td>
            </tr>
            <tr>
              <th>1</th>
              <td>2</td>
              <td>b</td>
            </tr>
            <tr>
              <th>2</th>
              <td>3</td>
              <td>c</td>
            </tr>
          </tbody>
        </table>
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_test_display_df(df)
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test display_df with large dataframe and max_lines.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "col_1": list(range(100)),
                "col_2": [f"val_{i}" for i in range(100)],
            }
        )
        # Prepare outputs.
        expected = """
        <table border="1" class="dataframe">
          <thead>
            <tr style="text-align: right;">
              <th></th>
              <th>col_1</th>
              <th>col_2</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th>0</th>
              <td>0</td>
              <td>val_0</td>
            </tr>
            <tr>
              <th>1</th>
              <td>1</td>
              <td>val_1</td>
            </tr>
            <tr>
              <th>...</th>
              <td>...</td>
              <td>...</td>
            </tr>
            <tr>
              <th>98</th>
              <td>98</td>
              <td>val_98</td>
            </tr>
            <tr>
              <th>99</th>
              <td>99</td>
              <td>val_99</td>
            </tr>
          </tbody>
        </table>
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_test_display_df(df, max_lines=5)
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Test display_df with inline_index=True.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "col_1": [1, 2, 3],
                "col_2": ["a", "b", "c"],
            }
        )
        # Prepare outputs.
        expected = """
         .  col_1 col_2
         0      1     a
         1      2     b
         2      3     c
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_test_display_df(df, inline_index=True, index=True)
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test4(self) -> None:
        """
        Test display_df with index=False.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "col_1": [1, 2, 3],
                "col_2": ["a", "b", "c"],
            }
        )
        # Prepare outputs.
        expected = """
         col_1 col_2
             1     a
             2     b
             3     c
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_test_display_df(df, index=False)
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test5(self) -> None:
        """
        Test display_df with named index and inline_index=True.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "col_1": [1, 2, 3],
                "col_2": ["a", "b", "c"],
            }
        )
        df.index.name = "my_index"
        # Prepare outputs.
        expected = """
         my_index  col_1 col_2
                0      1     a
                1      2     b
                2      3     c
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_test_display_df(df, inline_index=True, index=False)
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test6(self) -> None:
        """
        Test display_df with Pandas Series (should convert to DataFrame).
        """
        # Prepare inputs.
        series = pd.Series([1, 2, 3, 4, 5], name="my_series")
        # Prepare outputs.
        expected = """
         .  my_series
         0          1
         1          2
         2          3
         3          4
         4          5

        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_test_display_df(series, inline_index=True, index=False)
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test7(self) -> None:
        """
        Test display_df with tag parameter.
        """
        # Prepare inputs.
        df = pd.DataFrame({"col_1": [1, 2, 3]})
        # Prepare outputs.
        expected = """
         .  col_1
         0      1
         1      2
         2      3
        tag=my_tag
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_test_display_df(df, tag="my_tag", inline_index=True, index=False)
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test8(self) -> None:
        """
        Test display_df with mode='all_rows'.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "col_1": list(range(50)),
                "col_2": [f"val_{i}" for i in range(50)],
            }
        )
        # Prepare outputs.
        expected = """
        <table border="1" class="dataframe">
          <thead>
            <tr style="text-align: right;">
              <th></th>
              <th>col_1</th>
              <th>col_2</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th>0</th>
              <td>0</td>
              <td>val_0</td>
            </tr>
            <tr>
              <th>1</th>
              <td>1</td>
              <td>val_1</td>
            </tr>
            <tr>
              <th>...</th>
              <td>...</td>
              <td>...</td>
            </tr>
            <tr>
              <th>48</th>
              <td>48</td>
              <td>val_48</td>
            </tr>
            <tr>
              <th>49</th>
              <td>49</td>
              <td>val_49</td>
            </tr>
          </tbody>
        </table>
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_test_display_df(df, mode="all_rows")
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test9(self) -> None:
        """
        Test display_df with mode='all_cols'.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "col_1": [1, 2, 3],
                "col_2": ["a", "b", "c"],
                "col_3": [10.5, 20.5, 30.5],
            }
        )
        # Prepare outputs.
        expected = """
        <table border="1" class="dataframe">
          <thead>
            <tr style="text-align: right;">
              <th></th>
              <th>col_1</th>
              <th>col_2</th>
              <th>col_3</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th>0</th>
              <td>1</td>
              <td>a</td>
              <td>10.5</td>
            </tr>
            <tr>
              <th>1</th>
              <td>2</td>
              <td>b</td>
              <td>20.5</td>
            </tr>
            <tr>
              <th>2</th>
              <td>3</td>
              <td>c</td>
              <td>30.5</td>
            </tr>
          </tbody>
        </table>
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_test_display_df(df, mode="all_cols")
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test10(self) -> None:
        """
        Test display_df with mode='all'.
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "col_1": list(range(50)),
                "col_2": [f"val_{i}" for i in range(50)],
            }
        )
        # Prepare outputs.
        expected = """
        <table border="1" class="dataframe">
          <thead>
            <tr style="text-align: right;">
              <th></th>
              <th>col_1</th>
              <th>col_2</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th>0</th>
              <td>0</td>
              <td>val_0</td>
            </tr>
            <tr>
              <th>1</th>
              <td>1</td>
              <td>val_1</td>
            </tr>
            <tr>
              <th>...</th>
              <td>...</td>
              <td>...</td>
            </tr>
            <tr>
              <th>48</th>
              <td>48</td>
              <td>val_48</td>
            </tr>
            <tr>
              <th>49</th>
              <td>49</td>
              <td>val_49</td>
            </tr>
          </tbody>
        </table>
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_test_display_df(df, mode="all")
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test11(self) -> None:
        """
        Test display_df with invalid mode raises error.
        """
        # Prepare inputs.
        df = pd.DataFrame({"col_1": [1, 2, 3]})
        # Run test and check output.
        with self.assertRaises(ValueError) as cm:
            hpandisp.display_df(
                df,
                mode="invalid_mode",
                log_level=logging.DEBUG,
            )
        self.assertIn("Invalid mode", str(cm.exception))

    def test12(self) -> None:
        """
        Test display_df with duplicate columns raises assertion.
        """
        # Prepare inputs.
        df = pd.DataFrame([[1, 2], [3, 4]])
        df.columns = ["col", "col"]
        # Run test and check output.
        with self.assertRaises(AssertionError):
            hpandisp.display_df(df, log_level=logging.DEBUG)

    def test13(self) -> None:
        """
        Test display_df with single row dataframe.
        """
        # Prepare inputs.
        df = pd.DataFrame({"col_1": [1], "col_2": ["a"]})
        # Prepare outputs.
        expected = """
        <table border="1" class="dataframe">
          <thead>
            <tr style="text-align: right;">
              <th></th>
              <th>col_1</th>
              <th>col_2</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th>0</th>
              <td>1</td>
              <td>a</td>
            </tr>
          </tbody>
        </table>
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_test_display_df(df, max_lines=5)
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test14(self) -> None:
        """
        Test display_df with max_lines=1 (edge case).
        """
        # Prepare inputs.
        df = pd.DataFrame(
            {
                "col_1": list(range(10)),
                "col_2": [f"val_{i}" for i in range(10)],
            }
        )
        # Prepare outputs.
        expected = """
        <table border="1" class="dataframe">
          <thead>
            <tr style="text-align: right;">
              <th></th>
              <th>col_1</th>
              <th>col_2</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th>0</th>
              <td>0</td>
              <td>val_0</td>
            </tr>
            <tr>
              <th>1</th>
              <td>1</td>
              <td>val_1</td>
            </tr>
            <tr>
              <th>...</th>
              <td>...</td>
              <td>...</td>
            </tr>
            <tr>
              <th>8</th>
              <td>8</td>
              <td>val_8</td>
            </tr>
            <tr>
              <th>9</th>
              <td>9</td>
              <td>val_9</td>
            </tr>
          </tbody>
        </table>
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = self.helper_test_display_df(df, mode="all")
        # Check output.
        self.assert_equal(actual, expected, fuzzy_match=True)
