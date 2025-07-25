import asyncio
import argparse
import logging
import socketio
import uvicorn
from typing import Any, Dict
from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from pathlib import Path

from args_common import CreateCommonParser
from conversation import ConversationId
from web_server_state import create_web_server_state, WebServerState
from random_key import GenerateRandomKey

app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi')
sio_app = socketio.ASGIApp(sio)

app.mount("/socket.io", sio_app)

current_script_dir = Path(__file__).parent.resolve()
app.mount(
    "/static",
    StaticFiles(directory=current_script_dir / "static"),
    name="static")


def parse_arguments() -> argparse.Namespace:
  parser = CreateCommonParser()
  parser.add_argument(
      '--port', type=int, default=5000, help="Port to run the web server on.")
  return parser.parse_args()


@app.get("/")
async def read_root() -> FileResponse:
  return FileResponse(current_script_dir / "static/index.html")


async def send_update(server_state: WebServerState, data: Dict[str,
                                                               Any]) -> None:
  message_count = data.get('message_count', 0)
  conversation_id = data.get('conversation_id')
  if conversation_id is None:
    logging.error("SendUpdate: conversation_id is missing")
    return

  logging.info(f"Received: request_update, message_count: {message_count}")
  await server_state.send_update(
      conversation_id, message_count, confirmation_required=None)


async def main() -> None:
  args = parse_arguments()
  server_state = await create_web_server_state(args, sio)

  @sio.on('confirm')  # type: ignore[misc]
  async def handle_confirmation(sid: str, data: Dict[str, Any]) -> None:
    logging.info("Received: confirm.")
    confirmation = data.get('confirmation')
    conversation_id = data.get('conversation_id')
    if confirmation is None:
      logging.error("handle_confirmation: confirmation is missing")
      return
    if conversation_id is None:
      logging.error("handle_confirmation: conversation_id is missing")
      return
    server_state.ReceiveConfirmation(confirmation, conversation_id)
    await send_update(server_state, data)

  @sio.on('request_update')  # type: ignore[misc]
  async def start_update(sid: str, data: Dict[str, Any]) -> None:
    await send_update(server_state, data)

  @sio.on('list_conversations')  # type: ignore[misc]
  async def list_conversations(sid: str) -> None:
    logging.info("Received: list_conversations request")
    await server_state.list_conversations()

  server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=args.port))
  await asyncio.gather(server.serve(), server_state.wait_for_background_tasks())


if __name__ == "__main__":
  asyncio.run(main())
