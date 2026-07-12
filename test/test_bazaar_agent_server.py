"""
Test the BazaarQuery A2A agent server.
Run after starting bazaar_server.py
"""
import asyncio
import uuid
from python_a2a import A2AClient, Message, TextContent, MessageRole, Task


async def main():
    client = A2AClient("http://localhost:5006")

    message = Message(
        content=TextContent(text="User: 帮我找龙息药剂"),
        role=MessageRole.USER,
    )
    task = Task(id="task-" + str(uuid.uuid4()), message=message.to_dict())

    try:
        result = await client.send_task_async(task)
        print(f"State: {result.status.state}")
        if result.status.state == "completed":
            print(f"Result:\n{result.artifacts[0]['parts'][0]['text']}")
        else:
            print(f"Message: {result.status.message['content']['text']}")
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
