from typing import List, Dict, Any
import json

class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def Serialize(self) -> Dict[str, str]:
        return {'role': self.role, 'content': self.content}

    @staticmethod
    def Deserialize(data: Dict[str, Any]) -> 'Message':
        return Message(role=data['role'], content=data['content'])

class Conversation:
    def __init__(self):
        self.messages: List[Message] = []

    def Load(self, data: str) -> None:
        messages = json.loads(data)
        self.messages.extend(Message.Deserialize(message) for message in messages)

    def Save(self) -> str:
        return json.dumps([message.Serialize() for message in self.messages])

    def AddMessage(self, message: Message) -> None:
        self.messages.append(message)

    def GetMessagesList(self) -> List[Message]:
        return self.messages