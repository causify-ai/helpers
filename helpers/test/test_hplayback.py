import datetime
import logging
import os
from typing import Any, List, Optional

import pandas as pd
import pytest

import helpers.hserver as hserver

if not hserver.is_inside_docker():
    pytest.skip("Skipping: tests require dev container", allow_module_level=True)


import config_root.config as cconfig
import helpers.hio as hio
import helpers.hplayback as hplayba
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# TestJsonRoundtrip1
# #############################################################################


@pytest.mark.need_dev_container
class TestJsonRoundtrip1(hunitest.TestCase):
    """
    Test roundtrip conversion through jsonpickle for different types.
    """

    def test1(self) -> None:
        obj = 3
        #
        hplayba.round_trip_convert(obj, logging.DEBUG)

    def test2(self) -> None:
        obj = "hello"
        #
        hplayba.round_trip_convert(obj, logging.DEBUG)

    def test3(self) -> None:
        data = {
            "Product": ["Desktop Computer", "Tablet", "iPhone", "Laptop"],
            "Price": [700, 250, 800, 1200],
        }
        df = pd.DataFrame(data, columns=["Product", "Price"])
        df.index.name = "hello"
        #
        obj = df
        hplayba.round_trip_convert(obj, logging.DEBUG)

    def test4(self) -> None:
        obj = datetime.date(2015, 1, 1)
        #
        hplayba.round_trip_convert(obj, logging.DEBUG)


# #############################################################################
# TestPlaybackInputOutput1
# #############################################################################


