from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from io import StringIO
from itertools import product
from typing import BinaryIO

from app.schemas.prospects import (
    BANTScore,
    CollectProspectsRequest,
    ProspectCollectionResult,
    ProspectCollectionSummary,
    ProspectDataSourceItem,
    ProspectDataSourceListResult,
    ProspectImportResult,
    ProspectImportSummary,
    ProspectItem,
    ProspectListResult,
    ProspectProfile,
    ProspectReportView,
)

RawProspect = dict[str, object]

REQUIRED_CSV_HEADERS = {"company_name", "website", "contact_email", "region", "industry", "role"}
EXPORT_CSV_HEADERS = [
    "id",
    "company_name",
    "region",
    "industry",
    "role",
    "website",
    "contact_email",
    "bant_score",
    "priority",
    "company_scale",
    "pain_points",
    "needs",
    "profile_industry",
]


COMPANY_PREFIXES = [
    "增长",
    "启航",
    "云图",
    "极客",
    "智链",
    "数帆",
    "引力",
    "飞轮",
    "星河",
    "火种",
    "云梯",
    "蓝海",
]

COMPANY_SUFFIXES = [
    "科技",
    "软件",
    "智能",
    "数据",
    "引擎",
    "数字",
    "互联",
    "云服",
    "信息",
]

COMPANY_SCALES = ["10-20 人", "20-50 人", "50-100 人", "100-300 人"]

PAIN_POINT_PAIRS = [
    ["销售线索分散", "跟进节奏不稳定"],
    ["人工筛选效率低", "名单质量波动大"],
    ["客户画像不完整", "意向判断依赖经验"],
    ["商机复盘困难", "团队协作透明度低"],
]

NEED_PAIRS = [
    ["统一线索池", "自动优先级排序"],
    ["企业画像报告", "线索批量筛选"],
    ["稳定线索来源", "标准化销售动作"],
    ["可视化分析", "高质量目标客户名单"],
]


