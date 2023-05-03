import os
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union
import copy
import openai

HAS_TIKTOKEN = True
try:
  import tiktoken
except ImportError:
  HAS_TIKTOKEN = False

# get the openai api key from OPENAI_API_KEY env var
# api_key = os.getenv('OPENAI_API_KEY')
# if not api_key:
#   errmsg = \
# f'''The OPENAI_API_KEY environment variable is not set. Please set it to your OpenAI API key.
# You can get your API key from https://platform.openai.com/account/api-keys'''
#   raise ValueError(errmsg)
# openai.api_key = api_key
# del api_key  # keep things secure in the module



DEFAULT_ID = str(uuid.UUID(int=0))
DEFAULT_TIME = 0


class Message:
  """Message class for the GPT AI"""
  _role: str
  @property
  def role(self) -> str:
    """Role of the message, either assistant, user or system"""
    return self._role
  @role.setter
  def role(self, value: str):
    if not isinstance(value, str): raise TypeError("role must be a string")
    self._role = value

  _content: str
  @property
  def content(self) -> str:
    """Content of the message"""
    return self._content
  @content.setter
  def content(self, value: str):
    if not isinstance(value, str): raise TypeError("content must be a string")
    self._content = value

  _id: str
  @property
  def id(self) -> str:
    """Unique ID for the message"""
    return self._id
  @id.setter
  def id(self, value: str):
    if not isinstance(value, str): raise TypeError("id must be a string")
    self._id = value

  _created: int
  @property
  def created(self) -> int:
    """Timestamp of when the message was created, in seconds since the epoch"""
    return self._created
  @created.setter
  def created(self, value: int):
    if not isinstance(value, int): raise TypeError("created must be an integer")
    self._created = value

  def __init__(self, role: str, content: str, id: str = DEFAULT_ID, created: int = DEFAULT_TIME):
    """Message class for the GPT AI

    Args:
      role (str): Role of the message, either assistant, user or system
      content (str): Content of the message
      id (str = gpt.DEFAULT_ID): Unique ID for the message. Should be uuid or some other unique identifier
      created (int = gpt.DEFAULT_TIME): Timestamp of when the message was created, in seconds since the epoch
    """
    self.role = role
    self.content = content
    self.id = id
    self.created = created

  @staticmethod
  def Default() -> 'Message':
    """Returns a default initialized message."""
    return Message(role='', content='', id=DEFAULT_ID, created=0)

  def isDefault(self):
    """Returns True if the message is default initialized, False otherwise."""
    return self.role == "" and self.content == "" and self.id == DEFAULT_ID and self.created == DEFAULT_TIME

  def toApiMessage(self) -> Dict[str, str]:
    """Converts the message to an API message dict. Formatted as {"role": "...", "content": "..."}"""
    return {
      "role": self.role,
      "content": self.content
    }

  def toMessage(self) -> 'Message':
    """Returns a Message from this object."""
    return self

  @staticmethod
  def FromApiMessage(apiMessage: Dict[str, Any]) -> Optional['Message']:
    """Creates a Message from a message dict, or returns None if the message is invalid.

    Args:
      apiMessage: The message dict to create a Message from.
    """
    if "role" not in apiMessage or "content" not in apiMessage: return None
    role = apiMessage["role"]
    content = apiMessage["content"]
    if not isinstance(role, str) or not isinstance(content, str): return None
    return Message(role=role, content=content)

  @staticmethod
  def FromApiResponse(apiResponse: Dict[str, Any]) -> Optional['Message']:
    """Creates a Message from a response dict, or returns None if the response is invalid.

    Args:
      apiResponse: The response dict to create a Message from.
    """
    if "choices" not in apiResponse or "id" not in apiResponse or "created" not in apiResponse:
      return None
    choices: List[Dict[str, Any]] = apiResponse["choices"]
    id: str = apiResponse["id"]
    created: int = apiResponse["created"]
    if not isinstance(id, str) or not isinstance(choices, list) or not isinstance(created, int):
      return None
    if len(choices) == 0: return None
    choice: dict = choices[0]
    if not isinstance(choice, dict): return None
    if "message" not in choice and "delta" not in choice: return None
    isDelta = "delta" in choice
    message = choice["message"] if not isDelta else choice["delta"]  # TODO: hacky
    if not isinstance(message, dict): return None
    if "content" not in message: return None
    if not isDelta and "role" not in message: return None
    role = message["role"] if not isDelta else "assistant"
    content = message["content"]
    return Message(role=role, content=content, id=id, created=created)

  def copy(self) -> 'Message':
    """Returns a copy of the message."""
    return copy.deepcopy(self)