@pytest.mark.need_dev_container
class TestPlaybackInputOutput1(hunitest.TestCase):
    """
    Freeze the output of Playback.
    """

    def helper(self, mode: str, *args: Any, **kwargs: Any) -> None:
        # TODO(gp): Factor out the common code.
        # Define a function to generate a unit test for.
        def get_result_assert_equal(a: Any, b: Any) -> Any:
            p = hplayba.Playback("assert_equal")
            if isinstance(a, datetime.date) and isinstance(b, datetime.date):
                return p.run(abs(a - b))
            if isinstance(a, dict) and isinstance(b, dict):
                c = {}
                c.update(a)
                c.update(b)
                return p.run(c)
            if isinstance(a, cconfig.Config) and isinstance(b, cconfig.Config):
                c = cconfig.Config(update_mode="overwrite")
                c.update(a)
                c.update(b)
                return p.run(c)
            return p.run(a + b)

        def get_result_check_string(a: Any, b: Any) -> Any:
            p = hplayba.Playback("check_string")
            if isinstance(a, datetime.date) and isinstance(b, datetime.date):
                return p.run(abs(a - b))
            if isinstance(a, dict) and isinstance(b, dict):
                c = {}
                c.update(a)
                c.update(b)
                return p.run(c)
            if isinstance(a, cconfig.Config) and isinstance(b, cconfig.Config):
                c = cconfig.Config(update_mode="overwrite")
                c.update(a)
                c.update(b)
                return p.run(c)
            return p.run(a + b)

        def get_result_assert_equal_none() -> Any:
            p = hplayba.Playback("assert_equal")
            return p.run("Some string.")

        def get_result_check_string_none() -> Any:
            p = hplayba.Playback("check_string")
            return p.run("Some string")

        if mode == "assert_equal":
            if not args and not kwargs:
                code = get_result_assert_equal_none()
            else:
                code = get_result_assert_equal(*args, **kwargs)
        elif mode == "check_string":
            if not args and not kwargs:
                code = get_result_check_string_none()
            else:
                code = get_result_check_string(*args, **kwargs)
        else:
            raise ValueError("Invalid mode ")
        self.check_string(code, purify_text=True)
        _LOG.debug("Testing code:\n%s", code)
        exec(code, locals())  # pylint: disable=exec-used

    def test1(self) -> None:
        """
        Test for int inputs.
        """
        # Create inputs.
        a = 3
        b = 2
        # Generate, freeze and execute a unit test.
        self.helper("assert_equal", a=a, b=b)

    def test2(self) -> None:
        """
        Test for string inputs.
        """
        # Create inputs.
        a = "test"
        b = "case"
        # Generate, freeze and execute a unit test.
        self.helper("assert_equal", a=a, b=b)

    def test3(self) -> None:
        """
        Test for list inputs.
        """
        # Create inputs.
        a = [1, 2, 3]
        b = [4, 5, 6]
        # Generate, freeze and execute a unit test.
        self.helper("assert_equal", a=a, b=b)

    def test4(self) -> None:
        """
        Test for dict inputs.
        """
        # Create inputs.
        a = {"1": 2}
        b = {"3": 4}
        # Generate, freeze and execute a unit test.
        self.helper("assert_equal", a=a, b=b)

    def test5(self) -> None:
        """
        Test for pd.DataFrame inputs.
        """
        # Create inputs.
        a = pd.DataFrame({"Price": [700, 250, 800, 1200]})
        b = pd.DataFrame({"Price": [1, 1, 1, 1]})
        # Generate, freeze and execute a unit test.
        self.helper("assert_equal", a=a, b=b)

    def test6(self) -> None:
        """
        Test for datetime.date inputs (using `jsonpickle`).
        """
        # Create inputs.
        a = datetime.date(2015, 1, 1)
        b = datetime.date(2012, 1, 1)
        # Generate, freeze and execute a unit test.
        self.helper("assert_equal", a=a, b=b)

    def test7(self) -> None:
        """
        Test for int inputs with check_string.
        """
        # Create inputs.
        a = 3
        b = 2
        # Generate, freeze and execute a unit test.
        self.helper("check_string", a=a, b=b)

    def test8(self) -> None:
        """
        Test for string inputs with check_string.
        """
        # Create inputs.
        a = "test"
        b = "case"
        # Generate, freeze and execute a unit test.
        self.helper("check_string", a=a, b=b)

    def test9(self) -> None:
        """
        Test for list inputs with check_string.
        """
        # Create inputs.
        a = [1, 2, 3]
        b = [4, 5, 6]
        # Generate, freeze and execute a unit test.
        self.helper("check_string", a=a, b=b)

    def test10(self) -> None:
        """
        Test for dict inputs with check_string.
        """
        # Create inputs.
        a = {"1": 2}
        b = {"3": 4}
        # Generate, freeze and execute a unit test.
        self.helper("check_string", a=a, b=b)

    def test11(self) -> None:
        """
        Test for pd.DataFrame inputs with check_string.
        """
        # Create inputs.
        a = pd.DataFrame({"Price": [700, 250, 800, 1200]})
        b = pd.DataFrame({"Price": [1, 1, 1, 1]})
        # Generate, freeze and execute a unit test.
        self.helper("check_string", a=a, b=b)

    def test12(self) -> None:
        """
        Test for dict inputs with data structures recursion.
        """
        # Create inputs.
        a = {"1": ["a", 2]}
        b = {"3": pd.DataFrame({"Price": [700, 250, 800, 1200]}), "4": {"5": 6}}
        # Generate, freeze and execute a unit test.
        self.helper("assert_equal", a=a, b=b)

    def test13(self) -> None:
        """
        Test for pd.Series inputs with check_string.
        """
        # Create inputs.
        a = pd.Series([10, 20, 15], name="N Numbers")
        b = pd.Series([10.0, 0.0, 5.5], name="Z Numbers")
        # Generate, freeze and execute a unit test.
        self.helper("check_string", a=a, b=b)

    def test14(self) -> None:
        """
        Test for pd.Series inputs with assert_equal.
        """
        # Create inputs.
        a = pd.Series([10, 20, 15], name="N Numbers")
        b = pd.Series([10.0, 0.0, 5.5], name="Z Numbers")
        # Generate, freeze and execute a unit test.
        self.helper("assert_equal", a=a, b=b)

    def test15(self) -> None:
        """
        Test for cconfig.Config inputs with check_string.
        """
        # Create inputs.
        a = cconfig.Config([("meta", "meta value 1"), ("list", [1, 2])])
        b = cconfig.Config([("meta", "meta value 2")])
        # Generate, freeze and execute a unit test.
        self.helper("check_string", a=a, b=b)

    def test16(self) -> None:
        """
        Test for cconfig.Config inputs with assert_equal.
        """
        # Create inputs.
        a = cconfig.Config([("meta", "meta value 1"), ("list", [1, 2])])
        b = cconfig.Config([("meta", "meta value 2")])
        # Generate, freeze and execute a unit test.
        self.helper("assert_equal", a=a, b=b)

    def test17(self) -> None:
        """
        Test if testing function has no args with check_string.
        """
        self.helper("check_string")

    def test18(self) -> None:
        """
        Test if testing function has no args with assert_equal.
        """
        self.helper("assert_equal")


