import logging
import os
import types
import unittest.mock as umock

import pandas as pd
import pytest

pytest.importorskip(
    "openai"
)  # noqa: E402 # pylint: disable=wrong-import-position

import helpers.hopenai as hopenai
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

_TEST_CACHE_FILE = "cache.test_get_completion.json"

_USER_PROMPT1 = "what is machine learning?"
_USER_PROMPT2 = _USER_PROMPT1.upper()
_USER_PROMPT3 = "What is artificial intelligence"

_SYSTEM_PROMPT1 = "You are a helpful AI assistant."
_SYSTEM_PROMPT2 = "You are a very helpful AI assistant."


_TEMPERATURE1 = 1
_TEMPERATURE2 = 2

_MODEL1 = "gpt-4o-mini"
_MODEL2 = "gpt-o4-mini"


def _get_completion_parameters1() -> dict:
    data = {
        "user_prompt": _USER_PROMPT1,
        "system_prompt": _SYSTEM_PROMPT1,
        "temperature": _TEMPERATURE1,
        "model": _MODEL1,
    }
    return data


def _get_openai_request_parameters1() -> dict:
    messages = hopenai._build_messages(
        user_prompt=_USER_PROMPT1, system_prompt=_SYSTEM_PROMPT1
    )
    data = {"messages": messages, "temperature": _TEMPERATURE1, "model": _MODEL1}
    return data


def _get_completion_parameters2() -> dict:
    data = {
        "user_prompt": _USER_PROMPT2,
        "system_prompt": _SYSTEM_PROMPT1,
        "temperature": _TEMPERATURE1,
        "model": _MODEL1,
    }
    return data


def _get_openai_request_parameters2() -> dict:
    messages = hopenai._build_messages(
        user_prompt=_USER_PROMPT2, system_prompt=_SYSTEM_PROMPT1
    )
    data = {"messages": messages, "temperature": _TEMPERATURE1, "model": _MODEL1}
    return data


def _get_completion_parameters3() -> dict:
    data = {
        "user_prompt": _USER_PROMPT1,
        "system_prompt": _SYSTEM_PROMPT1,
        "temperature": _TEMPERATURE2,
        "model": _MODEL1,
    }
    return data


def _get_openai_request_parameters3() -> dict:
    messages = hopenai._build_messages(
        user_prompt=_USER_PROMPT1, system_prompt=_SYSTEM_PROMPT1
    )
    data = {"messages": messages, "temperature": _TEMPERATURE2, "model": _MODEL1}
    return data


def _get_completion_parameters4() -> dict:
    data = {
        "user_prompt": _USER_PROMPT1,
        "system_prompt": _SYSTEM_PROMPT1,
        "temperature": _TEMPERATURE2,
        "model": _MODEL2,
    }
    return data


def _get_openai_request_parameters4() -> dict:
    messages = hopenai._build_messages(
        user_prompt=_USER_PROMPT1, system_prompt=_SYSTEM_PROMPT1
    )
    data = {"messages": messages, "temperature": _TEMPERATURE2, "model": _MODEL2}
    return data