def _priority_from_score(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    return "D"


def _build_bant(budget: int, authority: int, need: int, timeline: int) -> BANTScore:
    score = budget + authority + need + timeline
    return BANTScore(
        score=score,
        priority=_priority_from_score(score),
        budget=budget,
        authority=authority,
        need=need,
        timeline=timeline,
    )


class ProspectProfileGenerator(ABC):
    @abstractmethod
    def generate(self, item: RawProspect) -> ProspectProfile:
        raise NotImplementedError


class MockProspectProfileGenerator(ProspectProfileGenerator):
    def generate(self, item: RawProspect) -> ProspectProfile:
        return ProspectProfile(
            industry=str(item["industry"]),
            company_scale=str(item["company_scale"]),
            pain_points=list(item["pain_points"]),
            needs=list(item["needs"]),
        )


DEFAULT_PROFILE_GENERATOR = MockProspectProfileGenerator()


def build_prospect_profile(
    item: RawProspect,
    generator: ProspectProfileGenerator | None = None,
) -> ProspectProfile:
    profile_generator = generator or DEFAULT_PROFILE_GENERATOR
    return profile_generator.generate(item)


def _prospect_item_from_raw(
    item: RawProspect,
    generator: ProspectProfileGenerator | None = None,
) -> ProspectItem:
    bant = _build_bant(
        int(item["budget"]),
        int(item["authority"]),
        int(item["need"]),
        int(item["timeline"]),
    )
    return ProspectItem(
        id=str(item["id"]),
        company_name=str(item["company_name"]),
        region=str(item["region"]),
        industry=str(item["industry"]),
        role=str(item["role"]),
        website=str(item["website"]),
        contact_email=str(item["contact_email"]),
        bant=bant,
        profile=build_prospect_profile(item, generator=generator),
    )


def _build_import_raw_item(index: int, row: dict[str, str]) -> RawProspect:
    normalized_industry = row["industry"].strip()
    return {
        "id": f"csv-lead-{index}",
        "company_name": row["company_name"].strip(),
        "region": row["region"].strip(),
        "industry": normalized_industry,
        "role": row["role"].strip(),
        "website": row["website"].strip(),
        "contact_email": row["contact_email"].strip(),
        "budget": 16,
        "authority": 15,
        "need": 18,
        "timeline": 11,
        "company_scale": "20-50 人",
        "pain_points": ["导入线索待统一清洗", "销售资料分散"],
        "needs": ["线索快速入池", "自动化初筛"],
    }


def import_prospects_from_csv(
    file_obj: BinaryIO,
    generator: ProspectProfileGenerator | None = None,
) -> ProspectImportResult:
    file_obj.seek(0)
    csv_text = file_obj.read().decode("utf-8-sig")
    reader = csv.DictReader(StringIO(csv_text))

    raw_fieldnames = reader.fieldnames or []
    normalized_fieldnames = [field.strip() for field in raw_fieldnames]
    missing_headers = sorted(REQUIRED_CSV_HEADERS - set(normalized_fieldnames))
    if missing_headers:
        raise ValueError(f"missing required CSV headers: {', '.join(missing_headers)}")

    items: list[ProspectItem] = []
    skipped = 0
    imported_count = 0

    for index, row in enumerate(reader, start=1):
        normalized_row = {(key or "").strip(): (value or "").strip() for key, value in row.items()}
        if not any(normalized_row.values()):
            skipped += 1
            continue
        if any(not normalized_row[header] for header in REQUIRED_CSV_HEADERS):
            skipped += 1
            continue
        imported_count += 1
        items.append(_prospect_item_from_raw(_build_import_raw_item(imported_count, normalized_row), generator=generator))

    return ProspectImportResult(
        summary=ProspectImportSummary(
            imported=len(items),
            skipped=skipped,
            failed=0,
        ),
        items=items,
    )


def _build_raw_items(
    industry: str = "SaaS",
    regions: list[str] | None = None,
    roles: list[str] | None = None,
) -> list[RawProspect]:
    normalized_regions = regions or ["深圳"]
    normalized_roles = roles or ["CTO"]
    primary_region = normalized_regions[0]
    secondary_region = normalized_regions[min(1, len(normalized_regions) - 1)]
    primary_role = normalized_roles[0]
    secondary_role = normalized_roles[min(1, len(normalized_roles) - 1)]

    raw_items: list[RawProspect] = [
        {
            "id": "lead-1",
            "company_name": "深圳云帆 SaaS 科技",
            "region": primary_region,
            "industry": industry,
            "role": primary_role,
            "website": "yunfan.example.com",
            "contact_email": "cto@yunfan.example.com",
            "budget": 24,
            "authority": 22,
            "need": 23,
            "timeline": 18,
            "company_scale": "100-300 人",
            "pain_points": ["线索分散", "销售漏斗不可视"],
            "needs": ["统一线索池", "自动优先级排序"],
        },
        {
            "id": "lead-2",
            "company_name": "深圳云帆 SaaS 科技",
            "region": primary_region,
            "industry": industry,
            "role": primary_role,
            "website": "yunfan.example.com",
            "contact_email": "cto@yunfan.example.com",
            "budget": 24,
            "authority": 22,
            "need": 23,
            "timeline": 18,
            "company_scale": "100-300 人",
            "pain_points": ["线索分散", "销售漏斗不可视"],
            "needs": ["统一线索池", "自动优先级排序"],
        },
        {
            "id": "lead-3",
            "company_name": "深圳增长引擎软件",
            "region": secondary_region,
            "industry": industry,
            "role": secondary_role,
            "website": "growth-engine.example.com",
            "contact_email": "hello@growth-engine.example.com",
            "budget": 20,
            "authority": 20,
            "need": 20,
            "timeline": 15,
            "company_scale": "50-100 人",
            "pain_points": ["人工筛选效率低", "缺少画像标签"],
            "needs": ["自动采集", "画像报告交付"],
        },
        {
            "id": "lead-4",
            "company_name": "深圳触达自动化有限公司",
            "region": primary_region,
            "industry": industry,
            "role": secondary_role,
            "website": "reach-auto.example.com",
            "contact_email": "contact@reach-auto.example.com",
            "budget": 18,
            "authority": 16,
            "need": 17,
            "timeline": 12,
            "company_scale": "20-50 人",
            "pain_points": ["团队跟进不稳定", "线索质量参差不齐"],
            "needs": ["高质量名单", "标准化报告"],
        },
        {
            "id": "lead-5",
            "company_name": "深圳出海伙伴平台",
            "region": secondary_region,
            "industry": industry,
            "role": primary_role,
            "website": "global-partner.example.com",
            "contact_email": "ops@global-partner.example.com",
            "budget": 15,
            "authority": 14,
            "need": 16,
            "timeline": 10,
            "company_scale": "10-20 人",
            "pain_points": ["市场信息滞后", "销售动作难复盘"],
            "needs": ["稳定线索来源", "可视化分析"],
        },
    ]

    region_role_pairs = list(product(normalized_regions, normalized_roles))
    generated_name_pairs = list(product(COMPANY_PREFIXES, COMPANY_SUFFIXES))

    for offset, (name_prefix, name_suffix) in enumerate(generated_name_pairs, start=6):
        region, role = region_role_pairs[(offset - 6) % len(region_role_pairs)]
        pain_points = PAIN_POINT_PAIRS[(offset - 6) % len(PAIN_POINT_PAIRS)]
        needs = NEED_PAIRS[(offset - 6) % len(NEED_PAIRS)]
        company_scale = COMPANY_SCALES[(offset - 6) % len(COMPANY_SCALES)]
        slug = f"lead-{offset}"

        raw_items.append(
            {
                "id": f"lead-{offset}",
                "company_name": f"{region}{name_prefix}{name_suffix}{industry}有限公司",
                "region": region,
                "industry": industry,
                "role": role,
                "website": f"{slug}.example.com",
                "contact_email": f"bd+{offset}@{slug}.example.com",
                "budget": 10 + ((offset - 6) % 4),
                "authority": 11 + ((offset - 6) % 4),
                "need": 12 + ((offset - 6) % 4),
                "timeline": 7 + ((offset - 6) % 3),
                "company_scale": company_scale,
                "pain_points": pain_points,
                "needs": needs,
            }
        )

    return raw_items


def _deduplicate_and_rank_items(
    raw_items: list[RawProspect],
    generator: ProspectProfileGenerator | None = None,
) -> list[ProspectItem]:
    deduplicated_items: list[ProspectItem] = []
    seen_keys: set[str] = set()

    for item in raw_items:
        dedupe_key = f"{item['company_name']}::{item['website']}::{item['contact_email']}"
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        deduplicated_items.append(_prospect_item_from_raw(item, generator=generator))

    return sorted(deduplicated_items, key=lambda item: item.bant.score, reverse=True)


def _build_seed_items(
    industry: str = "SaaS",
    regions: list[str] | None = None,
    roles: list[str] | None = None,
    generator: ProspectProfileGenerator | None = None,
) -> list[ProspectItem]:
    raw_items = _build_raw_items(industry=industry, regions=regions, roles=roles)
    return _deduplicate_and_rank_items(raw_items, generator=generator)


def list_available_data_sources() -> ProspectDataSourceListResult:
    return ProspectDataSourceListResult(
        items=[
            ProspectDataSourceItem(
                key="mock_seed",
                label="Mock seed",
                type="seed",
                status="available",
                description="内置示例线索数据，可直接用于 Phase 0/1 MVP 验证。",
            ),
            ProspectDataSourceItem(
                key="csv_import",
                label="CSV import",
                type="import",
                status="available",
                description="上传企业名单 CSV，走最小导入闭环并生成线索画像。",
            ),
        ]
    )


def list_prospects(
    industry: str = "SaaS",
    regions: list[str] | None = None,
    roles: list[str] | None = None,
    limit: int | None = None,
    generator: ProspectProfileGenerator | None = None,
) -> ProspectListResult:
    items = _build_seed_items(
        industry=industry,
        regions=regions,
        roles=roles,
        generator=generator,
    )
    if limit is not None:
        items = items[:limit]
    return ProspectListResult(items=items)


def export_prospects_to_csv(
    industry: str = "SaaS",
    regions: list[str] | None = None,
    roles: list[str] | None = None,
    limit: int | None = None,
    generator: ProspectProfileGenerator | None = None,
) -> str:
    result = list_prospects(
        industry=industry,
        regions=regions,
        roles=roles,
        limit=limit,
        generator=generator,
    )
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_CSV_HEADERS)
    writer.writeheader()

    for item in result.items:
        writer.writerow(
            {
                "id": item.id,
                "company_name": item.company_name,
                "region": item.region,
                "industry": item.industry,
                "role": item.role,
                "website": item.website,
                "contact_email": item.contact_email,
                "bant_score": item.bant.score,
                "priority": item.bant.priority,
                "company_scale": item.profile.company_scale,
                "pain_points": " | ".join(item.profile.pain_points),
                "needs": " | ".join(item.profile.needs),
                "profile_industry": item.profile.industry,
            }
        )

    return output.getvalue()


