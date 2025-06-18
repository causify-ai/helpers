import os
import types
import unittest.mock as umock
from typing import Any, Dict

import pandas as pd
import pytest

pytest.importorskip(
    "openai"
)  # noqa: E402 # pylint: disable=wrong-import-position
import helpers.hdbg as hdbg
import helpers.hllm as hllm
import helpers.hunit_test as hunitest

# cache file used for storing llm responses.
_TEST_CACHE_FILE = "cache.get_completion.json"


_USER_PROMPT1 = "what is machine learning?"
_USER_PROMPT2 = _USER_PROMPT1.upper()

_SYSTEM_PROMPT1 = "You are a helpful AI assistant."
_SYSTEM_PROMPT2 = (
    "You are a helpful AI assistant and excellent in explaining things."
)

_TEMPERATURE1 = 0.1
_TEMPERATURE2 = 0.2

_TOP_P1 = 0.5

_MODEL1 = "gpt-4o-mini"
_MODEL2 = "gpt-3.5-turbo"
_MODEL3 = "deepseek/deepseek-r1-0528-qwen3-8b:free/"


# Test functions for the unit tests.
def _get_completion_parameters1() -> Dict[str, Any]:
    data = {
        "user_prompt": _USER_PROMPT1,
        "system_prompt": _SYSTEM_PROMPT1,
        "temperature": _TEMPERATURE1,
        "model": _MODEL1,
    }
    return data


def _get_openai_request_parameters1() -> Dict[str, Any]:
    messages = hllm._build_messages(
        user_prompt=_USER_PROMPT1, system_prompt=_SYSTEM_PROMPT1
    )
    data = {"messages": messages, "temperature": _TEMPERATURE1, "model": _MODEL1}
    return data


def _get_completion_parameters2() -> Dict[str, Any]:
    data = {
        "user_prompt": _USER_PROMPT2,
        "system_prompt": _SYSTEM_PROMPT2,
        "temperature": _TEMPERATURE2,
        "model": _MODEL2,
        "top_p": _TOP_P1,
    }
    return data


def _get_openai_request_parameters2() -> Dict[str, Any]:
    messages = hllm._build_messages(
        user_prompt=_USER_PROMPT2, system_prompt=_SYSTEM_PROMPT2
    )
    data = {
        "messages": messages,
        "temperature": _TEMPERATURE2,
        "model": _MODEL2,
        "top_p": _TOP_P1,
    }
    return data


def _get_completion_parameters3() -> Dict[str, Any]:
    data = {
        "user_prompt": _USER_PROMPT2,
        "system_prompt": _SYSTEM_PROMPT2,
        "temperature": _TEMPERATURE2,
        "model": _MODEL3,
        "top_p": _TOP_P1,
    }
    return data


def _get_openai_request_parameters3() -> Dict[str, Any]:
    messages = hllm._build_messages(
        user_prompt=_USER_PROMPT2, system_prompt=_SYSTEM_PROMPT2
    )
    data = {
        "messages": messages,
        "temperature": _TEMPERATURE2,
        "model": _MODEL3,
        "top_p": _TOP_P1,
    }
    return data


# #############################################################################
# Test_get_completion
# #############################################################################


