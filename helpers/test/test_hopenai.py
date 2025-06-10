import logging
import unittest.mock as umock

import pytest

pytest.importorskip(
    "openai"
)  # noqa: E402 # pylint: disable=wrong-import-position

import helpers.hopenai as hopenai
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

# Shared cache file.
_CACHE_FILE = "cache.get_completion.json"
_TEMP_CACHE_FILE = "tmp.cache.get_completion.json"

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
    data = {
        "messages": messages,
        "temperature": _TEMPERATURE1,
        "model": _MODEL1,
    }
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
    data = {
        "messages": messages,
        "temperature": _TEMPERATURE1,
        "model": _MODEL1,
    }
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
    data = {
        "messages": messages,
        "temperature": _TEMPERATURE2,
        "model": _MODEL1,
    }
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
    data = {
        "messages": messages,
        "temperature": _TEMPERATURE2,
        "model": _MODEL2,
    }
    return data


# #############################################################################
# BaseOpenAICacheTest
# #############################################################################


# TODO(*): Rename _OpenAICacheTestCase
class BaseOpenAICacheTest(hunitest.TestCase):
    """
    - Ensure hopenai.get_completion() always uses REPLAY mode.
    - Uses shared cache("cache.get_completion.json")
    - if "--update_llm_cache" is passed in pytest command, cache file will be updated automatically.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self, pytestconfig):
        # Creating hopeani._CompletionCache instance.
        self.get_completion_cache = hopenai._CompletionCache(
            cache_file=_CACHE_FILE
        )
        # TODO(Sai) : This should be removed once "openai" module not found error is fixed.
        if pytestconfig.getoption("--update_llm_cache"):
            hopenai.set_update_llm_cache(True)
        # Patch get_completion to inject REPLAY.
        self.force_replay_cache()
        yield
        # Run common teardown after the test.
        self.tear_down_test()

    def force_replay_cache(self) -> None:
        """
        For all get_completion test cases, the cache_mode="REPLAY".
        """
        original_get_completion = hopenai.get_completion

        def replay_get_completion(**kwargs):
            return original_get_completion(**kwargs, cache_mode="REPLAY")

        self.patcher = umock.patch.object(
            hopenai, "get_completion", replay_get_completion
        )
        self.patcher.start()

    def tear_down_test(self) -> None:
        """
        Teardown operations to run after each test:
            -  Stop the patcher.
        """
        self.patcher.stop()


# #############################################################################
# Test_get_completion
# #############################################################################


class Test_get_completion(BaseOpenAICacheTest):

    def test1(self) -> None:
        """
        Verify that get_completion() returns response from cache with the
        expected response.
        """
        parameters1 = _get_completion_parameters1()
        actual_response = hopenai.get_completion(**parameters1)
        # generate hash key
        hash_key = self.get_completion_cache.hash_key_generator(
            **_get_openai_request_parameters1()
        )
        # load the response from cache.
        expected_response = self.get_completion_cache.load_response_from_cache(
            hash_key=hash_key
        )
        self.assert_equal(actual_response, expected_response)

    def test2(self) -> None:
        """
        Verify whether prompts with different capitalizations produce the same
        result.
        """
        parameters2 = _get_completion_parameters2()
        actual_response = hopenai.get_completion(**parameters2)
        # generate hash key
        hash_key = self.get_completion_cache.hash_key_generator(
            **_get_openai_request_parameters1()
        )
        # load the response from cache.
        expected_response = self.get_completion_cache.load_response_from_cache(
            hash_key=hash_key
        )
        self.assert_equal(actual_response, expected_response)

    def test3(self) -> None:
        """
        Verify if different parameters result in different results.
        """
        parameters1 = _get_completion_parameters1()
        parameters3 = _get_completion_parameters3()
        actual_response1 = hopenai.get_completion(**parameters1)
        actual_response3 = hopenai.get_completion(**parameters3)
        # generate hash keys
        hashkey1 = self.get_completion_cache.hash_key_generator(
            **_get_openai_request_parameters1()
        )
        hashkey3 = self.get_completion_cache.hash_key_generator(
            **_get_openai_request_parameters3()
        )
        # Load responses from cache.
        expected_response1 = self.get_completion_cache.load_response_from_cache(
            hash_key=hashkey1
        )
        expected_response3 = self.get_completion_cache.load_response_from_cache(
            hash_key=hashkey3
        )
        self.assert_equal(actual_response1, expected_response1)
        self.assert_equal(actual_response3, expected_response3)
        # Different parameters should give different results.
        self.assertNotEqual(actual_response1, actual_response3)

    # TODO(Sai): Tobe done after fixing hopenai.get_completion()
    def test4(self) -> None:
        """
        Verify if openrouter models are supported.
        """
        assert True


# #############################################################################
# Test_hash_key_generator
# #############################################################################


class Test_hash_key_generator(BaseOpenAICacheTest):

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


class Test_has_cache(BaseOpenAICacheTest):

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


class Test_save_response_to_cache(BaseOpenAICacheTest):

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


class Test_load_response_from_cache(BaseOpenAICacheTest):

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
