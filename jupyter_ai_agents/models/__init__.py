# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Jupyter AI Agents model package.

The following json schema describes the data model used in cells and notebook metadata to communicate between user clients and an Jupyter AI Agent.

```json
{
  "datalayer": {
    "type": "object",
    "properties": {
      "ai": {
        "type": "object",
        "properties": {
          "prompts": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": {
                  "title": "Prompt unique identifier",
                  "type": "string"
                },
                "prompt": {
                  "title": "User prompt",
                  "type": "string"
                },
                "username": {
                  "title": "Unique identifier of the user making the prompt.",
                  "type": "string"
                },
                "timestamp": {
                  "title": "Number of milliseconds elapsed since the epoch; i.e. January 1st, 1970 at midnight UTC.",
                  "type": "integer"
                }
              },
              "required": ["id", "prompt"]
            }
          },
          "messages": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "parent_id": {
                  "title": "Prompt unique identifier",
                  "type": "string"
                },
                "message": {
                  "title": "AI reply",
                  "type": "string"
                },
                "type": {
                  "title": "Type message",
                  "enum": [0, 1, 2]
                },
                "timestamp": {
                  "title": "Number of milliseconds elapsed since the epoch; i.e. January 1st, 1970 at midnight UTC.",
                  "type": "integer"
                }
              },
              "required": ["id", "prompt"]
            }
          }
        }
      }
    }
  }
}
```
    

""" 