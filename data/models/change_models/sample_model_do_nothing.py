"""A sample model which does nothing BUT we
can use to help us create test cases for the
overall SuggestionChange model without having
to construct complex cases"""

from pydantic import BaseModel


class SampleModelDoNothing(BaseModel):
    @classmethod
    def name(cls) -> str:
        return "sample_model_do_nothing"

    def validate(self):
        pass
