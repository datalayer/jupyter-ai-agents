# Copyright (c) 2021-2024 Datalayer, Inc.
#
# Datalayer License

import json

from jupyter_server.base.handlers import APIHandler

from jupyter_ai_agents.server.agents import AIAgentsManager


MANAGER = None


class AIAgentHandler(APIHandler):

#    @web.authenticated
    async def get(self, matched_part=None, *args, **kwargs):
        global MANAGER
        if MANAGER is None:
            MANAGER = AIAgentsManager()
        print('------------------', matched_part)
        self.write({
            "success": True,
            "matched_part": matched_part,
        })

#    @web.authenticated
    async def post(self, matched_part=None, *args, **kwargs):
        global MANAGER
        if MANAGER is None:
            MANAGER = AIAgentsManager()
        body_data = json.loads(self.request.body)
        print(body_data)
        self.write({
            "success": True,
            "matched_part": matched_part,
        })


class AIAgentsHandler(APIHandler):

#    @web.authenticated
    async def get(self, *args, **kwargs):
        global MANAGER
        if MANAGER is None:
            MANAGER = AIAgentsManager()
        self.write({
            "success": True,
        })

#    @web.authenticated
    async def post(self, *args, **kwargs):
        global MANAGER
        if MANAGER is None:
            MANAGER = AIAgentsManager()
        body_data = json.loads(self.request.body)
        print(body_data)
        self.write({
            "success": True,
        })
