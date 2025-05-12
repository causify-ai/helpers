import json
import logging
import os
import pickle
import pytest
from typing import Any, Dict

import pandas as pd
import pytest
import unittest.mock as umock

import helpers.hopenai as hopenai
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

_TEST_CACHE_FILE = "cache.test_get_completion.json"

_USER_PROMPT1 = "What is machine learning?"
_USER_PROMPT2 = _USER_PROMPT1.lower()
_USER_PROMPT3 = "What is artificial intelligence"

_SYSTEM_PROMPT1 ="You are a helpful AI assistant."
_SYSTEM_PROMPT2 ="You are a very helpful AI assistant."


_TEMPERATURE1 = 1
_TEMPERATURE2 = 2

_MODEL1="gpt-4o-mini"
_MODEL2="gpt-o4-mini"

def get_completion_paramters1():
    data =  { 
        "user_prompt": _USER_PROMPT1,
        "system_prompt": _SYSTEM_PROMPT1,
        "temperature":_TEMPERATURE1,
        "model":_MODEL1
    }
    return data



def get_openai_request_parameters1():
    messages = hopenai._construct_messages(user_prompt=_USER_PROMPT1, system_prompt=_SYSTEM_PROMPT1)
    data ={
        "messages":messages,
        "temperature":_TEMPERATURE1,
        "model" :_MODEL1}
    return data

def get_completion_paramters2():
    data =  { 
        "user_prompt": _USER_PROMPT2,
        "system_prompt": _SYSTEM_PROMPT1,
        "temperature":_TEMPERATURE1,
        "model":_MODEL1
    }
    return data

def get_openai_request_parameters2():
    messages = hopenai._construct_messages(user_prompt=_USER_PROMPT2, system_prompt=_SYSTEM_PROMPT1)
    data ={
        "messages":messages,
        "temperature":_TEMPERATURE1,
        "model" :_MODEL1}

    return data

def get_completion_paramters3():
    data =  { 
        "user_prompt": _USER_PROMPT1,
        "system_prompt": _SYSTEM_PROMPT1,
        "temperature":_TEMPERATURE2,
        "model":_MODEL1
    }
    return data

def get_openai_request_parameters3():
    messages = hopenai._construct_messages(user_prompt=_USER_PROMPT1, system_prompt=_SYSTEM_PROMPT1)
    data ={
        "messages":messages,
        "temperature":_TEMPERATURE2,
        "model" :_MODEL1}
    return data

def get_completion_paramters4():
    data =  { 
        "user_prompt": _USER_PROMPT1,
        "system_prompt": _SYSTEM_PROMPT1,
        "temperature":_TEMPERATURE2,
        "model":_MODEL2
    }
    return data

def get_openai_request_parameters4():
    messages = hopenai._construct_messages(user_prompt=_USER_PROMPT1, system_prompt=_SYSTEM_PROMPT1)
    data ={
        "messages":messages,
        "temperature":_TEMPERATURE2,
        "model" :_MODEL2}
    return data