class PartialMessage(Message):
  """Used when a ChatCompletion is set to 'stream'. Linked list of message fragments."""
  _prev: Optional['PartialMessage']
  @property
  def prev(self) -> Optional['PartialMessage']:
    """The previous message fragment"""
    return self._prev

  _next: Optional['PartialMessage']
  @property
  def next(self) -> Optional['PartialMessage']:
    """The next message fragment"""
    return self._next

  _first: 'PartialMessage'
  @property
  def first(self) -> 'PartialMessage':
    """The first message fragment in the linked list"""
    return self._first

  _idx: int = field(init=False, default=0)

  def __init__(self, role: str, content: str, id: str = DEFAULT_ID, created: int = DEFAULT_TIME, prev: Optional['PartialMessage'] = None):
    super().__init__(role=role, content=content, id=id, created=created)
    self._prev = None
    self._next = None
    self._first = self
    self._idx = 0
    if prev is not None:
      self._prev = prev
      self._first = prev._first
      self._idx = prev._idx + 1
      prev._next = self

  def toMessage(self):
    content = ''
    partial = self.first
    while partial is not None:
      content += partial.content
      partial = partial.next
    return Message(role=self.role, content=content, id=self.id, created=self.created)

  def toApiMessage(self) -> Dict[str, str]:
    return {
      "role": self.role,
      "content": self.toMessage().content
    }

  @staticmethod
  def FromApiResponse(apiResponse: Dict[str, Any], previous: Optional['PartialMessage'] = None) -> Optional['PartialMessage']:
    """Creates a PartialMessage from a response dict, or returns None if the response is invalid.

    Args:
      apiResponse: The response dict to create a PartialMessage from.
    """
    if "choices" not in apiResponse or "id" not in apiResponse or "created" not in apiResponse:
      return None
    id: str = apiResponse["id"]
    choices: List[Dict[str, Any]] = apiResponse["choices"]
    created: int = apiResponse["created"]
    if not isinstance(id, str) or not isinstance(choices, list) or not isinstance(created, int):
      return None
    if len(choices) == 0: return None
    choice: dict = choices[0]
    if not isinstance(choice, dict): return None
    if "delta" not in choice: return None
    message: dict = choice["delta"]
    if not isinstance(message, dict): return None
    if "content" not in message: return None
    role = "assistant"
    content = message["content"]
    return PartialMessage(role=role, content=content, id=id, created=created, prev=previous)

  @staticmethod
  def FromApiResponses(apiResponses: List[Dict[str, Any]]) -> Optional['PartialMessage']:
    """Creates a PartialMessage from a list of response dicts, or returns None if the responses are invalid.

    Args:
      apiResponses: The response dicts to create a PartialMessage from.
    """
    if len(apiResponses) == 0: return None
    first: Optional[PartialMessage] = None
    prev: Optional[PartialMessage] = None
    for response in apiResponses:
      message = PartialMessage.FromApiResponse(response, prev)
      if message is None: return None
      if first is None: first = message
      if prev is not None: prev._next = message
      prev = message
    return first


def messageFromApiResponse(apiResponseOrResponses: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Optional[Union[Message, PartialMessage]]:
  """Creates a Message or PartialMessage from a response dict or list of response dicts, or returns None if the response(s) are invalid.

  Args:
    apiResponseOrResponses: The response dict(s) to create a Message or PartialMessage from.
  """
  if isinstance(apiResponseOrResponses, dict):
    return Message.FromApiResponse(apiResponseOrResponses)
  elif isinstance(apiResponseOrResponses, list):
    return PartialMessage.FromApiResponses(apiResponseOrResponses)


@dataclass
class Usage:
  prompt_tokens: int = 0
  """Number of tokens used for the prompt"""
  completion_tokens: int = 0
  """Number of tokens used for the completion"""
  total_tokens: int = 0
  """Total number of tokens used"""

  def __post_init__(self):
    if not isinstance(self.prompt_tokens, int): raise TypeError("prompt_tokens must be an integer")
    if not isinstance(self.completion_tokens, int): raise TypeError("completion_tokens must be an integer")
    if not isinstance(self.total_tokens, int): raise TypeError("total_tokens must be an integer")

  def isDefault(self) -> bool:
    return self.prompt_tokens == 0 and self.completion_tokens == 0 and self.total_tokens == 0

  def toApiUsage(self) -> Dict[str, Any]:
    return {
      "prompt_tokens": self.prompt_tokens,
      "completion_tokens": self.completion_tokens,
      "total_tokens": self.total_tokens
    }

  @staticmethod
  def FromApiResponse(apiResponse: Dict[str, Any]) -> Optional['Usage']:
    """Creates a Usage from a response dict, or returns None if the response is invalid.

    Args:
      apiResponse: The response dict to create a Usage from.
    """
    if "prompt_tokens" not in apiResponse or "completion_tokens" not in apiResponse or "total_tokens" not in apiResponse:
      return None
    prompt_tokens, completion_tokens, total_tokens = apiResponse["prompt_tokens"], apiResponse["completion_tokens"], apiResponse["total_tokens"]
    if not isinstance(prompt_tokens, int) or not isinstance(completion_tokens, int) or not isinstance(total_tokens, int):
      return None
    return Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=total_tokens)