def _get_dummy_openai_response1() -> dict:
    response = {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1_612_345_678,
        "model": _MODEL1,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": """Machine learning is a subset of artificial intelligence
                      (AI) that focuses on the development of algorithms and statistical models
                        that enable computers to perform tasks without explicit instructions.
                        Instead, these systems learn from and make predictions or
                        decisions based on data.""",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 4, "total_tokens": 9},
    }
    return response


def _get_dummy_openai_response2() -> dict:
    response = {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1_612_345_999,
        "model": _MODEL2,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    # TODO(gp): Use hprint.dedent
                    "content": """Artificial Intelligence (AI) is the field of computer science focused on creating
                                 systems or machines that can perform tasks typically requiring human
                                 intelligence. These tasks include:
                                •   Perception: Recognizing images, speech, or patterns (e.g., facial recognition, voice assistants).
                                •   Reasoning and Decision-Making: Solving problems and making decisions (e.g., self-driving cars deciding
                                    when to stop or accelerate).
                                •   Learning: Improving performance from experience (e.g., recommendation systems like Netflix or Amazon).
                                •   Natural Language Understanding: Interacting using human language (e.g., chatbots, language translation).
                                •   Action: Controlling devices or robots to perform tasks (e.g., industrial automation, drones).""",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 200,
            "total_tokens": 215,
        },
    }
    return response


# #############################################################################
# _OpenAICacheTestCase
# #############################################################################


# TODO(*): Rename _OpenAICacheTestCase
class _OpenAICacheTestCase(hunitest.TestCase):
    """
    - Ensure hopenai.get_completion() always uses REPLAY mode.
    - Add dummy data to the test cache file for test cases.
    - Remove the test cache file after running tests.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> None:
        # Using test cache file to prevent ruining the actual cache file.
        # TODO(Sai): Reuse get_scratch_space().
        # self.cache_file = self.get_scratch_space()+f"/{_TEST_CACHE_FILE}"
        self.get_completion_cache = hopenai._CompletionCache(
            cache_file=_TEST_CACHE_FILE
            # cache_file=self.cache_file
        )
        # Patch get_completion to inject REPLAY.
        self.force_replay_cache()
        # Run common setuo for each test.
        self.set_up_test()
        yield
        # Run common teardown after the test.
        self.tear_down_test()

    def force_replay_cache(self) -> None:
        """
        For all get_completion test cases, the cache_mode="REPLAY".
        """
        original_get_completion = hopenai.get_completion

        def replay_get_completion(**kwargs) :
            return original_get_completion(**kwargs, cache_mode="REPLAY")

        self.patcher = umock.patch.object(
            hopenai, "get_completion", replay_get_completion
        )
        self.patcher.start()

    def set_up_test(self) -> None:
        """
        Setup operations to run before each test:
        - adding dummy requests and responses in temporary cache file
        """
        request_parameters1 = _get_openai_request_parameters1()
        request_parameters3 = _get_openai_request_parameters3()
        dummy_openai_response1 = _get_dummy_openai_response1()
        dummy_openai_response2 = _get_dummy_openai_response2()
        # generating hash keys
        dummy_hash_key1 = self.get_completion_cache.hash_key_generator(
            **request_parameters1
        )
        dummy_hash_key2 = self.get_completion_cache.hash_key_generator(
            **request_parameters3
        )
        # saving dummy responses to cache
        self.get_completion_cache.save_response_to_cache(
            hash_key=dummy_hash_key1,
            request=request_parameters1,
            response=dummy_openai_response1,
        )
        self.get_completion_cache.save_response_to_cache(
            hash_key=dummy_hash_key2,
            request=request_parameters3,
            response=dummy_openai_response2,
        )

    def tear_down_test(self) -> None:
        """
        Teardown operations to run after each test:
            -  Remove cache files created on disk.
        """
        self.patcher.stop()
        if os.path.exists(_TEST_CACHE_FILE):
            os.remove(_TEST_CACHE_FILE)
        # if os.path.exists(self.cache_file):
        #     os.remove(self.cache_file)


# #############################################################################
# Test_get_completion
# #############################################################################


class Test_get_completion(_OpenAICacheTestCase):

    def test1(self) -> None:
        """
        Verify that get_completion() returns response from cache with the
        expected response.
        """
        parameters1 = _get_completion_parameters1()
        dummy_response1 = _get_dummy_openai_response1()
        response = hopenai.get_completion(
            **parameters1,
            cache_file=_TEST_CACHE_FILE,
            # cache_file=self.cache_file
        )
        self.assert_equal(
            dummy_response1["choices"][0]["message"]["content"], response
        )

    def test2(self) -> None:
        """
        Verify that if hashkey is not in response, then get_completion() should
        raise error in replay mode.
        """
        # parameters4 are not saved in test cache file
        parameters4 = _get_completion_parameters4()
        with self.assertRaises(RuntimeError) as RTE:
            hopenai.get_completion(**parameters4, cache_file=_TEST_CACHE_FILE)
        self.assert_equal(
            str(RTE.exception), "No cached response for this request parameters!"
        )


# #############################################################################
# Test_hash_key_generator
# #############################################################################


class Test_hash_key_generator(_OpenAICacheTestCase):

    def test_different_request_parameters1(self) -> None:
        """
        This test case check if normalisation works before generating hash key.
        """
        parameters1 = _get_openai_request_parameters1()
        parameters2 = _get_openai_request_parameters2()
        hash_key1 = self.get_completion_cache.hash_key_generator(**parameters1)
        hash_key2 = self.get_completion_cache.hash_key_generator(**parameters2)
        self.assert_equal(hash_key1, hash_key2)

    def test_different_request_parameters2(self) -> None:
        """
        Different Temperature should give different hashkeys.
        """
        parameters1 = _get_openai_request_parameters1()
        parameters3 = _get_openai_request_parameters3()
        hash_key1 = self.get_completion_cache.hash_key_generator(**parameters1)
        hash_key2 = self.get_completion_cache.hash_key_generator(**parameters3)
        self.assertNotEqual(hash_key1, hash_key2)

    def test_different_request_parameters3(self) -> None:
        """
        Different model should give different hashkeys.
        """
        parameters3 = _get_openai_request_parameters3()
        parameters4 = _get_openai_request_parameters4()
        hash_key3 = self.get_completion_cache.hash_key_generator(**parameters3)
        hash_key4 = self.get_completion_cache.hash_key_generator(**parameters4)
        self.assertNotEqual(hash_key3, hash_key4)


# #############################################################################
# Test_has_cache
# #############################################################################


class Test_has_cache(_OpenAICacheTestCase):

    def test1(self) -> None:
        """
        Should return False if cache doesn't exist.
        """
        # These parameters are not saved in the cache file.
        parameters4 = _get_openai_request_parameters4()
        hash_key4 = self.get_completion_cache.hash_key_generator(**parameters4)
        self.assertFalse(self.get_completion_cache.has_cache(hash_key=hash_key4))

    def test2(self) -> None:
        """
        Should return True if cache exists.
        """
        # These parameters are stored in the cache through Set up function
        parameters1 = _get_openai_request_parameters1()
        hash_key1 = self.get_completion_cache.hash_key_generator(**parameters1)
        self.assertTrue(self.get_completion_cache.has_cache(hash_key=hash_key1))


# #############################################################################
# Test_save_response_to_cache
# #############################################################################


class Test_save_response_to_cache(_OpenAICacheTestCase):

    def test1(self) -> None:
        """
        Verify if response saves into cache.
        """
        parameters4 = _get_openai_request_parameters4()
        dummy_response1 = _get_dummy_openai_response1()
        hash_key4 = self.get_completion_cache.hash_key_generator(**parameters4)
        self.get_completion_cache.save_response_to_cache(
            hash_key=hash_key4, request=parameters4, response=dummy_response1
        )
        self.assertEqual(
            dummy_response1["choices"][0]["message"]["content"],
            self.get_completion_cache.load_response_from_cache(
                hash_key=hash_key4
            ),
        )
        self.assertTrue(self.get_completion_cache.has_cache(hash_key=hash_key4))


# #############################################################################
# Test_load_response_from_cache
# #############################################################################


class Test_load_response_from_cache(_OpenAICacheTestCase):

    def test1(self) -> None:
        """
        Verify if stored response can be loaded.
        """
        # This response  saved in test cache through set up function.
        dummy_response1 = _get_dummy_openai_response1()
        # same parameters used to save the above response in test cache.
        parameters1 = _get_openai_request_parameters1()
        hash_key1 = self.get_completion_cache.hash_key_generator(**parameters1)
        self.assert_equal(
            dummy_response1["choices"][0]["message"]["content"],
            self.get_completion_cache.load_response_from_cache(
                hash_key=hash_key1
            ),
        )

    def test2(self) -> None:
        """
        Trying to load unsaved response from cache.
        """
        # These parameters are not stored in cache.s
        parameters4 = _get_openai_request_parameters4()
        hash_key4 = self.get_completion_cache.hash_key_generator(**parameters4)
        with self.assertRaises(ValueError) as VE:
            self.get_completion_cache.load_response_from_cache(hash_key=hash_key4)
        self.assert_equal(str(VE.exception), "No cache found!")


# #############################################################################
# Test_response_to_txt
# #############################################################################


class Test_response_to_txt(hunitest.TestCase):

    # --- Dummy classes to satisfy isinstance checks --- #
    class DummyChatCompletion:

        def __init__(self, text="") -> None:
            msg = types.SimpleNamespace(content=text)
            choice = types.SimpleNamespace(message=msg)
            self.choices = [choice]

    # class DummySyncCursorPage:
    #     def __init__(self, text=""):
    #         # mimic .data[0].content[0].text.value
    #         text_obj = types.SimpleNamespace(value=text)
    #         content_item = types.SimpleNamespace(text=text_obj)
    #         data_item = types.SimpleNamespace(content=[content_item])
    #         self.data = [data_item]

    class DummyThreadMessage:

        def __init__(self, text="") -> None:
            # mimic .content[0].text.value
            value_obj = types.SimpleNamespace(value=text)
            text_obj = types.SimpleNamespace(text=value_obj)
            self.content = [text_obj]

    @umock.patch(
        "openai.types.chat.chat_completion.ChatCompletion",
        new=DummyChatCompletion,
    )
    def test_chat_completion_branch(self) -> None:
        resp = Test_response_to_txt.DummyChatCompletion("hello chat")
        self.assert_equal(hopenai.response_to_txt(resp), "hello chat")

    # @umock.patch(
    #     "helpers.hopenai.openai.pagination.SyncCursorPage",
    #     new=DummySyncCursorPage,
    # )
    # def test_sync_cursor_page_branch(self):
    #     resp = TestResponseToTxt.DummySyncCursorPage("paged text")
    #     self.assertEqual(response_to_txt(resp), "paged text")

    @umock.patch(
        "openai.types.beta.threads.message.Message",
        new=DummyThreadMessage,
    )
    def test_thread_message_branch(self) -> None:
        resp = Test_response_to_txt.DummyThreadMessage("thread reply")
        self.assert_equal(hopenai.response_to_txt(resp), "thread reply")

    def test_str_pass_through(self) -> None:
        self.assert_equal(
            hopenai.response_to_txt("just a string"), "just a string"
        )

    def test_unknown_type_raises(self) -> None:
        with self.assertRaises(ValueError) as cm:
            hopenai.response_to_txt(12345)
        self.assertIn("Unknown response type", str(cm.exception))


# #############################################################################
# Test_extract
# #############################################################################


class Test_extract(hunitest.TestCase):

    def test_extract_existing_and_missing_attributes(self) -> None:
        """
        Check for exisiting elements.
        """
        # Only x and y exist on our object
        dummy_file = types.SimpleNamespace(x=10, y="hello")
        # "z" does NOT exist.
        attrs = ["x", "y", "z"]
        result = hopenai._extract(dummy_file, attrs)
        self.assert_equal(str(result), str({"x": 10, "y": "hello"}))

    def test_extract_no_attributes(self) -> None:
        """
        Asking for nothing always yields an empty dict.
        """
        dummy_file = types.SimpleNamespace(anything=123)
        result = hopenai._extract(dummy_file, [])
        self.assert_equal(str(result), str({}))

    def test_extract_all_missing_attributes(self) -> None:
        """
        Non existent attributes yield empty dict.
        """
        dummy_file = types.SimpleNamespace(foo="bar")
        result = hopenai._extract(dummy_file, ["a", "b", "c"])
        self.assert_equal(str(result), str({}))

    def test_extract_various_types(self) -> None:
        """
        Ensure arbitrary attribute types pass through.
        """
        inner = types.SimpleNamespace(inner_attr="value")
        dummy_file = types.SimpleNamespace(num=42, lst=[1, 2, 3], obj=inner)
        attrs = ["num", "lst", "obj"]
        result = hopenai._extract(dummy_file, attrs)
        self.assert_equal(str(result["lst"]), str([1, 2, 3]))
        # The exact same object should be returned
        self.assertIs(result["obj"], inner)


# #############################################################################
# Test_get_openai_client
# #############################################################################


class Test_get_openai_client(hunitest.TestCase):

    @umock.patch.dict(os.environ, {"OPENAI_API_KEY": "openai-key"})
    @umock.patch("openai.OpenAI")
    def test_openai_provider(self, mock_openai_cls) -> None:
        """
        Verify if get_openai_client() returns openai's url and API key.
        """
        client = hopenai.get_openai_client("openai")
        mock_openai_cls.assert_called_once_with(
            base_url="https://api.openai.com/v1",
            api_key="openai-key",
        )
        self.assertIs(client, mock_openai_cls.return_value)

    @umock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "router-key"})
    @umock.patch("openai.OpenAI")
    def test_openrouter_provider(self, mock_openai_cls) -> None:
        """
        Verify if get_openai_client() returns openrouter's url and API key.
        """
        client = hopenai.get_openai_client("openrouter")
        mock_openai_cls.assert_called_once_with(
            base_url="https://openrouter.ai/api/v1",
            api_key="router-key",
        )
        self.assertIs(client, mock_openai_cls.return_value)

    def test_unknown_provider_raises(self) -> None:
        """
        Verify exception if unknown provider given.
        """
        with self.assertRaises(ValueError) as cm:
            hopenai.get_openai_client("not_a_provider")
        self.assertIn("Unknown provider: not_a_provider", str(cm.exception))


