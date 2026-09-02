# AI Use Disclosure - DATA-260 Homework 2

## 1. What I used an AI assistant for and what I did myself

I used an AI assistant for step-by-step explanations, code structure suggestions, debugging guidance, and help understanding the Homework 2 requirements.

I personally created and edited the files, ran the commands in Terminal, installed the required packages, tested the FastAPI endpoints, ran the browser tests, collected screenshots, and reviewed the experiment results.

## 2. One AI-produced output that was wrong or unsuitable

During the FastAPI setup, the HTTPException import became `from http.client import HTTPException`.

This was unsuitable because the application needs FastAPI's HTTPException, not Python's standard-library HTTPException.

## 3. How I detected the problem

I reviewed the import section in VS Code and checked the application behavior while starting and testing the FastAPI server. The incorrect import was identified during code review before continuing with the backend routes.

I also independently verified the application by running Uvicorn and sending curl requests to the API.

## 4. What I changed and why it works now

I replaced the incorrect import with `from fastapi import FastAPI, HTTPException`.

The FastAPI server then started correctly on port 8004, and the add, update, delete, and search requests returned the expected results.