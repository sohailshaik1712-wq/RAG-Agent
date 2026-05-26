import asyncio
import json

import httpx

BASE_URL = "https://rag-backend-128608771917.us-central1.run.app"


async def test_system():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login
        print(f"Attempting login for sohailsk1107@gmail.com...")
        login_data = {"email": "sohailsk1107@gmail.com", "password": "Shaiksohail@1107"}
        # Try JSON
        res = await client.post(f"{BASE_URL}/auth/login", json=login_data)

        if res.status_code != 200:
            print(f"Login failed: {res.status_code} - {res.text}")
            # If login fails, try to register
            print("Attempting registration...")
            reg_data = {
                "email": "sohailsk1107@gmail.com",
                "username": "sohail1107",
                "password": "Shaiksohail@1107",
            }
            res = await client.post(f"{BASE_URL}/auth/register", json=reg_data)
            print(f"Registration result: {res.status_code} - {res.text}")
            # Try login again after registration
            res = await client.post(f"{BASE_URL}/auth/login", json=login_data)

        if res.status_code == 200:
            tokens = res.json()
            access_token = tokens["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            print("Login successful!")

            # 2. List Conversations
            res = await client.get(f"{BASE_URL}/conversations/", headers=headers)
            print(f"Conversations: {res.status_code}")

            # 3. Create a conversation if none exist
            convs = res.json()
            if not convs:
                res = await client.post(
                    f"{BASE_URL}/conversations/",
                    json={"title": "Test Cloud RAG"},
                    headers=headers,
                )
                conv = res.json()
            else:
                conv = convs[0]

            conv_id = conv["id"]
            print(f"Using conversation: {conv_id}")

            # 4. Try to chat (this might fail if no docs are uploaded, but let's check the response)
            chat_data = {"message": "Hello, can you see my documents?"}
            # The chat endpoint likely uses streaming or a different path,
            # let's try the standard chat endpoint
            print("Sending test message...")
            res = await client.post(
                f"{BASE_URL}/chat/{conv_id}", json=chat_data, headers=headers
            )
            print(f"Chat response ({res.status_code}): {res.text[:200]}...")

        else:
            print("Could not proceed without authentication.")


if __name__ == "__main__":
    asyncio.run(test_system())