# #############################################################################
# Test_get_default_model
# #############################################################################


class Test_get_default_model(hunitest.TestCase):

    def test_openai_provider(self) -> None:
        """
        Explicit "openai" provider return "gpt-4o".
        """
        self.assert_equal(hopenai._get_default_model("openai"), "gpt-4o")

    def test_openrouter_provider(self) -> None:
        """
        "openrouter" provider return "openai/gpt-4o".
        """
        self.assert_equal(
            hopenai._get_default_model("openrouter"), "openai/gpt-4o"
        )

    def test_default_argument(self) -> None:
        """
        Default provider name (should be "openai") return "gpt-4o".
        """
        self.assert_equal(hopenai._get_default_model(), "gpt-4o")

    def test_unknown_provider_raises(self) -> None:
        """
        Unknown provider should raise a ValueError.
        """
        with self.assertRaises(ValueError) as cm:
            hopenai._get_default_model("invalid_provider")
        self.assertIn("Unknown provider: invalid_provider", str(cm.exception))


# #############################################################################
# Test_retrieve_openrouter_model_info
# #############################################################################


class Test_retrieve_openrouter_model_info(hunitest.TestCase):

    @umock.patch("requests.get")
    def test_retrieve_success(self, mock_get) -> None:
        # Prepare dummy JSON data.
        data = [
            {"id": "model1", "name": "Model One"},
            {"id": "model2", "name": "Model Two"},
        ]
        mock_response = umock.Mock()
        mock_response.json.return_value = {"data": data}
        mock_get.return_value = mock_response
        # Call the function under test.
        df = hopenai._retrieve_openrouter_model_info()
        # Build expected DataFrame.
        expected_df = pd.DataFrame(data)
        # Verify DataFrame content.
        self.assertEqual(
            df.to_dict(orient="records"), expected_df.to_dict(orient="records")
        )
        # Ensure the correct URL was requested.
        mock_get.assert_called_once_with("https://openrouter.ai/api/v1/models")

    @umock.patch("requests.get")
    def test_missing_data_key_raises(self, mock_get) -> None:
        # JSON missing the 'data' key.
        mock_response = umock.Mock()
        mock_response.json.return_value = {"wrong": []}
        mock_get.return_value = mock_response
        # Expect an assertion from hdbg.dassert_eq.
        with self.assertRaises(AssertionError):
            hopenai._retrieve_openrouter_model_info()


