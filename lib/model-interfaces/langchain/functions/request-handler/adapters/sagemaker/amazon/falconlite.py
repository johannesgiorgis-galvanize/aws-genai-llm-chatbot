import json
import os

from langchain.llms.sagemaker_endpoint import LLMContentHandler, SagemakerEndpoint
from langchain.prompts.prompt import PromptTemplate

from ...base import ModelAdapter
from ...registry import registry


class FalconLiteContentHandler(LLMContentHandler):
    content_type = "application/json"
    accepts = "application/json"

    def transform_input(self, prompt, model_kwargs) -> bytes:
        input_str = json.dumps(
            {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 10000,
                    "do_sample": True,
                    "temperature": None,
                    "return_full_text": False,
                    "typical_p": 0.2,
                    "use_cache": True,
                    "seed": 1,
                },
            }
        )
        return input_str.encode("utf-8")

    def transform_output(self, output: bytes):
        response_json = json.loads(output.read().decode("utf-8"))
        return response_json[0]["generated_text"]


content_handler = FalconLiteContentHandler()


class SMFalconLiteAdapter(ModelAdapter):
    def __init__(self, model_id, **kwargs):
        self.model_id = model_id

        super().__init__(**kwargs)

    def get_llm(self, *args, **kwargs):
        return SagemakerEndpoint(
            endpoint_name=self.model_id,
            region_name=os.environ["AWS_REGION"],
            content_handler=content_handler,
        )

    def get_prompt(self):
        template = """<|prompter|>Our current conversation: {chat_history}

        {input}<|endoftext|><|assistant|>"""

        input_variables = ["input", "chat_history"]
        prompt_template_args = {
            "chat_history": "{chat_history}",
            "input_variables": input_variables,
            "template": template,
        }
        prompt_template = PromptTemplate(**prompt_template_args)

        return prompt_template


# Register the adapter
registry.register(r"^SageMaker.amazon-FalconLite*", SMFalconLiteAdapter)