# #############################################################################
# TestToPythonCode1
# #############################################################################


@pytest.mark.need_dev_container
class TestToPythonCode1(hunitest.TestCase):
    """
    Test to_python_code() for different types.
    """

    def _check(self, input_obj: Any, expected: str) -> None:
        res = hplayba.to_python_code(input_obj)
        self.assert_equal(res, expected)

    def test_float1(self) -> None:
        """
        Test float without first zero.
        """
        self._check(0.1, "0.1")

    def test_float2(self) -> None:
        """
        Test positive float.
        """
        self._check(1.0, "1.0")

    def test_float3(self) -> None:
        """
        Test negative float.
        """
        self._check(-1.1, "-1.1")

    def test_int1(self) -> None:
        """
        Test zero.
        """
        self._check(0, "0")

    def test_int2(self) -> None:
        """
        Test positive int.
        """
        self._check(10, "10")

    def test_int3(self) -> None:
        """
        Test negative int.
        """
        self._check(-10, "-10")

    def test_str1(self) -> None:
        """
        Test str simple.
        """
        self._check("a", '"a"')

    def test_str2(self) -> None:
        """
        Test str with double quotes.
        """
        self._check('"b"', '"\\"b\\""')

    def test_str3(self) -> None:
        """
        Test str with single quotes.
        """
        self._check("'c'", "\"'c'\"")

    def test_list1(self) -> None:
        """
        Test List.
        """
        self._check([1, 0.2, "3"], '[1, 0.2, "3"]')

    def test_dict1(self) -> None:
        """
        Test Dist.
        """
        self._check({"a": 0.2, 3: "b"}, '{"a": 0.2, 3: "b"}')

    def test_df1(self) -> None:
        """
        Test pd.DataFrame (single quotes expected in field names)
        """
        self._check(
            pd.DataFrame.from_dict({"a": [0.2, 0.1]}),
            "pd.DataFrame.from_dict({'a': [0.2, 0.1]})",
        )

    def test_dataseries1(self) -> None:
        """
        Test pd.Series.
        """
        self._check(
            pd.Series([0.2, 0.1], name="a"),
            "pd.Series(data=[0.2, 0.1], index=RangeIndex(start=0, stop=2, step=1), "
            'name="a", dtype=float64)',
        )

    def test_config1(self) -> None:
        """
        Test cconfig.Config.
        """
        config = cconfig.Config()
        config["var1"] = "val1"
        config["var2"] = cconfig.Config([("var3", 10), ("var4", "val4")])
        self._check(
            config,
            "cconfig.Config.from_python(\"Config({'var1': 'val1', "
            "'var2': Config({'var3': 10, 'var4': 'val4'})})\")",
        )


# #############################################################################
# TestPlaybackFilePath1
# #############################################################################


@pytest.mark.need_dev_container
class TestPlaybackFilePath1(hunitest.TestCase):
    """
    Test file mode correctness.
    """

    def test1(self) -> None:
        """
        Test writing to file when number of tests is more than generated (10).
        """
        test_file = hplayba.Playback._get_test_file_name(
            "./path/to/somewhere.py"
        )
        self.assert_equal(
            test_file, "./path/to/test/test_by_playback_somewhere.py"
        )


# #############################################################################
# TestPlaybackFileMode1
# #############################################################################


@pytest.mark.need_dev_container
class TestPlaybackFileMode1(hunitest.TestCase):
    """
    Test file mode correctness.
    """

    def get_code(self, max_tests: Optional[int] = None) -> str:
        """
        Return a code for executable file to run.
        """
        max_tests_str = "" if max_tests is None else f", max_tests={max_tests}"
        code = (
            "\n".join(
                [
                    "import helpers.hplayback as hplayba",
                    "def plbck_sum(a: int, b: int) -> int:",
                    '    hplayba.Playback("check_string", to_file=True%s).run(None)',
                    "    return a + b",
                    "",
                    "[plbck_sum(i, i + 1) for i in range(4)]",
                ]
            )
            % max_tests_str
        )
        return code

    def helper(self, max_tests: Optional[int] = None) -> Any:
        """
        Return generated by playback code.
        """
        # Get file paths.
        tmp_dir = self.get_scratch_space()
        # File with code.
        code_basename = "code_.py"
        tmp_py_file = os.path.join(tmp_dir, code_basename)
        # File with test.
        tmp_test_file = os.path.join(
            tmp_dir, "test", "test_by_playback_" + code_basename
        )
        # Save the code to the file.
        hio.to_file(tmp_py_file, self.get_code(max_tests))
        # Executes the code.
        hsystem.system(f"python {tmp_py_file}")
        playback_code = hio.from_file(tmp_test_file)
        return playback_code

    @pytest.mark.requires_ck_infra
    @pytest.mark.slow("~10 seconds.")
    def test1(self) -> None:
        """
        Test writing to file when number of tests is more than generated.
        """
        max_tests = 100
        self.check_string(self.helper(max_tests))

    @pytest.mark.requires_ck_infra
    @pytest.mark.slow("~10 seconds.")
    def test2(self) -> None:
        """
        Test writing to file when number of tests is default.
        """
        self.check_string(self.helper())

    @pytest.mark.requires_ck_infra
    @pytest.mark.slow("~10 seconds.")
    def test3(self) -> None:
        """
        Test writing to file when number of tests is lower than generated.
        """
        max_tests = 2
        self.check_string(self.helper(max_tests))