# #############################################################################
# Test_save_models_info_to_csv
# #############################################################################


class Test_save_models_info_to_csv(hunitest.TestCase):

    def get_temp_path(self, tmp_file_name: str = "tmp.models_info.csv") -> str:
        """
        Helper function for creating temporary directory.
        """
        self.tmp_dir = self.get_scratch_space()
        self.tmp_path = os.path.join(self.tmp_dir, tmp_file_name)
        return self.tmp_path

    def test_save_models_info(self) -> None:
        """
        Save Dataframe as a CSV and check.
        """
        # Prepare a DataFrame with extra columns.
        data = [
            {
                "id": "m1",
                "name": "Model1",
                "description": "desc1",
                "pricing": {"prompt": "0.1", "completion": "0.2"},
                "supported_parameters": ["a", "b"],
                "extra_col": 123,
            },
            {
                "id": "m2",
                "name": "Model2",
                "description": "desc2",
                "pricing": {"prompt": "0.3", "completion": "0.4"},
                "supported_parameters": ["c"],
                "extra_col": 456,
            },
        ]
        df = pd.DataFrame(data)
        output_file: str = self.get_temp_path()
        # Call the function under test.
        returned_df = hopenai._save_models_info_to_csv(df, output_file)
        # The returned DataFrame should have only the selected columns.
        expected_columns = [
            "id",
            "name",
            "description",
            "prompt_pricing",
            "completion_pricing",
            "supported_parameters",
        ]
        assert list(returned_df.columns) == expected_columns
        # Verify pricing values are extracted correctly.
        self.assertListEqual(
            returned_df["prompt_pricing"].tolist(), ["0.1", "0.3"]
        )
        self.assertListEqual(
            returned_df["completion_pricing"].tolist(), ["0.2", "0.4"]
        )
        # File should be created and readable.
        assert os.path.exists(output_file)
        saved_df = pd.read_csv(output_file)
        # turn the in‐memory lists into exactly what pandas read back.
        returned_df["prompt_pricing"] = returned_df["prompt_pricing"].astype(
            float
        )
        returned_df["completion_pricing"] = returned_df[
            "completion_pricing"
        ].astype(float)
        returned_df["supported_parameters"] = returned_df[
            "supported_parameters"
        ].astype(str)
        pd.testing.assert_frame_equal(returned_df, saved_df)

    def test_invalid_filename_type(self) -> None:
        """
        Check with invalid filename.
        """
        df = pd.DataFrame()
        with pytest.raises(AssertionError):
            hopenai._save_models_info_to_csv(df, 123)

    def test_invalid_filename_empty(self) -> None:
        """
        Check with empty string as filename.
        """
        df = pd.DataFrame()
        with pytest.raises(AssertionError):
            hopenai._save_models_info_to_csv(df, "")


