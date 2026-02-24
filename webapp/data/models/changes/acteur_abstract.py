"""change model to use as template for acteur changes"""

from pydantic import BaseModel


class ChangeActeurAbstract(BaseModel):
    # We need to know which acteur to change
    id: str
    # And what data to use (if it's an update)
    data: dict = {}

    @classmethod
    def name(cls) -> str:
        # Return a name in snake_case format
        raise NotImplementedError("Method must be implemented")

    def validate(self):
        # Method called to validate the data
        # - either as standalone when we prepare suggestions
        # - or automatically as part of apply
        raise NotImplementedError("Method must be implemented")

    def apply(self):
        # Method called to make the change effective
        self.validate()
        raise NotImplementedError("Method must be implemented")
