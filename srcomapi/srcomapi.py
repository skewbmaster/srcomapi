from urllib import response
import requests
from http.client import responses
from os.path import dirname
from os import environ
import inspect

import srcomapi
import srcomapi.datatypes as datatypes
from .exceptions import APIRequestException, APINotProvidedException

# libraries for mocking
import json
import gzip

with open(dirname(srcomapi.__file__) + "/.version") as f:
    __version__ = f.read().strip()
API_URL = "https://www.speedrun.com/api/v1/"
TEST_DATA = dirname(srcomapi.__file__) + "/test_data/"

class SpeedrunCom(object):
    def __init__(self, api_key=None, user_agent="blha303:srcomapi/"+__version__, mock=False):
        self._datatypes = {v.endpoint:v for k,v in inspect.getmembers(datatypes, inspect.isclass) if hasattr(v, "endpoint")}
        self.api_key = api_key
        self.user_agent = user_agent
        self.mock = mock
        self.debug = 0

    def get(self, endpoint, **kwargs):
        headers = {"User-Agent": self.user_agent}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        kwargs.update({"headers": headers})
        uri = API_URL + endpoint
        if self.debug >= 1: print(uri)
        if self.mock:
            mock_endpoint = ".".join(endpoint.split("/")[0::2])
            try:
                with gzip.open(TEST_DATA + mock_endpoint + ".json.gz") as f:
                    data = json.loads(f.read().decode("utf-8"))["data"]
            except FileNotFoundError:
                response = requests.get(uri, **kwargs)
                if response.status_code != 404:
                    with gzip.open(TEST_DATA + mock_endpoint + ".json.gz", "wb") as f:
                        f.write(json.dumps(response.json()).encode("utf-8"))
                    data = response.json()["data"]
                else:
                    raise APIRequestException((response.status_code, responses[response.status_code], uri[len(API_URL):]), response)
        else:
            response = requests.get(uri, **kwargs)
            if response.status_code == 404:
                raise APIRequestException((response.status_code, responses[response.status_code], uri[len(API_URL):]), response)
            data = response.json()["data"]
        return data

    def post(self, endpoint, data, **kwargs):
        headers = {"User-Agent": self.user_agent}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        kwargs.update({"headers": headers})
        uri = API_URL + endpoint
        if self.debug >= 1: print(uri)

        if self.mock:
            # Implement if needed
            data = None

        else:
            response = requests.post(uri, data=data **kwargs)
            if response.status_code != 201:
                raise APIRequestException((response.status_code, responses[response.status_code], uri[len(API_URL):]), response)

            data = response.json()["data"]

        return data



    def get_game(self, id, **kwargs):
        return datatypes.Game(self, data=self.get("games/" + id))

    def get_games(self, **kwargs):
        """ Legacy function, will be removed in next major version"""
        return self.search(datatypes.Game, **kwargs)

    def get_user(self, id, **kwargs):
        return datatypes.User(self, data=self.get("users/" + id))

    def search(self, datatype, params):
        """Returns a generator that uses the given datatype and search params to get results"""
        response = self.get(datatype.endpoint, params=params)
        return [datatype(self, data=data) for data in response]

    def submit_run(self, times_obj, variables_obj, players_array, category, level = None, run_date = None, region = None, platform = None, video_link = None, comment = None, splitsio = None, emulated = False, verified = False):
        """Sends a POST HTTP request with parameters given to this function, """
        if not self.api_key:
            return "No API Key Provided"

        rundata = { "run" : {} }

        rundata["run"]["category"] = category.id
        
        rundata["run"]["times"] = times_obj
        rundata["run"]["variables"] = variables_obj

        if players_array != None:
            rundata["run"]["players"] = players_array

        if level:
            rundata["run"]["level"] = level.id

        if region:
            rundata["run"]["region"] = region.id

        if platform:
            rundata["run"]["platform"] = platform.id

        if run_date:
            rundata["run"]["date"] = run_date

        if video_link:
            rundata["run"]["video"] = video_link

        if comment:
            rundata["run"]["comment"] = comment

        if splitsio:
            rundata["run"]["splitsio"] = splitsio

        if emulated:
            rundata["run"]["emulated"] = True

        if verified:
            rundata["run"]["verified"] = True

        response = self.post(datatypes.Run.endpoint, rundata)


    def create_players_obj(self, *players):
        players_obj = []

        for i, player in enumerate(players):
            players_obj[i] = {
                "rel" : player.role,
                "id" : player.id
            }

        return players_obj

    def create_variables_obj(self, *variable_tuples):
        variables_obj = {}

        for vartup in variable_tuples:
            variables_obj[vartup[0].id] = {
                "type" : "user_defined" if vartup[0].user_defined else "pre-defined",
                "value" : vartup[1]
            }
        
        return variables_obj
