# !interpreter [optional-arg]
# -*- coding: utf-8 -*-

import json
from locust import task, constant
from locust.contrib.fasthttp import FastHttpUser
from locust.env import Environment
import webbrowser


def getHeaders(token):
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "contentauditor_web",
    }
    return headers


def getPayload(query):
    payload = {
        "prompt": query
    }
    return payload


class LocustClient(FastHttpUser):
    host = "https://session-1fa78eee-f67e-422d-b062-d61c49e7e4c9.devbox.training.adobesensei.io/server"
    wait_time = constant(0)
    token = ""

    def __init__(self, environment):
        super().__init__(environment)

    def on_start(self):
        pass

    def on_stop(self):
        pass

    @task
    def testChatCompletions(self):
        headers = getHeaders(self.token)
        try:
            # Build your query parameter for GET API requests
            api = "/v1/generate"
            query = "How are you?"
            payload = json.dumps(getPayload(query))

            with self.client.post(self.host + api, headers=headers, catch_response=True, data=payload, name=api) as resp:
                if resp.status_code == 200:
                    body = resp.json()
                    if 'response' in body:
                        resp.success()
                    else:
                        resp.failure(resp.text)
                else:
                    resp.failure(resp.text)

        except Exception as e:
            print(f"Exception occurred! details are {e}")


if __name__ == "__main__":
    env = Environment(user_classes=[LocustClient])
    runner = env.create_local_runner()
    web_ui = env.create_web_ui("127.0.0.1", 8089)
    try:
        webbrowser.get(using=None).open("http://127.0.0.1:8089", new=2)
    except Exception as e:
        pass
    runner.start(20, spawn_rate=5)
    env.runner.greenlet.join()
    web_ui.stop()