# #############################################################################
# Test_convert_to_type
# #############################################################################


class Test_convert_to_type(hunitest.TestCase):

    def test_convert_to_type_bool(self) -> None:
        """
        Check converting to bool column.
        """
        # Mix of booleans, truthy/falsy strings, numerics, and invalid values
        data = [True, False, "True", "false", 1, 0, "1", "0", "yes", None]
        series = pd.Series(data, dtype=object)
        result = hopenai.convert_to_type(series, "is_bool")
        expected = pd.Series(
            [True, True, True, True, True, True, True, True, False, False],
            dtype=bool,
        )
        pd.testing.assert_series_equal(result, expected)

    def test_convert_to_type_int_and_numeric(self) -> None:
        """
        Check converting to numeric and int column.
        """
        # Strings that parse to numbers, floats, invalid strings, and ints
        series = pd.Series(["1", "2", "3.5", "abc", 4], dtype=object)
        # is_int should coerce numeric strings to numbers, invalid -> NaN
        result_int = hopenai.convert_to_type(series, "is_int")
        expected_int = pd.to_numeric(series, errors="coerce")
        pd.testing.assert_series_equal(result_int, expected_int)
        # is_numeric is the same as to_numeric
        result_numeric = hopenai.convert_to_type(series, "is_numeric")
        pd.testing.assert_series_equal(result_numeric, expected_int)

    def test_convert_to_type_string(self) -> None:
        """
        Check converting to string column.
        """
        # Strings vs non-strings
        data = ["a", 1, None, "hello", True, 3.14]
        series = pd.Series(data, dtype=object)
        result = hopenai.convert_to_type(series, "is_string")
        expected = pd.Series([True, False, False, True, False, False], dtype=bool)
        pd.testing.assert_series_equal(result, expected)

    def test_convert_to_type_unknown(self) -> None:
        "Check converting to invalid datatype column."
        series = pd.Series([1, 2, 3], dtype=object)
        with pytest.raises(ValueError) as exc:
            hopenai.convert_to_type(series, "invalid_type")
        self.assertIn("Unknown column type: invalid_type", str(exc.value))


