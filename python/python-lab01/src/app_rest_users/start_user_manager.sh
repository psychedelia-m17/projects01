#!/bin/bash

uvicorn src.app_rest_users.user_manager:app --host 0.0.0.0 --port 8000