class Test_get_completion(hunitest.TestCase):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the cache instance.
        """
        super().__init__(*args, **kwargs)
        self.llm_cache = hllm._CompletionCache(cache_file=_TEST_CACHE_FILE)

    def test1(self) -> None:
        """
        Verify that get_completion() returns response from cache with the
        expected response.
        """
        parameters1 = _get_completion_parameters1()
        actual_response = hllm.get_completion(
            **parameters1, cache_mode="HIT_CACHE_OR_ABORT"
        )
        openai_request_parameters1 = _get_openai_request_parameters1()
        hash_key1 = self.llm_cache.hash_key_generator(
            **openai_request_parameters1
        )
        expected_response = self.llm_cache.load_response_from_cache(hash_key1)
        self.assert_equal(actual_response, expected_response)
        self.assertIsInstance(actual_response, str)

    def test2(self) -> None:
        """
        Verify with different openai models.
        """
        parameters2 = _get_completion_parameters2()
        actual_response = hllm.get_completion(
            **parameters2, cache_mode="HIT_CACHE_OR_ABORT"
        )
        openai_request_parameters2 = _get_openai_request_parameters2()
        hash_key2 = self.llm_cache.hash_key_generator(
            **openai_request_parameters2
        )
        expected_response = self.llm_cache.load_response_from_cache(
            hash_key=hash_key2
        )
        self.assert_equal(actual_response, expected_response)
        self.assertIsInstance(actual_response, str)

    def test3(self) -> None:
        """
        Verify if hllm.get_completion() support openrouter models.
        """
        parameters3 = _get_completion_parameters3()
        actual_response = hllm.get_completion(
            **parameters3, cache_mode="HIT_CACHE_OR_ABORT"
        )
        openai_request_parameters3 = _get_openai_request_parameters3()
        hash_key3 = self.llm_cache.hash_key_generator(
            **openai_request_parameters3
        )
        expected_response = self.llm_cache.load_response_from_cache(
            hash_key=hash_key3
        )
        self.assert_equal(actual_response, expected_response)
        self.assertIsInstance(actual_response, str)


# #############################################################################
# Test_response_to_txt
# #############################################################################


class Test_response_to_txt(hunitest.TestCase):

    # Dummy classes to satisfy `isinstance` checks.

    class DummyChatCompletion:

        def __init__(self, text: str = "") -> None:
            msg = types.SimpleNamespace(content=text)
            choice = types.SimpleNamespace(message=msg)
            self.choices = [choice]

    class DummyThreadMessage:

        def __init__(self, text: str = "") -> None:
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
        act = hllm.response_to_txt(resp)
        exp = "hello chat"
        self.assert_equal(act, exp)

    @umock.patch(
        "openai.types.beta.threads.message.Message",
        new=DummyThreadMessage,
    )
    def test_thread_message_branch(self) -> None:
        resp = Test_response_to_txt.DummyThreadMessage("thread reply")
        act = hllm.response_to_txt(resp)
        exp = "thread reply"
        self.assert_equal(act, exp)

    def test_str_pass_through(self) -> None:
        act = hllm.response_to_txt("just a string")
        exp = "just a string"
        self.assert_equal(act, exp)

    def test_unknown_type_raises(self) -> None:
        with self.assertRaises(ValueError) as cm:
            hllm.response_to_txt(12345)
        self.assertIn("Unknown response type", str(cm.exception))


# #############################################################################
# Test_get_openai_client
# #############################################################################


class Test_get_openai_client(hunitest.TestCase):

    @umock.patch.dict(os.environ, {"OPENAI_API_KEY": "openai-key"})
    @umock.patch("openai.OpenAI")
    def test_openai_provider(self, mock_openai_cls) -> None:
        """
        Verify that `get_openai_client()` returns OpenAI's URL and API key.
        """
        client = hllm.get_openai_client("openai")
        mock_openai_cls.assert_called_once_with(
            base_url="https://api.openai.com/v1",
            api_key="openai-key",
        )
        self.assertIs(client, mock_openai_cls.return_value)

    @umock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "router-key"})
    @umock.patch("openai.OpenAI")
    def test_openrouter_provider(self, mock_openai_cls) -> None:
        """
        Verify that `get_openai_client()` returns OpenRouter's URL and API key.
        """
        client = hllm.get_openai_client("openrouter")
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
            hllm.get_openai_client("not_a_provider")
        self.assertIn("Unknown provider: not_a_provider", str(cm.exception))


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
        df = hllm._retrieve_openrouter_model_info()
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
            hllm._retrieve_openrouter_model_info()


# #############################################################################
# Test_save_models_info_to_csv
# #############################################################################


class Test_save_models_info_to_csv(hunitest.TestCase):

    def get_temp_path(self) -> str:
        """
        Helper function for creating temporary directory.
        """
        self.tmp_dir = self.get_scratch_space()
        tmp_file_name = "tmp.models_info.csv"
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
                "pricing": {"prompt": 0.1, "completion": 0.2},
                "supported_parameters": ["a", "b"],
                "extra_col": 123,
            },
            {
                "id": "m2",
                "name": "Model2",
                "description": "desc2",
                "pricing": {"prompt": 0.3, "completion": 0.4},
                "supported_parameters": ["c"],
                "extra_col": 456,
            },
        ]
        df = pd.DataFrame(data)
        output_file: str = self.get_temp_path()
        # Call the function under test.
        returned_df = hllm._save_models_info_to_csv(df, output_file)
        # The returned DataFrame should have only the selected columns.
        expected_columns = [
            "id",
            "name",
            "description",
            "prompt_pricing",
            "completion_pricing",
            "supported_parameters",
        ]
        hdbg.dassert_eq(list(returned_df.columns), expected_columns)
        # Verify pricing values are extracted correctly.
        self.assert_equal(
            str(returned_df["prompt_pricing"]),
            str(pd.Series([0.1, 0.3], name="prompt_pricing", dtype=float)),
        )
        self.assert_equal(
            str(returned_df["completion_pricing"]),
            str(pd.Series([0.2, 0.4], name="completion_pricing", dtype=float)),
        )
        # File should be created and readable.
        hdbg.dassert_file_exists(output_file)
        saved_df = pd.read_csv(output_file)
        self.assert_equal(
            str(returned_df["completion_pricing"]),
            str(saved_df["completion_pricing"]),
        )
        self.assert_equal(
            str(returned_df["prompt_pricing"]), str(saved_df["prompt_pricing"])
        )


# #############################################################################
# Test_calculate_cost
# #############################################################################


class Test_calculate_cost(hunitest.TestCase):

    def get_tmp_path(self) -> str:
        """
        Return temporary file path.
        """
        self.tmp_dir = self.get_scratch_space()
        tmp_file_name: str = "tmp.models_info.csv"
        self.tmp_path = os.path.join(self.tmp_dir, tmp_file_name)
        return self.tmp_path

    def test_openai_cost(self) -> None:
        """
        Known OpenAI model and token counts produce expected cost.
        """
        comp = types.SimpleNamespace(
            usage=types.SimpleNamespace(
                prompt_tokens=1000000, completion_tokens=2000000
            )
        )
        cost = hllm._calculate_cost(
            comp, model="gpt-3.5-turbo", models_info_file=""
        )
        # 1000000*(0.5/1000000) + 20000000*(1.5/1000000) = 3.5
        self.assertAlmostEqual(cost, 3.5)

    def test_openai_unknown_model(self) -> None:
        """
        Passing an unknown OpenAI model should raise an assertion or
        ValueError.
        """
        comp = types.SimpleNamespace(
            usage=types.SimpleNamespace(prompt_tokens=1, completion_tokens=1)
        )
        with pytest.raises(AssertionError):
            hllm._calculate_cost(
                comp, model="nonexistent-model", models_info_file=""
            )

    def test_openrouter_load_existing_csv(self) -> None:
        """
        Assume that the CSV file exists for OpenRouter.

        Then we should load CSV and calculate cost without fetching.
        """
        # Write a tiny CSV: id,prompt_pricing,completion_pricing
        temp_csv_file = self.get_tmp_path()
        pd.DataFrame(
            {
                "id": ["m1"],
                "prompt_pricing": [0.1],
                "completion_pricing": [0.2],
            }
        ).to_csv(temp_csv_file, index=False)
        comp = types.SimpleNamespace(
            usage=types.SimpleNamespace(prompt_tokens=1, completion_tokens=1)
        )
        cost = hllm._calculate_cost(
            comp,
            model="m1",
            models_info_file=temp_csv_file,
            provider_name="openrouter",
        )
        # 1*0.1 + 1*0.2 = 0.1 + 0.2 = 0.3
        self.assertAlmostEqual(cost, 0.3)