# #############################################################################
# Test_infer_column_types
# #############################################################################


class Test_infer_column_types(hunitest.TestCase):

    def test_numeric_dominance(self) -> None:
        """
        Check with numeric dominant column.
        """
        # 5 elements: '1','2',3 (numeric), 'a', None
        col = pd.Series(["1", "2", 3, "a", None], dtype=object)
        vals = hopenai.infer_column_types(col)
        # is_numeric: True for "1","2",3 → 3/5 = 0.6
        assert pytest.approx(vals["is_numeric"], rel=1e-6) == 0.6
        # is_bool: none are bool → 0.0
        assert vals["is_bool"] == 0.0
        # is_string: "1","2","a" are str → 3/5 = 0.6
        assert pytest.approx(vals["is_string"], rel=1e-6) == 0.6
        # numeric ≥ string, and bool < numeric ⇒ type is numeric
        self.assert_equal(vals["type"], "is_numeric")

    def test_bool_dominance(self) -> None:
        """
        Check with bool dominant column.
        """
        # 4 elements: True, False, True (bool), "x"
        col = pd.Series([True, False, True, "x"], dtype=object)
        vals = hopenai.infer_column_types(col)
        # is_bool: 3/4 = 0.75
        assert pytest.approx(vals["is_bool"], rel=1e-6) == 0.75
        # is_numeric: True→1, False→0, True→1, "x"→NaN  → notna → 3/4 = 0.75
        assert pytest.approx(vals["is_numeric"], rel=1e-6) == 0.75
        # is_string: only "x" → 1/4 = 0.25
        assert pytest.approx(vals["is_string"], rel=1e-6) == 0.25
        # bool ≥ numeric ⇒ type is bool
        self.assert_equal(vals["type"], "is_bool")

    def test_string_dominance(self) -> None:
        """
        Check with string dominant column.
        """
        # 3 elements: 1.5 (numeric), "a","b" (strings)
        col = pd.Series([1.5, "a", "b"], dtype=object)
        vals = hopenai.infer_column_types(col)
        # is_bool: none are bool → 0/3 = 0.0
        assert pytest.approx(vals["is_bool"], rel=1e-6) == 0.0
        # is_numeric: 1/3 ≈ 0.333...
        assert pytest.approx(vals["is_numeric"], rel=1e-6) == pytest.approx(
            1 / 3, rel=1e-6
        )
        # is_string: 2/3 ≈ 0.666...
        assert pytest.approx(vals["is_string"], rel=1e-6) == pytest.approx(
            2 / 3, rel=1e-6
        )
        # bool < numeric < string ⇒ type is string
        self.assert_equal(vals["type"], "is_string")


