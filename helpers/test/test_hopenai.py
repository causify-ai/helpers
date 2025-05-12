import json
import logging
import os
import pickle
import pytest
from typing import Any, Dict

import pandas as pd
import pytest

import helpers.hopenai as hopenai
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)

_USER_PROMPT1 = "What is machine learning?"
_USER_PROMPT2 = _USER_PROMPT1.lower()
_USER_PROMPT3 = "What is artificial intelligence"

_SYSTEM_PROMPT1 ="You are a helpful AI assistant."
_SYSTEM_PROMPT2 ="You are not so helpful AI assistant."


_TEMPERATURE1 = 1
_TEMPERATURE2 =2

_MODEL1="gpt-4o-mini"
_MODEL2="gpt-o4-mini"



def get_request_parameters1():

    messages = hopenai._construct_messages(user_prompt=_USER_PROMPT1, system_prompt=_SYSTEM_PROMPT1)
    data ={
        "messages":messages,
        "temperature":_TEMPERATURE1,
        "model" :_MODEL1}
    return data

def get_request_parameters2():
    messages = hopenai._construct_messages(user_prompt=_USER_PROMPT2, system_prompt=_SYSTEM_PROMPT1)
    data ={
        "messages":messages,
        "temperature":_TEMPERATURE1,
        "model" :_MODEL1}

    return data


def get_request_parameters3():
    messages = hopenai._construct_messages(user_prompt=_USER_PROMPT1, system_prompt=_SYSTEM_PROMPT1)
    data ={
        "messages":messages,
        "temperature":_TEMPERATURE2,
        "model" :_MODEL1}
    return data

def get_request_parameters4():
    messages = hopenai._construct_messages(user_prompt=_USER_PROMPT1, system_prompt=_SYSTEM_PROMPT1)
    data ={
        "messages":messages,
        "temperature":_TEMPERATURE2,
        "model" :_MODEL2}
    return data






class Test_hash_key_generator(hunitest.TestCase):

    def test_different_request_parameters1(self):
        """
        This test case checks if normalisation works before generating hash key
        """
        parameters1= get_request_parameters1()
        parameters2 = get_request_parameters2()

        openai_cache = hopenai.OpenAICache()
        hash_key1= openai_cache.hash_key_generator(**parameters1)
        hash_key2 = openai_cache.hash_key_generator(**parameters2)

        self.assertEqual(hash_key1, hash_key2)

    def test_different_request_parameters2(self):
        """
        Different Temperatures should give different hashkeys.
        """
        parameters1= get_request_parameters1()
        parameters3 = get_request_parameters3()

        openai_cache = hopenai.OpenAICache()
        hash_key1= openai_cache.hash_key_generator(**parameters1)
        hash_key2 = openai_cache.hash_key_generator(**parameters3)

        self.assertNotEqual(hash_key1, hash_key2)

    def test_different_request_parameters3(self):
        """
        Different models should give different hashkeys.
        """
        parameters3= get_request_parameters3()
        parameters4 = get_request_parameters4()

        openai_cache = hopenai.OpenAICache()
        hash_key3= openai_cache.hash_key_generator(**parameters3)
        hash_key4 = openai_cache.hash_key_generator(**parameters4)

        self.assertNotEqual(hash_key3, hash_key4)

    
 ############################################################################

#############################################################################

class BaseOpenAICacheTest(hunitest.TestCase):
    """
    This pytest fixture ensures hopenai.get_completion uses replay mode while 
    testing to prevent openai calls.
    """
    @pytest.fixture(autouse=True)
    def force_replay_cache(monkeypatch):
        """
        For all get_completion test cases, the cache_mode="REPLAY".
        """
        original_get_completion = hopenai.get_completion

        def replay_get_completion(**kwargs):
            return original_get_completion(cache_mode="REPLAY", **kwargs)
        
        monkeypatch.setattr(hopenai, "get_completion", replay_get_completion)

        yield

    











    


   
    






