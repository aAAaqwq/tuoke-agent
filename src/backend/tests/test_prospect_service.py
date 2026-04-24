from io import BytesIO
from pathlib import Path

import pytest

from app.schemas.prospects import CollectProspectsRequest, ProspectProfile
from app.services.prospect_service import (
    build_prospect_profile,
    collect_prospects,
    export_prospects_to_csv,
    get_prospect_by_id,
    get_prospect_report_by_id,
    import_prospects_from_csv,
    list_prospects,
)


FIXTURE_DIRECTORY = Path(__file__).parent / "fixtures"
SAMPLE_CSV_PATH = FIXTURE_DIRECTORY / "prospects_enterprise_100.csv"


def test_collect_prospects_deduplicates_and_sorts_by_bant_score() -> None:
    request = CollectProspectsRequest(
        industry="SaaS",
        regions=["深圳"],
        roles=["CTO"],
        limit=5,
    )

    result = collect_prospects(request)

    assert result.summary.requested == 5
    assert result.summary.returned == len(result.items)
    assert result.summary.deduplicated >= 1
    assert result.summary.validity_rate >= 0.8
    assert len(result.items) >= 3

    scores = [item.bant.score for item in result.items]
    assert scores == sorted(scores, reverse=True)
    assert all(item.profile.pain_points for item in result.items)
    assert all(item.profile.needs for item in result.items)


def test_collect_prospects_uses_all_requested_regions_and_roles() -> None:
    request = CollectProspectsRequest(
        industry="SaaS",
        regions=["深圳", "广州"],
        roles=["CTO", "技术副总裁"],
        limit=4,
    )

    result = collect_prospects(request)

    assert {item.region for item in result.items} == {"深圳", "广州"}
    assert {item.role for item in result.items} == {"CTO", "技术副总裁"}
    assert result.summary.deduplicated == 1
    assert result.summary.returned == len(result.items)


def test_collect_prospects_keeps_three_plus_requested_regions_and_roles_visible() -> None:
    request = CollectProspectsRequest(
        industry="SaaS",
        regions=["深圳", "广州", "杭州"],
        roles=["CTO", "技术副总裁", "技术总监"],
        limit=9,
    )

    result = collect_prospects(request)

    assert {item.region for item in result.items} == {"深圳", "广州", "杭州"}
    assert {item.role for item in result.items} == {"CTO", "技术副总裁", "技术总监"}


def test_collect_prospects_returns_100_plus_leads_for_phase_one_target() -> None:
    request = CollectProspectsRequest(
        industry="SaaS",
        regions=["深圳"],
        roles=["CTO"],
        limit=100,
    )

    result = collect_prospects(request)

    assert result.summary.requested == 100
    assert result.summary.returned == 100
    assert len(result.items) == 100
    assert result.summary.validity_rate >= 0.8
    assert len({item.id for item in result.items}) == 100


def test_collect_prospects_supports_custom_profile_generator() -> None:
    request = CollectProspectsRequest(
        industry="SaaS",
        regions=["深圳"],
        roles=["CTO"],
        limit=3,
    )

    result = collect_prospects(request, generator=StubProfileGenerator())

    assert result.items
    assert all(item.profile.industry == f"custom-{item.industry}" for item in result.items)
    assert all(item.profile.pain_points == ["自定义痛点"] for item in result.items)


class StubProfileGenerator:
    def generate(self, item: dict[str, object]) -> ProspectProfile:
        return ProspectProfile(
            industry=f"custom-{item['industry']}",
            company_scale="100-300 人",
            pain_points=["自定义痛点"],
            needs=["自定义需求"],
        )



def test_build_prospect_profile_supports_custom_generator() -> None:
    profile = build_prospect_profile(
        {
            "industry": "SaaS",
            "company_scale": "20-50 人",
            "pain_points": ["线索分散"],
            "needs": ["统一线索池"],
        },
        generator=StubProfileGenerator(),
    )

    assert profile.industry == "custom-SaaS"
    assert profile.company_scale == "100-300 人"
    assert profile.pain_points == ["自定义痛点"]
    assert profile.needs == ["自定义需求"]



def test_import_prospects_from_csv_supports_custom_profile_generator() -> None:
    csv_file = BytesIO(
        "company_name,website,contact_email,region,industry,role\n深圳样例科技,example.com,cto@example.com,深圳,SaaS,CTO\n".encode("utf-8")
    )

    result = import_prospects_from_csv(csv_file, generator=StubProfileGenerator())

    assert result.items[0].profile.industry == "custom-SaaS"
    assert result.items[0].profile.needs == ["自定义需求"]



def test_import_prospects_from_csv_imports_one_valid_row() -> None:
    csv_file = BytesIO(
        "company_name,website,contact_email,region,industry,role\n深圳样例科技,example.com,cto@example.com,深圳,SaaS,CTO\n".encode("utf-8")
    )

    result = import_prospects_from_csv(csv_file)

    assert result.summary.imported == 1
    assert result.summary.skipped == 0
    assert result.summary.failed == 0
    assert len(result.items) == 1
    assert result.items[0].company_name == "深圳样例科技"
    assert result.items[0].profile.industry == "SaaS"


def test_import_prospects_from_csv_rejects_missing_required_headers() -> None:
    csv_file = BytesIO("company_name,website,region,industry,role\n深圳样例科技,example.com,深圳,SaaS,CTO\n".encode("utf-8"))

    with pytest.raises(ValueError, match="contact_email"):
        import_prospects_from_csv(csv_file)