# #############################################################################
# Test_convert_df
# #############################################################################


class Test_convert_df(hunitest.TestCase):

    def test_convert_df_all_bool(self) -> None:
        """
        A column of pure booleans should stay booleans.
        """
        df = pd.DataFrame({"flag": [True, False, True, False]})
        df_out = hopenai.convert_df(df)
        # Expect a DataFrame back
        assert isinstance(df_out, pd.DataFrame)
        # Column dtype must be bool
        self.assert_equal(df_out["flag"].dtype.name, "bool")
        # Values preserved
        self.assert_equal(
            str(df_out["flag"].tolist()), str([True, False, True, False])
        )

    def test_convert_df_all_numeric(self) -> None:
        """
        A column of numeric strings and ints should become floats.
        """
        df = pd.DataFrame({"score": ["1", 2, "3.5", 4]}, dtype=object)
        df_out = hopenai.convert_df(df)
        assert isinstance(df_out, pd.DataFrame)
        # dtype should be float64
        assert df_out["score"].dtype == float
        # Values converted correctly
        assert df_out["score"].tolist() == [1.0, 2.0, 3.5, 4.0]

    def test_convert_df_all_string(self) -> None:
        """
        A column of strings (and mixed non-numeric non-bool) stays as-is.
        """
        df = pd.DataFrame({"name": ["alice", "bob", "", "charlie"]}, dtype=object)
        df_out = hopenai.convert_df(df)
        assert isinstance(df_out, pd.DataFrame)
        # dtype remains object (strings)
        self.assert_equal(df_out["name"].dtype.name, "object")
        self.assert_equal(
            str(df_out["name"].tolist()), str(["alice", "bob", "", "charlie"])
        )

    def test_convert_df_mixed_columns(self) -> None:
        """
        Different datatype columns should convert accordingly.
        """
        df = pd.DataFrame(
            {
                "flag": [True, False, False],
                "value": ["10", "20", "xyz"],
                "text": ["one", 2, None],
            },
            dtype=object,
        )
        df_out = hopenai.convert_df(df)
        # flag → bool
        self.assert_equal(df_out["flag"].dtype.name, "bool")
        self.assert_equal(str(df_out["flag"].tolist()), str([True, False, False]))
        # value → numeric (since 2/3 parse as numbers > bool(1/3) or string(0/3))
        self.assert_equal(df_out["value"].dtype.name, "float")
        # "10","20"→10.0,20.0; "xyz"→NaN
        assert pytest.approx(df_out["value"].tolist(), rel=1e-6) == [
            10.0,
            20.0,
            pytest.approx(float("nan")),
        ]
        # text → string (since 1/3 numeric < 1/3 string and bool=0)
        self.assert_equal(df_out["text"].dtype.name, "object")
        self.assert_equal(str(df_out["text"].tolist()), str(["one", 2, None]))


