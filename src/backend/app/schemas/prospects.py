from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CollectProspectsRequest(BaseModel):
    industry: str
    regions: list[str] = Field(min_length=1)
    roles: list[str] = Field(min_length=1)
    limit: int = Field(default=100, ge=1, le=100)

    @field_validator("industry")
    @classmethod
    def normalize_industry(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("industry must not be empty")
        return normalized_value

    @field_validator("regions", "roles")
    @classmethod
    def normalize_str_list(cls, values: list[str]) -> list[str]:
        normalized_values = [value.strip() for value in values if value.strip()]
        if not normalized_values:
            raise ValueError("list must not be empty")
        return normalized_values

    @field_validator("limit", mode="before")
    @classmethod
    def cap_limit(cls, value: int) -> int:
        return min(int(value), 100)


class ProspectListQuery(BaseModel):
    industry: str = Field(default="SaaS", min_length=1)
    region: str = Field(default="深圳, 广州", min_length=1)
    roles: str = Field(default="CTO, 技术副总裁", min_length=1)
    limit: int = Field(default=100, ge=1, le=100)

    @field_validator("industry")
    @classmethod
    def validate_industry(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("industry must not be empty")
        return normalized_value

    @field_validator("region", "roles")
    @classmethod
    def validate_csv_query_value(cls, value: str, info) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError(f"{info.field_name} must not be empty")

        if not [item.strip() for item in normalized_value.split(",") if item.strip()]:
            raise ValueError(f"{info.field_name} must include at least one item")

        return normalized_value

    @property
    def regions(self) -> list[str]:
        return [item.strip() for item in self.region.split(",") if item.strip()]

    @property
    def normalized_roles(self) -> list[str]:
        return [item.strip() for item in self.roles.split(",") if item.strip()]


class BANTScore(BaseModel):
    score: int
    priority: Literal["A", "B", "C", "D"]
    budget: int
    authority: int
    need: int
    timeline: int


class ProspectProfile(BaseModel):
    industry: str
    company_scale: str
    pain_points: list[str]
    needs: list[str]


class ProspectItem(BaseModel):
    id: str
    company_name: str
    region: str
    industry: str
    role: str
    website: str
    contact_email: str
    bant: BANTScore
    profile: ProspectProfile


class ProspectReportView(BaseModel):
    id: str
    company_name: str
    industry: str
    region: str
    role: str
    priority: Literal["A", "B", "C", "D"]
    bant_score: int
    summary_text: str
    profile: ProspectProfile
    bant: BANTScore


class ProspectCollectionSummary(BaseModel):
    requested: int
    returned: int
    deduplicated: int
    validity_rate: float


class ProspectImportSummary(BaseModel):
    imported: int
    skipped: int
    failed: int


class ProspectImportResult(BaseModel):
    summary: ProspectImportSummary
    items: list[ProspectItem]


class ProspectCollectionResult(BaseModel):
    summary: ProspectCollectionSummary
    items: list[ProspectItem]


class ProspectListResult(BaseModel):
    items: list[ProspectItem]


class ProspectDataSourceItem(BaseModel):
    key: str
    label: str
    type: Literal["seed", "import"]
    status: Literal["available", "unavailable"]
    description: str


class ProspectDataSourceListResult(BaseModel):
    items: list[ProspectDataSourceItem]