def get_dummy_openai_response1():
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
                        Instead, these systems learn from and make predictions or decisions based on data."""
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 5,
            "completion_tokens": 4,
            "total_tokens": 9
        }
    }
    return response


def get_dummy_openai_response2():
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
                    "content": """Artificial Intelligence (AI) is the field of computer science focused on creating systems or machines 
                                that can perform tasks typically requiring human intelligence. These tasks include:
                                •	Perception: Recognizing images, speech, or patterns (e.g., facial recognition, voice assistants).
                                •	Reasoning and Decision-Making: Solving problems and making decisions (e.g., self-driving cars deciding when to stop or accelerate).
                                •	Learning: Improving performance from experience (e.g., recommendation systems like Netflix or Amazon).
                                •	Natural Language Understanding: Interacting using human language (e.g., chatbots, language translation).
                                •	Action: Controlling devices or robots to perform tasks (e.g., industrial automation, drones)."""
                            },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 200,
            "total_tokens": 215
        }
    }


############################################################################

#############################################################################

class BaseOpenAICacheTest(hunitest.TestCase):
    """
   
    """
    @pytest.fixture(autouse=True)
    def setup_teardown_test(self):
        #Patch get_completion to inject REPLAY
        self.force_replay_cache()
        # Run common setuo for each test
        self.set_up_test()
        yield
        # Run common teardown after the test.
        self.tear_down_test()


    def force_replay_cache(self):
        """
        For all get_completion test cases, the cache_mode="REPLAY".
        """
        original_get_completion = hopenai.get_completion

        def replay_get_completion(**kwargs):
            return original_get_completion(**kwargs, cache_mode="REPLAY" )
        
        self.patcher =umock.patch.object(hopenai, "get_completion", replay_get_completion)
        self.patcher.start()

    def set_up_test(self)-> None:
        """
        Setup Operations to run before each test:
        - adding dummy requests and responses in temporary cache file
        """
        
        test_cache  = hopenai.OpenAICache(cache_file=_TEST_CACHE_FILE)

        request_parameters1 = get_openai_request_parameters1()
        request_parameters3 = get_openai_request_parameters3()

        dummy_openai_response1 = get_dummy_openai_response1()
        dummy_openai_response2 = get_dummy_openai_response2()

        # generating hash keys
        dummy_hash_key1 = test_cache.hash_key_generator(**request_parameters1)
        dummy_hash_key2 = test_cache.hash_key_generator(**request_parameters3)

        #saving dummy responses to cache
        test_cache.save_response_to_cache(hash_key=dummy_hash_key1, request=request_parameters1, response=dummy_openai_response1)
        test_cache.save_response_to_cache(hash_key=dummy_hash_key2, request=request_parameters3, response=dummy_openai_response2)

    def tear_down_test(self):
        """
        Teardown operations to run after each test:
            -  Remove cache files created on disk.
        """
        self.patcher.stop()
        if os.path.exists(_TEST_CACHE_FILE):
            os.remove(_TEST_CACHE_FILE)


# #############################################################################
# Test_get_completion
# #############################################################################

class Test_get_completion(BaseOpenAICacheTest):

    def test1(self):
        """
        Verify that get_completion returns response from cache with the expected response.
        """

        parameters1 = get_completion_paramters1()
        dummy_response1= get_dummy_openai_response1()
        response =hopenai.get_completion(**parameters1, cache_file=_TEST_CACHE_FILE)

        self.assertEqual(dummy_response1["choices"][0]["message"]["content"], response)
    
    def test2(self):
        """
        Verify that if hashkey is not in response, then get_completion should raise error in replay mode.
        """
        # parameters4 are not saved in test cache file
        paramters4 = get_completion_paramters4()

        with self.assertRaises(RuntimeError) as RTE:
            hopenai.get_completion(**paramters4, cache_file=_TEST_CACHE_FILE)

        self.assertEqual(str(RTE.exception), "No cached response for this request parameters!")

    


# #############################################################################
# OpenAICache's hash key generator tests
# #############################################################################


class Test_hash_key_generator(BaseOpenAICacheTest):

    def test_different_request_parameters1(self):
        """
        This test case checks if normalisation works before generating hash key
        """
        parameters1= get_openai_request_parameters1()
        parameters2 = get_openai_request_parameters2()

        openai_cache = hopenai.OpenAICache(_TEST_CACHE_FILE)
        hash_key1= openai_cache.hash_key_generator(**parameters1)
        hash_key2 = openai_cache.hash_key_generator(**parameters2)

        self.assertEqual(hash_key1, hash_key2)

    def test_different_request_parameters2(self):
        """
        Different Temperatures should give different hashkeys.
        """
        parameters1= get_openai_request_parameters1()
        parameters3 = get_openai_request_parameters3()

        openai_cache = hopenai.OpenAICache(_TEST_CACHE_FILE)
        hash_key1= openai_cache.hash_key_generator(**parameters1)
        hash_key2 = openai_cache.hash_key_generator(**parameters3)

        self.assertNotEqual(hash_key1, hash_key2)

    def test_different_request_parameters3(self):
        """
        Different models should give different hashkeys.
        """
        parameters3= get_openai_request_parameters3()
        parameters4 = get_openai_request_parameters4()

        openai_cache = hopenai.OpenAICache(_TEST_CACHE_FILE)
        hash_key3= openai_cache.hash_key_generator(**parameters3)
        hash_key4 = openai_cache.hash_key_generator(**parameters4)

        self.assertNotEqual(hash_key3, hash_key4)

    









    











    


   
    