# #############################################################################
# Test_record_replay_storage1
# #############################################################################


class Test_record_replay_storage1(hunitest.TestCase):
    """
    Test the storage layer used by `@record` and the mock classes.
    """

    def test1(self) -> None:
        """
        Test round-trip of records with simple types.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "records.json")
        records = [
            {"args": ["cmd1"], "kwargs": {}, "result": [{"id": "1"}]},
            {"args": ["cmd2"], "kwargs": {"limit": 5}, "result": [{"id": "2"}]},
        ]
        # Run test.
        hplayba._save_records(file_path, records)
        actual = hplayba._load_records(file_path)
        # Check outputs.
        self.assert_equal(str(actual), str(records))

    def test2(self) -> None:
        """
        Test that the saved fixture file is human-readable JSON for simple
        types.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "records.json")
        records = [
            {"args": ["echo hi"], "kwargs": {}, "result": [{"id": "abc"}]},
        ]
        # Run test.
        hplayba._save_records(file_path, records)
        actual = hio.from_file(file_path)
        # Check outputs.
        # The saved file must contain the args/result inline as readable JSON.
        self.assertIn("echo hi", actual)
        self.assertIn("abc", actual)


# #############################################################################
# Test_recording1
# #############################################################################


class Test_recording1(hunitest.TestCase):
    """
    Test the `@record` decorator and the `recording()` context manager.
    """

    def test1(self) -> None:
        """
        Test that an undecorated call writes nothing and behaves normally.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "records.json")

        @hplayba.record(file_path)
        def add(a: int, b: int) -> int:
            return a + b

        # Run test.
        actual = add(2, 3)
        # Check outputs.
        self.assertEqual(actual, 5)
        # No file should have been written.
        self.assertFalse(os.path.exists(file_path))

    def test2(self) -> None:
        """
        Test that calls inside `recording()` are captured and flushed.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "records.json")

        @hplayba.record(file_path)
        def add(a: int, b: int) -> int:
            return a + b

        # Run test.
        with hplayba.recording(add):
            add(2, 3)
            add(10, 20)
        actual = hplayba._load_records(file_path)
        # Prepare outputs.
        expected = [
            {"args": [2, 3], "kwargs": {}, "result": 5},
            {"args": [10, 20], "kwargs": {}, "result": 30},
        ]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        """
        Test that calls outside the context are not captured.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "records.json")

        @hplayba.record(file_path)
        def add(a: int, b: int) -> int:
            return a + b

        # Run test.
        # Before the context: not captured.
        add(1, 1)
        with hplayba.recording(add):
            add(2, 3)
        # After the context: not captured.
        add(5, 5)
        actual = hplayba._load_records(file_path)
        # Prepare outputs.
        expected = [{"args": [2, 3], "kwargs": {}, "result": 5}]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test4(self) -> None:
        """
        Test that recording is turned off even if the block raises.
        """
        # Prepare inputs.
        file_path = os.path.join(self.get_scratch_space(), "records.json")

        @hplayba.record(file_path)
        def add(a: int, b: int) -> int:
            return a + b

        # Run test.
        with self.assertRaises(RuntimeError):
            with hplayba.recording(add):
                add(2, 3)
                raise RuntimeError("boom")
        # Subsequent calls outside the context must not be recorded.
        add(99, 99)
        actual = hplayba._load_records(file_path)
        # Prepare outputs.
        expected = [{"args": [2, 3], "kwargs": {}, "result": 5}]
        # Check outputs.
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# TestMockDict1
# #############################################################################


class TestMockDict1(hunitest.TestCase):
    """
    Test `MockDict` for order-independent replay.
    """

    def _write_fixture(self, records: List[Any]) -> hplayba.MockDict:
        """
        Persist `records` to a scratch fixture and return a `MockDict`.
        """
        file_path = os.path.join(self.get_scratch_space(), "records.json")
        hplayba._save_records(file_path, records)
        return hplayba.MockDict(file_path)

    def test1(self) -> None:
        """
        Test lookup of a recorded call.
        """
        # Prepare inputs.
        records = [
            {"args": ["cmd1"], "kwargs": {}, "result": [{"id": "1"}]},
            {"args": ["cmd2"], "kwargs": {}, "result": [{"id": "2"}]},
        ]
        mock_dict = self._write_fixture(records)
        # Run test.
        actual1 = mock_dict("cmd1")
        actual2 = mock_dict("cmd2")
        # Check outputs.
        self.assertEqual(actual1, [{"id": "1"}])
        self.assertEqual(actual2, [{"id": "2"}])

    def test2(self) -> None:
        """
        Test that calls can be replayed in any order.
        """
        # Prepare inputs.
        records = [
            {"args": ["A"], "kwargs": {}, "result": 1},
            {"args": ["B"], "kwargs": {}, "result": 2},
        ]
        mock_dict = self._write_fixture(records)
        # Run test.
        # Call in the reverse order.
        actual_b = mock_dict("B")
        actual_a = mock_dict("A")
        # Check outputs.
        self.assertEqual(actual_a, 1)
        self.assertEqual(actual_b, 2)

    def test3(self) -> None:
        """
        Test that missing keys raise an assertion error.
        """
        # Prepare inputs.
        records = [{"args": ["cmd1"], "kwargs": {}, "result": "ok"}]
        mock_dict = self._write_fixture(records)
        # Run test and check output.
        with self.assertRaises(AssertionError):
            mock_dict("missing_cmd")


# #############################################################################
# TestMockSequence1
# #############################################################################


class TestMockSequence1(hunitest.TestCase):
    """
    Test `MockSequence` for ordered replay.
    """

    def _write_fixture(self, records: List[Any]) -> hplayba.MockSequence:
        """
        Persist `records` to a scratch fixture and return a `MockSequence`.
        """
        file_path = os.path.join(self.get_scratch_space(), "records.json")
        hplayba._save_records(file_path, records)
        return hplayba.MockSequence(file_path)

    def test1(self) -> None:
        """
        Test that results are returned in the recorded order.
        """
        # Prepare inputs.
        records = [
            {"args": ["A"], "kwargs": {}, "result": 1},
            {"args": ["B"], "kwargs": {}, "result": 2},
            {"args": ["C"], "kwargs": {}, "result": 3},
        ]
        mock_seq = self._write_fixture(records)
        # Run test.
        actual_a = mock_seq("A")
        actual_b = mock_seq("B")
        actual_c = mock_seq("C")
        # Check outputs.
        self.assertEqual(actual_a, 1)
        self.assertEqual(actual_b, 2)
        self.assertEqual(actual_c, 3)

    def test2(self) -> None:
        """
        Test that out-of-order calls raise an assertion error.
        """
        # Prepare inputs.
        records = [
            {"args": ["A"], "kwargs": {}, "result": 1},
            {"args": ["B"], "kwargs": {}, "result": 2},
        ]
        mock_seq = self._write_fixture(records)
        # Run test and check output.
        with self.assertRaises(AssertionError):
            mock_seq("B")

    def test3(self) -> None:
        """
        Test that exhausting the sequence raises an assertion error.
        """
        # Prepare inputs.
        records = [{"args": ["A"], "kwargs": {}, "result": 1}]
        mock_seq = self._write_fixture(records)
        # Run test.
        mock_seq("A")
        # Check outputs.
        with self.assertRaises(AssertionError):
            mock_seq("A")

    def test4(self) -> None:
        """
        Test that `reset()` restarts the sequence.
        """
        # Prepare inputs.
        records = [{"args": ["A"], "kwargs": {}, "result": 1}]
        mock_seq = self._write_fixture(records)
        # Run test.
        first_call = mock_seq("A")
        mock_seq.reset()
        second_call = mock_seq("A")
        # Check outputs.
        self.assertEqual(first_call, 1)
        self.assertEqual(second_call, 1)
