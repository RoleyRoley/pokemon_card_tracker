from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class CardSearchRequest(BaseModel):
    card_name: str = Field(..., min_length=2, max_length=200) # Card name should be between 2 and 200 characters
    condition_type: Literal["raw", "graded"] # Condition type can only be "raw" or "graded"
    grader: Optional[Literal["PSA", "ACE"]] = None # Grader can only be "PSA" or "ACE" if condition_type is "graded"
    grade: Optional[int] = Field(None, ge=1, le=10) # Grade must be between 1 and 10 if condition_type is "graded"
    include_unsold: bool = False # Whether to include unsold listings in the response
    max_results: int = Field(20, ge=1, le=50) # Maximum number of listings to return, between 1 and 50

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


class EbayListing(BaseModel):
    title: str
    price: float
    currency: str
    listing_url: str
    image_url: Optional[str] = None
    condition_text: Optional[str] = None
    date_text: Optional[str] = None
    shipping_text: Optional[str] = None
    sold: bool


class ListingStats(BaseModel):
    count: int
    lowest_price: Optional[float] = None
    highest_price: Optional[float] = None
    average_price: Optional[float] = None
    median_price: Optional[float] = None


class CardSearchResponse(BaseModel):
    query_used: str
    sold_listings: List[EbayListing]
    sold_stats: ListingStats
    unsold_listings: List[EbayListing] = []