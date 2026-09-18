from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Claim(StrictModel):
    kind: Literal["observation", "hypothesis", "unknown", "next_check", "guidance"]
    text: str = Field(min_length=1, max_length=1600)
    evidence_ids: list[str] = Field(min_length=1, max_length=12)


class Section(StrictModel):
    heading: Literal[
        "Alert triggers",
        "What happened",
        "Suspicious indicators",
        "Legitimate explanations",
        "Relevant guidance",
        "Missing evidence and next checks",
    ]
    claims: list[Claim] = Field(min_length=1, max_length=10)


class BriefContent(StrictModel):
    sections: list[Section] = Field(min_length=6, max_length=6)
    conclusion: Literal["Further investigation required"]


class BriefRequest(StrictModel):
    mode: Literal["reference", "live"] = "reference"
    retrieval_mode: Literal["keyword", "vector", "hybrid"] = "keyword"


class SearchRequest(StrictModel):
    query: str = Field(min_length=2, max_length=500)
    mode: Literal["keyword", "vector", "hybrid"] = "keyword"
    k: int = Field(default=5, ge=1, le=10)


class ReviewRequest(StrictModel):
    brief_id: str
    disposition: Literal[
        "needs_more_evidence", "escalate_for_review", "legitimate_explanation_supported"
    ]
    notes: str = Field(min_length=10, max_length=2000)