# #############################################################################
# Test_build_messages
# #############################################################################


# #############################################################################
# Test_build_messages
# #############################################################################
class Test_build_messages(hunitest.TestCase):

    def test_build_messages_returns_correct_structure(self) -> None:
        """
        Should return list with a certain format.
        """
        system = "System prompt"
        user = "User prompt"
        msgs = hopenai._build_messages(system, user)
        # Should be a list of two dicts with the right roles and contents
        self.assertIsInstance(msgs, list)
        self.assert_equal(
            str(msgs),
            str(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ]
            ),
        )


# #############################################################################
# Test_call_api_sync
# #############################################################################


class Test_call_api_sync(hunitest.TestCase):

    def test_call_api_sync_calls_client_and_returns_response(self) -> None:
        # Prepare mock completion object
        mock_content = "Hello from LLM"
        mock_message = umock.Mock()
        mock_message.content = mock_content
        mock_choice = umock.Mock(message=mock_message)
        mock_completion = umock.Mock(choices=[mock_choice])
        # Mock client with chat.completions.create
        mock_client = umock.Mock()
        mock_client.chat.completions.create.return_value = mock_completion
        # Test inputs
        messages = [{"role": "user", "content": "Hi"}]
        temperature = 0.5
        model = "gpt-test"
        extra_kwargs = {"foo": "bar"}
        # Call under test
        response, raw = hopenai._call_api_sync(
            mock_client,
            messages=messages,
            temperature=temperature,
            model=model,
            **extra_kwargs,
        )
        # Verify return values
        self.assert_equal(response, mock_content)
        self.assertIs(raw, mock_completion)
        # Verify the create() call was made with exactly the right arguments
        mock_client.chat.completions.create.assert_called_once_with(
            model=model,
            messages=messages,
            temperature=temperature,
            **extra_kwargs,
        )


# #############################################################################
# Test_calculate_cost
# #############################################################################


class Test_calculate_cost(hunitest.TestCase):

    def test_openai_cost(self) -> None:
        """
        Scenario: Known OpenAI model and token counts produce expected cost.
        """
        # TODO: implement test to assert correct cost calculation for OpenAI provider branch.

    def test_openai_unknown_model(self) -> None:
        """
        Scenario: Passing an unknown OpenAI model should raise an assertion or ValueError.
        """
        # TODO: implement test that unsupported model triggers appropriate error.

    def test_openrouter_download_and_save(self):
        """
        Scenario: No CSV file exists for OpenRouter; should retrieve model info, save CSV, then calculate cost.
        """
        # TODO: use pytest tmp_path to simulate missing file, patch retrieve and save, assert CSV creation and cost.

    def test_openrouter_load_existing_csv(self) -> None:
        """
        Scenario: CSV file exists for OpenRouter; should load CSV and calculate cost without fetching.
        """
        # TODO: write a sample CSV to tmp_path, patch os.path.isfile/read_csv, assert cost matches expected.

    def test_openrouter_missing_model(self) -> None:
        """
        Scenario: CSV exists but missing the requested model ID; should raise an assertion error.
        """
        # TODO: simulate CSV lacking the model row and assert that dassert_in triggers an error.

    def test_openrouter_invalid_csv(self) -> None:
        """
        Scenario: Existing CSV is malformed or unreadable; should raise a parsing or assertion error.
        """
        # TODO: simulate malformed CSV content and assert exception is raised.
