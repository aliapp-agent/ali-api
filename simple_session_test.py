import asyncio
import httpx
import json

async def test_session_persistence():
    base_url = "http://localhost:8081"
    
    # 1. Register
    import uuid
    unique_email = f"test_session_{str(uuid.uuid4())[:8]}@example.com"
    register_data = {"email": unique_email, "password": "Test123!@#"}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{base_url}/api/v1/auth/register", json=register_data)
        register_result = response.json()
        print(f"Register: {response.status_code} - {register_result}")
        
        if response.status_code != 200:
            return
            
        user_token = register_result["token"]["access_token"]
        
        # 2. Create Session
        headers = {"Authorization": f"Bearer {user_token}"}
        response = await client.post(f"{base_url}/api/v1/auth/session", headers=headers)
        session_result = response.json()
        print(f"Create Session: {response.status_code} - {session_result}")
        
        if response.status_code != 200:
            return
            
        session_token = session_result["token"]["access_token"]
        session_id = session_result["session_id"]
        
        # 3. Test using session token
        session_headers = {"Authorization": f"Bearer {session_token}"}
        response = await client.post(
            f"{base_url}/api/v1/chatbot/chat", 
            headers=session_headers,
            json={"messages": [{"role": "user", "content": "Hello"}]}
        )
        chat_result = response.json()
        print(f"Chat Test: {response.status_code} - {chat_result}")

if __name__ == "__main__":
    asyncio.run(test_session_persistence())
