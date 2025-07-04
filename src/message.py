from typing import List, Dict, Any, Optional, NamedTuple
from datetime import datetime, timezone

from agent_command import CommandInput, CommandOutput


class ContentSection(NamedTuple):
  content: str
  command: Optional[CommandInput] = None
  command_output: Optional[CommandOutput] = None
  summary: Optional[str] = None


class Message:

  def __init__(self,
               role: str,
               content_sections: Optional[List[ContentSection]] = None,
               creation_time: Optional[datetime] = None):
    self.role = role
    self._content_sections: List[
        ContentSection] = content_sections if content_sections is not None else []
    self.creation_time = creation_time or datetime.now(timezone.utc)

  def Serialize(self) -> Dict[str, Any]:
    serialized_sections = []
    for section in self._content_sections:
      section_dict: Dict[str, Any] = {'content': section.content}
      if section.summary is not None:
        section_dict['summary'] = section.summary
      if section.command is not None:
        section_dict['command'] = str(section.command)
      if section.command_output is not None:
        section_dict['command_output'] = str(section.command_output)
      serialized_sections.append(section_dict)
    return {
        'role': self.role,
        'content_sections': serialized_sections,
        'creation_time': self.creation_time.isoformat()
    }

  def ToPropertiesDict(self) -> Dict[str, Any]:
    serialized_sections = []
    for section in self._content_sections:
      section_dict: Dict[str, Any] = {'content': section.content}
      if section.summary is not None:
        section_dict['summary'] = section.summary
      if section.command is not None:
        command_dict = {
            'command_name': section.command.command_name,
        }
        for key, value in section.command.args.items():
            command_dict[key] = str(value)
        section_dict['command'] = command_dict
      if section.command_output is not None:
        section_dict['command_output'] = {
            'command_name': section.command_output.command_name,
            'output': str(section.command_output.output),
            'errors': str(section.command_output.errors),
            'summary': str(section.command_output.summary),
            'task_done': str(section.command_output.task_done)
        }
      serialized_sections.append(section_dict)
    return {
        'role': self.role,
        'content_sections': serialized_sections,
        'creation_time': self.creation_time.isoformat()
    }

  @staticmethod
  def Deserialize(data: Dict[str, Any]) -> 'Message':
    content_sections: List[ContentSection] = []
    raw_sections = data.get('content_sections', [])
    for section_data in raw_sections:
      content_sections.append(
          ContentSection(
              content="".join(section_data.get('content', [])),
              summary=section_data.get('summary')))
    return Message(
        role=data['role'],
        content_sections=content_sections,
        creation_time=datetime.fromisoformat(data['creation_time']))

  def GetContentSections(self) -> List[ContentSection]:
    return self._content_sections

  def PushSection(self, section: ContentSection) -> None:
    self._content_sections.append(section)