def get_prospect_by_id(
    prospect_id: str,
    generator: ProspectProfileGenerator | None = None,
) -> ProspectItem | None:
    return next((item for item in _build_seed_items(generator=generator) if item.id == prospect_id), None)


def get_prospect_report_by_id(
    prospect_id: str,
    generator: ProspectProfileGenerator | None = None,
) -> ProspectReportView | None:
    prospect = get_prospect_by_id(prospect_id, generator=generator)
    if prospect is None:
        return None

    return ProspectReportView(
        id=prospect.id,
        company_name=prospect.company_name,
        industry=prospect.industry,
        region=prospect.region,
        role=prospect.role,
        priority=prospect.bant.priority,
        bant_score=prospect.bant.score,
        summary_text=f"{prospect.company_name}属于 {prospect.industry} 行业，当前优先级 {prospect.bant.priority}，建议优先跟进。",
        profile=prospect.profile,
        bant=prospect.bant,
    )


def collect_prospects(
    request: CollectProspectsRequest,
    generator: ProspectProfileGenerator | None = None,
) -> ProspectCollectionResult:
    raw_items = _build_raw_items(
        industry=request.industry,
        regions=request.regions,
        roles=request.roles,
    )
    deduplicated_items = _deduplicate_and_rank_items(raw_items, generator=generator)
    limited_items = deduplicated_items[: request.limit]
    raw_count = len(raw_items)
    deduplicated_count = raw_count - len(deduplicated_items)
    validity_rate = round(len(deduplicated_items) / raw_count, 2)

    return ProspectCollectionResult(
        summary=ProspectCollectionSummary(
            requested=request.limit,
            returned=len(limited_items),
            deduplicated=deduplicated_count,
            validity_rate=validity_rate,
        ),
        items=limited_items,
    )
