#!/usr/bin/env python
"""
基础WebSocket客户端示例
"""
import asyncio
import json
import websockets
import sys
import uuid


async def test_websocket_connection():
    """测试WebSocket连接"""
    uri = "ws://localhost:8765/ws"

    try:
        # 连接到WebSocket服务器
        async with websockets.connect(uri) as websocket:
            print(f"已连接到 {uri}")

            # 创建测试令牌（在实际使用中应由服务器生成）
            test_token = "test_token_123"
            auth_message = {"token": test_token}

            # 发送认证消息
            await websocket.send(json.dumps(auth_message))
            print(f"已发送认证消息: {auth_message}")

            # 接收认证响应
            response = await websocket.recv()
            print(f"收到认证响应: {response}")

            # 测试流式消息
            print("\n=== 测试流式消息 ===")
            stream_request = {
                "type": "stream",
                "prompt": "你好，请介绍一下WebSocket的优点。",
                "model": "mock"
            }
            await websocket.send(json.dumps(stream_request))
            print(f"已发送流式请求: {stream_request}")

            # 接收流式响应
            print("等待流式响应...")
            try:
                async for message in websocket:
                    data = json.loads(message)
                    if data.get("type") == "stream":
                        print(f"收到流式分块: {data}")
                        if data.get("is_complete"):
                            print("流式响应完成")
                            break
            except Exception as e:
                print(f"接收流式响应时出错: {e}")

            # 测试聊天消息
            print("\n=== 测试聊天消息 ===")
            chat_request = {
                "type": "chat",
                "content": "你好，这是测试消息。",
                "room_id": "test_room"
            }
            await websocket.send(json.dumps(chat_request))
            print(f"已发送聊天请求: {chat_request}")

            response = await websocket.recv()
            print(f"收到聊天响应: {response}")

            # 测试状态查询
            print("\n=== 测试状态查询 ===")
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            status_request = {
                "type": "status",
                "task_id": task_id,
                "action": "query"
            }
            await websocket.send(json.dumps(status_request))
            print(f"已发送状态请求: {status_request}")

            response = await websocket.recv()
            print(f"收到状态响应: {response}")

            print("\n=== 测试完成 ===")

    except ConnectionRefusedError:
        print(f"无法连接到 {uri}，请确保服务器正在运行")
        return False
    except Exception as e:
        print(f"连接错误: {e}")
        return False

    return True


async def main():
    """主函数"""
    print("=== x-websocket 客户端测试 ===")

    # 测试连接
    success = await test_websocket_connection()

    if success:
        print("\n测试成功！")
    else:
        print("\n测试失败！")


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())