import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as Client:
        login_user_1 = await Client.post("/login", data={"username": "string", "password": "stringst"})
        print(login_user_1.status_code)

        responses = await asyncio.gather(
            Client.post("/chats/direct", json={"user_id": 2}),
            Client.post("/chats/direct", json={"user_id": 2}),
        )

        for resp in responses:
            print(resp.status_code)

asyncio.run(main())

