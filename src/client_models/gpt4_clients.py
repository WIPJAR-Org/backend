from abc import ABC, abstractmethod
import base64
from mimetypes import guess_type
from openai import AzureOpenAI

class BaseGPTClient(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    @property
    @abstractmethod
    def client(self):
        pass
   
    @property
    @abstractmethod
    def deployment_name(self):
        pass
    
    def chat_completion(self, messages, max_tokens):
        try :
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                max_tokens=max_tokens,
            )
            if response is None:
                raise ValueError("Failed to obtain a response!")
            return response
        except Exception as e:
            # if e["error"] is not None:
            #     print("Exception from GPT", e["error"]["message"], e["error"]["param"])
            # else :
            print("Exception from GPT", e)