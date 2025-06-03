import logging
import os
import unittest.mock as umock

import pytest

pytest.importorskip("openai")  # noqa: E402 # pylint: disable=wrong-import-position

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
        "usage": {
            "prompt_tokens": 5,
            "completion_tokens": 4,
            "total_tokens": 9,
        },
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
# BaseOpenAICacheTest
# #############################################################################


# TODO(*): Rename _OpenAICacheTestCase
class BaseOpenAICacheTest(hunitest.TestCase):
    """
    - Ensure hopenai.get_completion() always uses REPLAY mode.
    - Add dummy data to the test cache file for test cases.
    - Remove the test cache file after running tests.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown_test(self):
        # Using test cache file to prevent ruining the actual cache file.
        # TODO(Sai): Reuse get_scratch_space().
        # self.cache_file = self.get_scratch_space()+f"/{_TEST_CACHE_FILE}"
        self.get_completion_cache = hopenai.CompletionCache(
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

        def replay_get_completion(**kwargs):
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


class Test_get_completion(BaseOpenAICacheTest):
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
            str(RTE.exception),
            "No cached response for this request parameters!",
        )


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
        Verifies if response saves into cache.
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
        Verifies if stored response can be loaded.
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
            self.get_completion_cache.load_response_from_cache(
                hash_key=hash_key4
            )
        self.assert_equal(str(VE.exception), "No cache found!")