def test_import_prospects_from_csv_skips_rows_with_blank_required_values() -> None:
    csv_file = BytesIO(
        "company_name,website,contact_email,region,industry,role\n深圳样例科技,example.com,cto@example.com,深圳,SaaS,CTO\n,example2.com,owner@example.com,广州,SaaS,创始人\n".encode("utf-8")
    )

    result = import_prospects_from_csv(csv_file)

    assert result.summary.imported == 1
    assert result.summary.skipped == 1
    assert result.summary.failed == 0
    assert result.items[0].id == "csv-lead-1"



def test_import_prospects_from_csv_uses_contiguous_ids_for_successful_rows() -> None:
    csv_file = BytesIO(
        "company_name,website,contact_email,region,industry,role\n,broken.example.com,broken@example.com,深圳,SaaS,CTO\n广州样例科技,example2.com,owner@example.com,广州,SaaS,创始人\n".encode("utf-8")
    )

    result = import_prospects_from_csv(csv_file)

    assert result.summary.imported == 1
    assert result.summary.skipped == 1
    assert result.items[0].id == "csv-lead-1"
    assert result.items[0].company_name == "广州样例科技"



def test_import_prospects_from_csv_imports_100_sample_rows_for_phase_zero_dataset() -> None:
    csv_file = BytesIO(SAMPLE_CSV_PATH.read_bytes())

    result = import_prospects_from_csv(csv_file)

    assert result.summary.imported == 100
    assert result.summary.skipped == 0
    assert result.summary.failed == 0
    assert len(result.items) == 100
    assert result.items[0].id == "csv-lead-1"
    assert result.items[0].company_name == "深圳SaaS样本企业001"
    assert result.items[0].contact_email == "owner+001@sample-001.example.com"
    assert result.items[49].id == "csv-lead-50"
    assert result.items[49].company_name == "北京跨境电商样本企业050"
    assert result.items[49].role == "运营负责人"
    assert result.items[-1].id == "csv-lead-100"
    assert result.items[-1].company_name == "北京企业服务样本企业100"
    assert result.items[-1].website == "sample-100.example.com"


def test_list_prospects_supports_custom_profile_generator() -> None:
    result = list_prospects(generator=StubProfileGenerator())

    assert result.items
    assert result.items[0].profile.industry == f"custom-{result.items[0].industry}"
    assert result.items[0].profile.pain_points == ["自定义痛点"]



def test_export_prospects_to_csv_reuses_list_filters_and_order() -> None:
    csv_text = export_prospects_to_csv(
        industry="跨境电商",
        regions=["深圳", "杭州"],
        roles=["创始人", "销售总监"],
        limit=5,
    )

    lines = [line for line in csv_text.strip().splitlines() if line]
    assert lines[0].startswith("id,company_name,region,industry,role")
    assert len(lines) == 6
    assert ",lead-1," in f",{lines[1]},"
    assert all(",跨境电商," in f"{line}," for line in lines[1:])
    assert any(",深圳," in f"{line}," for line in lines[1:])
    assert any(",杭州," in f"{line}," for line in lines[1:])



def test_export_prospects_to_csv_supports_custom_profile_generator() -> None:
    csv_text = export_prospects_to_csv(generator=StubProfileGenerator())

    assert "profile_industry" in csv_text
    assert "custom-SaaS" in csv_text
    assert "自定义痛点" in csv_text
    assert "自定义需求" in csv_text



def test_list_prospects_returns_ranked_items() -> None:
    result = list_prospects()

    assert len(result.items) >= 3
    assert result.items[0].id == "lead-1"
    assert result.items[0].bant.score >= result.items[-1].bant.score


def test_get_prospect_by_id_returns_matching_item() -> None:
    prospect = get_prospect_by_id("lead-4")

    assert prospect is not None
    assert prospect.id == "lead-4"
    assert prospect.profile.company_scale == "20-50 人"


def test_get_prospect_by_id_supports_custom_profile_generator() -> None:
    prospect = get_prospect_by_id("lead-1", generator=StubProfileGenerator())

    assert prospect is not None
    assert prospect.id == "lead-1"
    assert prospect.profile.industry == "custom-SaaS"
    assert prospect.profile.needs == ["自定义需求"]


def test_get_prospect_by_id_returns_none_for_missing_item() -> None:
    assert get_prospect_by_id("missing") is None


def test_get_prospect_report_by_id_aggregates_delivery_fields() -> None:
    report = get_prospect_report_by_id("lead-1")

    assert report is not None
    assert report.id == "lead-1"
    assert report.company_name == "深圳云帆 SaaS 科技"
    assert report.priority == "A"
    assert report.bant_score == 87
    assert report.summary_text == "深圳云帆 SaaS 科技属于 SaaS 行业，当前优先级 A，建议优先跟进。"
    assert report.profile.company_scale == "100-300 人"


def test_get_prospect_report_by_id_supports_custom_profile_generator() -> None:
    report = get_prospect_report_by_id("lead-1", generator=StubProfileGenerator())

    assert report is not None
    assert report.id == "lead-1"
    assert report.profile.industry == "custom-SaaS"
    assert report.profile.pain_points == ["自定义痛点"]
    assert report.priority == "A"


def test_get_prospect_report_by_id_returns_none_for_missing_item() -> None:
    assert get_prospect_report_by_id("missing") is None