class Response:
  """Response class for the GPT AI"""
  choices: List[Union[Message, PartialMessage]]
  """List of choices for the response"""
  created: int
  """Timestamp of when the response was created, in seconds since the epoch"""
  id: str
  """Unique ID for the response"""
  model: str
  """The model used to generate the response"""
  object_: str
  """The response object type, e.g. 'chat.completion' or 'chat.completion.chunk"""
  usage: Usage
  """Usage statistics for the response"""

  def __init__(self, choices: List[Union[Message, PartialMessage]], created: int, id: str, model: str, object_: str, usage: Usage = Usage()):
    self.choices = choices
    self.created = created
    self.id = id
    self.model = model
    self.object_ = object_
    self.usage = usage

  def toApiResponse(self) -> Dict[str, Any]:
    ret = {
      "choices": [msg.toApiMessage() for msg in self.choices],
      "created": self.created,
      "id": self.id,
      "model": self.model,
      "object": self.object_,
    }
    if not self.usage.isDefault():
      ret["usage"] = self.usage.toApiUsage()
    return ret

  def isDefault(self):
    return self.choices == [] and self.created == 0 and self.id == "" and self.model == "" and self.object_ == "" and self.usage.isDefault()

  @staticmethod
  def Default() -> 'Response':
    return Response(choices=[], created=0, id="", model="", object_="", usage=Usage())

  @staticmethod
  def FromApiResponse(apiResponse: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Optional['Response']:
    """Creates a Response from a response dict, or returns None if the response is invalid.

    Args:
      apiResponse: The response dict to create a Response from.
    """
    def parseResponse(resp):
      if "choices" not in apiResponse or "id" not in apiResponse or "created" not in apiResponse or "model" not in apiResponse or "object" not in apiResponse:
        return None
      choicesApi: List[Dict[str, Any]] = apiResponse["choices"]
      idApi: str = apiResponse["id"]
      createdApi: int = apiResponse["created"]
      modelApi: str = apiResponse["model"]
      objectApi: str = apiResponse["object"]
      usageApi: Optional[Dict[str, Any]] = apiResponse.get("usage", None)
      if not isinstance(choicesApi, list) or not isinstance(idApi, str) or not isinstance(createdApi, int) or not isinstance(modelApi, str) or not isinstance(objectApi, str):
        return None
      if usageApi and not isinstance(usageApi, dict):
        return None
      choices = []
      for choice in choicesApi:
        message = messageFromApiResponse(apiResponse)
        if message is None: return None
        choices.append(message)
      usage: Usage = Usage()
      if usageApi:
        usage = Usage.FromApiResponse(usageApi) or Usage()
      return Response(choices=choices, created=createdApi, id=idApi, model=modelApi, object_=objectApi, usage=usage)
    if isinstance(apiResponse, dict):
      return parseResponse(apiResponse)
    elif isinstance(apiResponse, list):
      if len(apiResponse) == 0: return None
      return parseResponse(apiResponse[0])

  @staticmethod
  def FromApiResponses(apiResponses: List[Dict[str, Any]]) -> Optional['Response']:
    """Creates a singular Response from a list of streamed responses, or returns None if the responses are invalid.

    Args:
      apiResponses: The list of response dicts to create Responses from.
    """
    if len(apiResponses) == 0: return None
    if len(apiResponses) == 1: return Response.FromApiResponse(apiResponses[0])
    resp = Response.FromApiResponse(apiResponses[0])
    if resp is None: return None
    message = messageFromApiResponse(apiResponses)
    if message is None: return None
    resp.choices = [message.toMessage()]
    return resp

class ChatEntry:
  """An entry in the chat history. A new entry is created each time the user creates or edits a prompt.
  Each entry contains a reference to the previous entry and a list of child entries.
  """
  _parent: Optional['ChatEntry']
  @property
  def parent(self) -> Optional['ChatEntry']:
    """The parent entry, or None if this is the root entry"""
    return self._parent

  _children: List['ChatEntry']
  @property
  def children(self) -> List['ChatEntry']:
    """The child entries"""
    return self._children

  _prompt: Message
  @property
  def prompt(self) -> Message:
    """The prompt message"""
    return self._prompt

  _response: Response
  @property
  def response(self) -> Response:
    """The response"""
    return self._response
  @response.setter
  def response(self, value: Response):
    self._response = value

  def __init__(self, prompt: Message, response: Response = Response.Default(), parent: Optional['ChatEntry'] = None):
    self._prompt = prompt
    self._response = response
    self._parent = parent
    self._children = []
    if self._parent:
      self._parent._children.append(self)

  def index(self) -> int:
    """Returns the index of this entry in the parent's children list, or 0 if this is the root entry."""
    if self._parent is None: return 0
    return self._parent._children.index(self)

  def isRoot(self) -> bool:
    """Returns True if this is the root entry, False otherwise."""
    return self._parent is None

  def isLeaf(self) -> bool:
    """Returns True if this is a leaf entry, False otherwise."""
    return len(self._children) == 0

  def isDefaultContent(self) -> bool:
    """Returns True if this entry contains the default content, False otherwise."""
    return self._prompt.isDefault() and self._response.isDefault()

  def path(self) -> List['ChatEntry']:
    """Returns the path to this entry."""
    path = []
    entry: Optional[ChatEntry] = self
    while entry is not None:
      path.append(entry)
      entry = entry._parent
    path.reverse()
    return path

  def messages(self) -> List[Message]:
    """Returns a list of all messages up to and including this entry."""
    path = self.path()
    messages = []
    for i, entry in enumerate(path):
      if i == 0 and entry.isDefaultContent(): continue # skip default content
      messages.append(entry._prompt)
      if len(entry.response.choices) > 0:
        choice: Union[Message, PartialMessage] = entry.response.choices[0]
        messages.append(choice.toMessage())
    return messages

  def apiMessages(self) -> List[Dict[str, str]]:
    """Returns a list of all messages up to and including this entry, in API format."""
    return [msg.toApiMessage() for msg in self.messages()]

  def responses(self) -> List[Response]:
    """Returns a list of all responses up to and including this entry."""
    path = self.path()
    responses = []
    for entry in path:
      responses.append(entry._response)
    return responses

  def apiResponses(self) -> List[Dict[str, Any]]:
    """Returns a list of all responses up to and including this entry, in API format."""
    return [resp.toApiResponse() for resp in self.responses()]

  @staticmethod
  def Default() -> 'ChatEntry':
    return ChatEntry(prompt=Message.Default(), response=Response.Default(), parent=None)



class Chat:
  """A chat session. Contains a history of chat entries."""
  _current: ChatEntry
  @property
  def current(self) -> ChatEntry:
    """The current chat entry. This is the entry that was just added."""
    return self._current

  _root: ChatEntry
  @property
  def root(self) -> ChatEntry:
    """Pseudo-root entry, contains the real first ChatEntry(s). This entry is never displayed."""
    return self._root

  _previous: Optional[ChatEntry]
  @property
  def previous(self) -> Optional[ChatEntry]:
    """The previous chat entry"""
    return self._previous

  _cursor: ChatEntry
  @property
  def cursor(self) -> ChatEntry:
    """The chat entry that is currently being displayed"""
    return self._cursor

  _path: List[ChatEntry]
  """The path to the current chat entry"""

  _cursorPath: List[ChatEntry]
  """The path to the chat entry that is currently being displayed"""

  _cursorSiblingIndex: int

  def __init__(self):
    self._root = ChatEntry.Default()
    self.clear()

  def isDefault(self) -> bool:
    return self._current.parent == self._root \
      and len(self._current.children) == 0 and len(self._root.children) == 1 \
      and self._current._prompt.isDefault() and self._current._response.isDefault()

  def isEditable(self) -> bool:
    return self._cursor == self._current

  def addSibling(self, prompt: Message, response: Response = Response.Default()):
    """Adds a new entry as a sibling of the current cursor position.
    The added entry can be accessed via the `current` property."""
    if self._cursor is None: return
    self._previous = self._current
    self._current.prompt.content = ""
    self._current.response.choices = []
    self._current = ChatEntry(prompt=prompt, response=response, parent=self._cursor._parent)
    self._path = self._current.path()
    self._cursor = self._current
    self._updateCursorAttrs()

  def addDescendant(self, prompt: Message, response: Response = Response.Default()):
    """Adds a new entry as a descendant of the current cursor position.
    The added entry can be accessed via the `current` property."""
    if self._cursor is None: return
    self._previous = self._current
    self._current = ChatEntry(prompt=prompt, response=response, parent=self._cursor)
    self._path = self._current.path()
    self._cursor = self._current
    self._updateCursorAttrs()

  def _updateCursorAttrs(self):
    if self._cursor is None:
      self._cursorSiblingIndex = 0
      return
    self._cursorPath = self._cursor.path()
    self._cursorSiblingIndex = self._cursor.index()

  def canMoveUp(self) -> bool:
    """Returns True if the cursor can move up one level in the chat history, False otherwise."""
    if self._cursor.parent is None or self._cursor.parent == self._root: return False
    return True

  def canMoveDown(self) -> bool:
    """Returns True if the cursor can move down one level in the chat history, False otherwise."""
    if len(self._cursor.children) == 0: return False
    return True

  def canMoveLeft(self) -> bool:
    """Returns True if the cursor can move to the left sibling of the current entry, False otherwise."""
    if self._cursorSiblingIndex == 0: return False
    return True

  def canMoveRight(self) -> bool:
    """Returns True if the cursor can move to the right sibling of the current entry, False otherwise."""
    if self._cursor.parent is None: return False # should never happen but makes pyright happy
    if self._cursorSiblingIndex == len(self._cursor.parent.children) - 1: return False
    return True

  def up(self):
    """Moves the cursor up one level in the chat history, towards the root entry."""
    if self._cursor.parent is None: return
    if self._cursor.parent == self._root: return
    self._cursor = self._cursor.parent
    self._updateCursorAttrs()

  def down(self):
    """Moves the cursor down one level in the chat history, towards the leaf entries."""
    if len(self._cursor.children) == 0: return
    downIdx = -1 # default to the last child
    if self._cursor in self._path and len(self._cursor.children) > 1: # if the cursor is in the path, we want to go to the next entry in the path
      downIdx = self._path[self._path.index(self._cursor) + 1].index()
    self._cursor = self._cursor.children[downIdx]
    self._updateCursorAttrs()

  def left(self):
    """Moves the cursor to the left sibling of the current entry."""
    if self._cursorSiblingIndex == 0: return
    self._cursor = self._cursor.parent.children[self._cursorSiblingIndex - 1]
    self._updateCursorAttrs()

  def right(self):
    """Moves the cursor to the right sibling of the current entry."""
    if self._cursor.parent is None: return # should never happen but makes pyright happy
    if self._cursorSiblingIndex == len(self._cursor.parent.children) - 1: return
    self._cursor = self._cursor.parent.children[self._cursorSiblingIndex + 1]
    self._updateCursorAttrs()

  def top(self):
    """Moves the cursor to the first entry."""
    if self._cursor.parent is None or self._cursor.parent == self._root: return
    self._cursor = self._path[0]
    self._updateCursorAttrs()

  def bottom(self):
    """Moves the cursor to the last entry (the current entry)."""
    if len(self._cursor.children) == 0: return
    self._cursor = self._current
    self._updateCursorAttrs()

  def returnToCurrent(self) -> None:
    """Sets cursor to the current entry."""
    self._cursor = self._current

  def clear(self) -> None:
    """Clears the chat history, except for the root entry and sets current to a default editable object."""
    self._root.children.clear()
    self._current = ChatEntry(prompt=Message.Default(), response=Response.Default(), parent=self._root)
    self._previous = None
    self._path = self._current.path()
    self._cursor = self._current
    self._cursorSiblingIndex = 0
    self._cursorPath = self._cursor.path()



@dataclass
class TokenSet:
  """Represents a group of tokens. Useful for grouping tokens together for use with the `ChatCompletionParams` class."""
  tokens: List[int]
  """The tokens in the set."""
  bias: float
  """The weight of the tokens."""

  def __post_init__(self):
    if not isinstance(self.tokens, list) or not all(isinstance(x, int) for x in self.tokens): raise TypeError("tokens must be a list of integers")
    if not isinstance(self.bias, float): raise TypeError("weight must be a float")

class ChatCompletionParams:
  """A named and documented class representing the parameters for creating an openai ChatCompletion. This can be converted to dict keyword params with the `toDict()` method."""

  _apiKey: str
  @property
  def apiKey(self) -> str:
    """Your OpenAI API key."""
    return self._apiKey
  @apiKey.setter
  def apiKey(self, value: str) -> None:
    if not isinstance(value, str): raise TypeError("apiKey must be a string")
    self._apiKey = value

  _model: str
  @property
  def model(self) -> str:
    """ID of the model to use. See https://platform.openai.com/docs/models/model-endpoint-compatibility table for details on which models work with the Chat API.
    Models can be easily retrieved with `getChatModels()`"""
    return self._model
  @model.setter
  def model(self, value: str) -> None:
    if not isinstance(value, str): raise TypeError("model must be a string")
    self._model = value

  _messages: List[Message] = field(default_factory=list)
  @property
  def messages(self) -> List[Message]:
    """A list of messages describing the conversation so far"""
    return self._messages
  @messages.setter
  def messages(self, value: List[Message]) -> None:
    if not isinstance(value, list): raise TypeError("messages must be a list")
    if not all(isinstance(x, Message) for x in value): raise TypeError("messages must be a list of Message objects")
    self._messages = value

  _temperature: Optional[float] = None
  @property
  def temperature(self) -> float:
    """What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. Defaults to 1.0 if not specified. We generally recommend altering this or `top_p` but not both."""
    if self._temperature is None: return 1.0
    return self._temperature
  @temperature.setter
  def temperature(self, value: Optional[float]) -> None:
    if value and not isinstance(value, float): raise TypeError("temperature must be a float")
    self._temperature = value

  _max_tokens: Optional[int] = None
  @property
  def max_tokens(self) -> int:
    """The maximum number of tokens to generate in the chat completion. The total length of input tokens and generated tokens is limited by the model's context length."""
    if self._max_tokens is None: return 2048
    return self._max_tokens
  @max_tokens.setter
  def max_tokens(self, value: Optional[int]) -> None:
    if value and not isinstance(value, int): raise TypeError("max_tokens must be an int")
    self._max_tokens = value

  _top_p: Optional[float] = None
  @property
  def top_p(self) -> float:
    """An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered. Defaults to 1.0 if not specified, which is equivalent to temperature sampling. We generally recommend altering this or `temperature` but not both"""
    if self._top_p is None: return 1.0
    return self._top_p
  @top_p.setter
  def top_p(self, value: Optional[float]) -> None:
    if value and not isinstance(value, float): raise TypeError("top_p must be a float")
    self._top_p = value

  _n: Optional[int] = None
  @property
  def n(self) -> int:
    """How many chat completion choices to generate for each input message. Defaults to 1 if not specified. Must be between 1 and 10."""
    if self._n is None: return 1
    return self._n
  @n.setter
  def n(self, value: Optional[int]) -> None:
    if value and not isinstance(value, int): raise TypeError("n must be an int")
    self._n = value

  _frequency_penalty: Optional[float] = None
  @property
  def frequency_penalty(self) -> float:
    """Number between -2.0 and 2.0. Positive values encourage the model to talk about new topics, while negative values encourage the model to repeat itself. This parameter has been superseded by `presence_penalty`, which is much more effective."""
    if self._frequency_penalty is None: return 0.0
    return self._frequency_penalty
  @frequency_penalty.setter
  def frequency_penalty(self, value: Optional[float]) -> None:
    if value and not isinstance(value, float): raise TypeError("frequency_penalty must be a float")
    self._frequency_penalty = value

  _presence_penalty: Optional[float] = None
  @property
  def presence_penalty(self) -> float:
    """Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics. See: https://platform.openai.com/docs/api-reference/parameter-details"""
    if self._presence_penalty is None: return 0.0
    return self._presence_penalty
  @presence_penalty.setter
  def presence_penalty(self, value: Optional[float]) -> None:
    if value and not isinstance(value, float): raise TypeError("presence_penalty must be a float")
    self._presence_penalty = value

  _stop: Optional[List[str]] = None
  @property
  def stop(self) -> List[str]:
    """Up to 4 sequences where the API will stop generating further tokens."""
    if self._stop is None: return []
    return self._stop
  @stop.setter
  def stop(self, value: Optional[List[str]]) -> None:
    if value and not isinstance(value, list): raise TypeError("stop must be a list")
    if value and not all(isinstance(x, str) for x in value): raise TypeError("stop must be a list of strings")
    self._stop = value

  _stream: bool = True
  @property
  def stream(self) -> bool:
    """If set, partial message deltas will be sent, like in ChatGPT. Tokens will be sent as data-only server-sent events as they become available, with the stream terminated by a data: [DONE] message. See the OpenAI Cookbook for example code."""
    return self._stream
  @stream.setter
  def stream(self, value: bool) -> None:
    if not isinstance(value, bool): raise TypeError("stream must be a bool")
    self._stream = value

  _logit_bias: Optional[List[TokenSet]] = None
  @property
  def logit_bias(self) -> Optional[List[TokenSet]]:
    """Modify the likelihood of specified tokens appearing in the completion. Accepts a dict object that maps tokens (specified by their token ID in the tokenizer) to an associated bias value from -100 to 100. Mathematically, the bias is added to the logits generated by the model prior to sampling. The exact effect will vary per model, but values between -1 and 1 should decrease or increase likelihood of selection; values like -100 or 100 should result in a ban or exclusive selection of the relevant token"""
    return self._logit_bias


  _user: Optional[str] = None
  @property
  def user(self) -> Optional[str]:
    """A unique identifier representing your end-user, which can help OpenAI to monitor and detect abuse"""
    return self._user
  @user.setter
  def user(self, value: Optional[str]) -> None:
    if value and not isinstance(value, str): raise TypeError("user must be a str")
    self._user = value


  def __init__(self, model: str, messages: Optional[List[Message]] = None,
               temperature: Optional[float] = None, max_tokens: Optional[int] = None, top_p: Optional[float] = None,
               n: Optional[int] = None, frequency_penalty: Optional[float] = None,
               presence_penalty: Optional[float] = None, stop: Optional[List[str]] = None, stream: bool = True,
               logit_bias: Optional[List[TokenSet]] = None, user: Optional[str] = None, apiKey: str = ""):
    """Sets the stop sequence."""
    if messages is None: messages = []
    if temperature and (not isinstance(temperature, float) or temperature < 0 or temperature > 2): raise ValueError('temperature must be a float between 0 and 2')
    if max_tokens and not isinstance(max_tokens, int): raise TypeError('max_tokens must be an int')
    if top_p and (not isinstance(top_p, float) or top_p < 0 or top_p > 1): raise ValueError('top_p must be a float between 0 and 1')
    if n and (not isinstance(n, int) or n < 1 or n > 10): raise ValueError('n must be an int between 1 and 10')
    if frequency_penalty and (not isinstance(frequency_penalty, float) or frequency_penalty < -2 or frequency_penalty > 2): raise ValueError('frequency_penalty must be a float between -2 and 2')
    if presence_penalty and (not isinstance(presence_penalty, float) or presence_penalty < -2 or presence_penalty > 2): raise ValueError('presence_penalty must be a float between -2 and 2')
    if stop and (not isinstance(stop, list) or len(stop) > 4): raise ValueError('stop must be a list of up to 4 strings')
    if logit_bias and not isinstance(logit_bias, list): raise ValueError('logit_bias must be a list')
    if user and (not isinstance(user, str) or len(user) > 256): raise ValueError('user must be a string of up to 256 characters')
    if not isinstance(apiKey, str): raise TypeError('apiKey must be a string')
    self.apiKey = apiKey
    self.model = model
    self.messages = messages
    self.temperature = temperature
    self.max_tokens = max_tokens
    self.top_p = top_p
    self.n = n
    self.frequency_penalty = frequency_penalty
    self.presence_penalty = presence_penalty
    self.stop = stop
    self.stream = stream
    self._logit_bias = logit_bias
    self.user = user

  def hasMaxTokens(self) -> bool:
    """Returns whether max_tokens is set."""
    return self._max_tokens is not None

  def hasTemperature(self) -> bool:
    """Returns whether temperature is set."""
    return self._temperature is not None

  def hasTopP(self) -> bool:
    """Returns whether top_p is set."""
    return self._top_p is not None

  def hasN(self) -> bool:
    """Returns whether n is set."""
    return self._n is not None

  def hasFrequencyPenalty(self) -> bool:
    """Returns whether frequency_penalty is set."""
    return self._frequency_penalty is not None

  def hasPresencePenalty(self) -> bool:
    """Returns whether presence_penalty is set."""
    return self._presence_penalty is not None

  def hasStop(self) -> bool:
    """Returns whether stop is set."""
    return self._stop is not None

  def hasLogitBias(self) -> bool:
    """Returns whether logit_bias is set."""
    return self._logit_bias is not None

  def hasUser(self) -> bool:
    """Returns whether user is set."""
    return self._user is not None

  def setLogitBias(self, logit_bias: Optional[List[TokenSet]]) -> None:
    """Sets the logit bias from a list of TokenSets."""
    if logit_bias:
      if not isinstance(logit_bias, list): raise TypeError("logit_bias must be a dict")
      if not all(isinstance(x, TokenSet) for x in logit_bias): raise TypeError("logit_bias values must be TokenSets")
    self._logit_bias = logit_bias

  def setLogitBiasStrDict(self, logit_bias: Dict[str, float]) -> None:
    """Sets the logit bias from a dictionary of strings to floats. Module `tiktoken` is required or this will do nothing."""
    if not HAS_TIKTOKEN: return
    if not isinstance(logit_bias, dict): raise TypeError("logit_bias must be a dict")
    if not all(isinstance(x, str) for x in logit_bias.keys()): raise TypeError("logit_bias keys must be strings")
    if not all(isinstance(x, float) for x in logit_bias.values()): raise TypeError("logit_bias values must be floats")
    lb_tokenized: List[TokenSet] = []
    enc = tiktoken.encoding_for_model(self._model)
    for k, v in logit_bias.items():
      tokens = enc.encode(k)
      lb_tokenized.append(TokenSet(tokens, v))
    self._logit_bias = lb_tokenized

  def getLogitBiasStrDict(self) -> Dict[str, float]:
    """Returns the logit bias as a dictionary of strings to floats. Module `tiktoken` is required or this will return an empty dict."""
    if not HAS_TIKTOKEN: return {}
    if not self._logit_bias: return {}
    enc = tiktoken.encoding_for_model(self._model)
    return {enc.decode(x.tokens): x.bias for x in self._logit_bias}

  def toDict(self) -> dict:
    """Returns a dictionary of the parameters for use with the OpenAI API."""
    d = {}
    apiMessages = [m.toApiMessage() for m in self._messages]
    d['model'] = self._model
    d['messages'] = apiMessages
    if self._temperature: d['temperature'] = self._temperature
    if self._max_tokens: d['max_tokens'] = self._max_tokens
    if self._top_p: d['top_p'] = self._top_p
    if self._n: d['n'] = self._n
    if self._frequency_penalty: d['frequency_penalty'] = self._frequency_penalty
    if self._presence_penalty: d['presence_penalty'] = self._presence_penalty
    if self._stop: d['stop'] = self._stop
    if self._stream: d['stream'] = self._stream
    if self._logit_bias:
      lbd: Dict[int, float] = {}
      for tset in self._logit_bias:
        for t in tset.tokens: lbd[t] = tset.bias
      d['logit_bias'] = lbd
    return d

  def copy(self):
    """Returns a copy of the Completion object."""
    messages = None
    if self._messages: messages = [m.copy() for m in self._messages]
    logit_bias = None
    if self._logit_bias: logit_bias = self._logit_bias.copy()
    return ChatCompletionParams(apiKey=self._apiKey, model=self._model, messages=messages, temperature=self._temperature,
                                max_tokens=self._max_tokens, top_p=self._top_p, n=self._n,
                                frequency_penalty=self._frequency_penalty, presence_penalty=self._presence_penalty,
                                stop=self._stop, stream=self._stream, logit_bias=logit_bias, user=self._user)


def getModels(filterPrefixes: Optional[List[str]] = None) -> List[str]:
  """Returns a list of all chat model names
  Args:
    filterPrefixes ([str] = ['gpt']): Only return models that start with these prefixes. Set to [] to return all models."""
  if filterPrefixes is None: filterPrefixes = ['gpt']
  try:
    engineList: dict = openai.Engine.list()
  except Exception as e:
    return []
  models = engineList['data']
  models = [m['id'] for m in models]
  if len(filterPrefixes) > 0:
    # filter out the models that are not in the filter list
    models = [m for m in models if any([m.startswith(p) for p in filterPrefixes])]
  return models

