from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional

# Schemas for API requests and responses

# Request schema for searching cards
class CardSearchRequest(BaseModel):
    card_name: str = Field(..., min_length=2, max_length=200) # Card name to search for
    condition_type: Literal["raw", "graded"] # "raw" for ungraded cards, "graded" for graded cards
    grader: Optional[Literal["PSA", "ACE"]] = None # Only required if condition_type is "graded"
    grade: Optional[int] = Field(None, ge=1, le=10) # Only required if condition_type is "graded", must be between 1 and 10
    include_unsold: bool = False # Whether to include unsold cards in the search results
    max_results: int = Field(20, ge=1, le=50) # Maximum number of search results to return
    
    
    @model_validator(mode="after")
    def validate_graded_fields(self):
        if self.condition_type == "graded":
            if not self.grader:
                raise ValueError("Grader must be specified when condition_type is 'graded'")
            if self.grade is None:
                raise ValueError("Grade must be specified when condition_type is 'graded'")
        else:
            if self.grader is not None or self.grade is not None:
                raise ValueError("Grader and Grade must only be provided for graded cards")
        return self