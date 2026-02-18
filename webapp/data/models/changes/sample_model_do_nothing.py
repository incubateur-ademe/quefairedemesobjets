"""A sample model which does nothing BUT helps us create test cases for the
overall SuggestionChange model"""

from pydantic import BaseModel


class SampleModelDoNothing(BaseModel):
    @classmethod
    def name(cls) -> str:
        return "sample_model_do_nothing"

    def validate(self):
        pass

    def apply(self):
        pass
