from pydantic import BaseModel, Field
from typing import Literal

class OutputSchema(BaseModel):
    evidence_standard_met: bool = Field(description="true if image set is sufficient to evaluate the claim; otherwise false")
    evidence_standard_met_reason: str = Field(description="Short reason for the evidence decision")
    risk_flags: str = Field(description="semicolon-separated risk flags, or 'none'")
    issue_type: Literal["dent", "scratch", "crack", "glass_shatter", "broken_part", "missing_part", "torn_packaging", "crushed_packaging", "water_damage", "stain", "none", "unknown"]
    object_part: str = Field(description="Relevant object part from the allowed list for the claim_object")
    claim_status: Literal["supported", "contradicted", "not_enough_information"]
    claim_status_justification: str = Field(description="Concise image-grounded explanation")
    supporting_image_ids: str = Field(description="image IDs supporting the decision, separated by semicolons; use 'none' if no image is sufficient")
    valid_image: bool = Field(description="true if image set is usable for automated review; otherwise false")
    severity: Literal["none", "low", "medium", "high", "unknown"]
