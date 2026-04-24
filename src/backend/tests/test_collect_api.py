from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app
from app.routers.prospects import get_profile_generator
from app.schemas.prospects import ProspectProfile


FIXTURE_DIRECTORY = Path(__file__).parent / "fixtures"
SAMPLE_CSV_PATH = FIXTURE_DIRECTORY / "prospects_enterprise_100.csv"


client = TestClient(app)


class ApiStubProfileGenerator:
    def generate(self, item: dict[str, object]) -> ProspectProfile:
        return ProspectProfile(
            industry=f"api-{item['industry']}",
            company_scale="200-500 人",
            pain_points=["API 自定义痛点"],
            needs=["API 自定义需求"],
        )


def test_list_prospects_supports_overridden_profile_generator_dependency() -> None:
    app.dependency_overrides[get_profile_generator] = lambda: ApiStubProfileGenerator()
    try:
        response = client.get("/api/v1/prospects")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["items"][0]["profile"]["industry"].startswith("api-")
    assert payload["data"]["items"][0]["profile"]["needs"] == ["API 自定义需求"]



def test_list_prospects_returns_existing_ranked_items() -> None:
    response = client.get("/api/v1/prospects")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "OK"
    assert payload["message"] == "prospects listed"
    assert payload["data"]["items"]
    first_item = payload["data"]["items"][0]
    assert first_item["id"] == "lead-1"
    assert first_item["bant"]["score"] >= payload["data"]["items"][-1]["bant"]["score"]



def test_list_prospects_applies_query_filters_to_seed_results() -> None:
    response = client.get(
        "/api/v1/prospects",
        params={
            "industry": "跨境电商",
            "region": "深圳,杭州",
            "roles": "创始人,销售总监",
            "limit": "20",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "OK"
    assert len(payload["data"]["items"]) == 20
    assert {item["region"] for item in payload["data"]["items"]} == {"深圳", "杭州"}
    assert {item["role"] for item in payload["data"]["items"]} == {"创始人", "销售总监"}
    assert all(item["industry"] == "跨境电商" for item in payload["data"]["items"])



def test_list_prospects_rejects_limit_below_one_with_standard_envelope() -> None:
    response = client.get("/api/v1/prospects", params={"limit": "0"})

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert "limit" in payload["message"]
    assert payload["data"] is None



def test_list_prospects_rejects_blank_region_query_with_standard_envelope() -> None:
    response = client.get(
        "/api/v1/prospects",
        params={
            "industry": "SaaS",
            "region": " , ",
            "roles": "CTO",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert "region" in payload["message"]
    assert payload["data"] is None



def test_list_prospects_openapi_documents_standard_error_responses() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    components = payload["components"]["schemas"]
    list_route = payload["paths"]["/api/v1/prospects"]["get"]
    export_route = payload["paths"]["/api/v1/prospects/export"]["get"]
    detail_route = payload["paths"]["/api/v1/prospects/{prospect_id}"]["get"]
    report_route = payload["paths"]["/api/v1/prospects/{prospect_id}/report"]["get"]
    collect_route = payload["paths"]["/api/v1/prospects/collect"]["post"]
    import_route = payload["paths"]["/api/v1/prospects/import"]["post"]

    assert "ApiErrorResponse" in components
    assert components["ApiErrorResponse"]["properties"].keys() >= {"code", "message", "data"}
    assert set(list_route["responses"].keys()) >= {"200", "422"}
    assert set(export_route["responses"].keys()) >= {"200", "422"}
    assert set(detail_route["responses"].keys()) >= {"200", "404", "422"}
    assert set(report_route["responses"].keys()) >= {"200", "404", "422"}
    assert set(collect_route["responses"].keys()) >= {"200", "422"}
    assert set(import_route["responses"].keys()) >= {"200", "400", "422"}
    assert list_route["responses"]["422"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ApiErrorResponse"
    assert export_route["responses"]["200"]["content"]["text/csv"]["schema"]["type"] == "string"
    assert export_route["responses"]["422"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ApiErrorResponse"
    assert detail_route["responses"]["404"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ApiErrorResponse"
    assert report_route["responses"]["404"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ApiErrorResponse"
    assert collect_route["responses"]["422"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ApiErrorResponse"
    assert import_route["responses"]["400"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ApiErrorResponse"
    assert import_route["responses"]["422"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ApiErrorResponse"



def test_get_prospect_detail_returns_single_report() -> None:
    response = client.get("/api/v1/prospects/lead-3")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "OK"
    assert payload["message"] == "prospect retrieved"
    assert payload["data"]["id"] == "lead-3"
    assert payload["data"]["profile"]["industry"] == "SaaS"


def test_get_prospect_detail_supports_overridden_profile_generator_dependency() -> None:
    app.dependency_overrides[get_profile_generator] = lambda: ApiStubProfileGenerator()
    try:
        response = client.get("/api/v1/prospects/lead-1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["profile"]["industry"] == "api-SaaS"
    assert payload["data"]["profile"]["needs"] == ["API 自定义需求"]


def test_get_prospect_detail_returns_404_with_standard_envelope() -> None:
    response = client.get("/api/v1/prospects/missing")

    assert response.status_code == 404
    payload = response.json()
    assert payload["code"] == "NOT_FOUND"
    assert payload["message"] == "prospect not found"
    assert payload["data"] is None



def test_method_not_allowed_returns_specific_standard_envelope() -> None:
    response = client.post("/api/v1/prospects/lead-1")

    assert response.status_code == 405
    payload = response.json()
    assert payload["code"] == "METHOD_NOT_ALLOWED"
    assert payload["message"]
    assert payload["data"] is None


def test_get_prospect_report_supports_overridden_profile_generator_dependency() -> None:
    app.dependency_overrides[get_profile_generator] = lambda: ApiStubProfileGenerator()
    try:
        response = client.get("/api/v1/prospects/lead-1/report")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["profile"]["industry"] == "api-SaaS"
    assert payload["data"]["profile"]["pain_points"] == ["API 自定义痛点"]



def test_get_prospect_report_returns_aggregated_view_model() -> None:
    response = client.get("/api/v1/prospects/lead-1/report")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "OK"
    assert payload["message"] == "prospect report retrieved"
    assert payload["data"]["priority"] == "A"
    assert payload["data"]["bant_score"] == 87
    assert payload["data"]["bant"]["priority"] == payload["data"]["priority"]
    assert payload["data"]["bant"]["score"] == payload["data"]["bant_score"]
    assert set(payload["data"]["profile"].keys()) == {"industry", "company_scale", "pain_points", "needs"}
    assert payload["data"]["summary_text"]


def test_get_prospect_report_returns_404_with_standard_envelope() -> None:
    response = client.get("/api/v1/prospects/missing/report")

    assert response.status_code == 404
    payload = response.json()
    assert payload["code"] == "NOT_FOUND"
    assert payload["message"] == "prospect report not found"
    assert payload["data"] is None


def test_collect_prospects_supports_overridden_profile_generator_dependency() -> None:
    app.dependency_overrides[get_profile_generator] = lambda: ApiStubProfileGenerator()
    try:
        response = client.post(
            "/api/v1/prospects/collect",
            json={
                "industry": "SaaS",
                "regions": ["深圳"],
                "roles": ["CTO"],
                "limit": 2,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["items"][0]["profile"]["industry"].startswith("api-")
    assert payload["data"]["items"][0]["profile"]["pain_points"] == ["API 自定义痛点"]



def test_collect_prospects_returns_ranked_leads_with_report_fields() -> None:
    response = client.post(
        "/api/v1/prospects/collect",
        json={
            "industry": "SaaS",
            "regions": ["深圳"],
            "roles": ["CTO"],
            "limit": 3,
        },
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["code"] == "OK"
    assert payload["message"] == "prospects collected"
    assert payload["data"]["summary"]["requested"] == 3
    assert payload["data"]["summary"]["returned"] == 3
    assert payload["data"]["summary"]["deduplicated"] >= 1
    assert payload["data"]["summary"]["validity_rate"] >= 0.8

    first_item = payload["data"]["items"][0]
    assert first_item["industry"] == "SaaS"
    assert first_item["region"] == "深圳"
    assert first_item["bant"]["priority"] in ["A", "B", "C", "D"]
    assert set(first_item["profile"].keys()) == {"industry", "company_scale", "pain_points", "needs"}


def test_collect_prospects_returns_100_plus_leads_for_phase_one_target() -> None:
    response = client.post(
        "/api/v1/prospects/collect",
        json={
            "industry": "SaaS",
            "regions": ["深圳"],
            "roles": ["CTO"],
            "limit": 100,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["summary"]["requested"] == 100
    assert payload["data"]["summary"]["returned"] == 100
    assert len(payload["data"]["items"]) == 100


def test_collect_prospects_keeps_three_plus_requested_regions_and_roles_visible() -> None:
    response = client.post(
        "/api/v1/prospects/collect",
        json={
            "industry": "SaaS",
            "regions": ["深圳", "广州", "杭州"],
            "roles": ["CTO", "技术副总裁", "技术总监"],
            "limit": 9,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    items = payload["data"]["items"]
    assert {item["region"] for item in items} == {"深圳", "广州", "杭州"}
    assert {item["role"] for item in items} == {"CTO", "技术副总裁", "技术总监"}
    assert payload["data"]["summary"]["returned"] == len(items)


def test_import_prospects_supports_overridden_profile_generator_dependency() -> None:
    app.dependency_overrides[get_profile_generator] = lambda: ApiStubProfileGenerator()
    try:
        response = client.post(
            "/api/v1/prospects/import",
            files={
                "file": (
                    "prospects.csv",
                    "company_name,website,contact_email,region,industry,role\n深圳样例科技,example.com,cto@example.com,深圳,SaaS,CTO\n".encode("utf-8"),
                    "text/csv",
                )
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["items"][0]["profile"]["industry"] == "api-SaaS"
    assert payload["data"]["items"][0]["profile"]["company_scale"] == "200-500 人"



def test_import_prospects_endpoint_accepts_csv_upload_and_returns_summary() -> None:
    response = client.post(
        "/api/v1/prospects/import",
        files={
            "file": (
                "prospects.csv",
                "company_name,website,contact_email,region,industry,role\n深圳样例科技,example.com,cto@example.com,深圳,SaaS,CTO\n".encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "OK"
    assert payload["message"] == "prospects imported"
    assert payload["data"]["summary"]["imported"] == 1
    assert payload["data"]["summary"]["skipped"] == 0
    assert payload["data"]["summary"]["failed"] == 0



def test_import_prospects_endpoint_accepts_100_sample_rows_for_phase_zero_dataset() -> None:
    response = client.post(
        "/api/v1/prospects/import",
        files={
            "file": (
                "prospects-enterprise-100.csv",
                SAMPLE_CSV_PATH.read_bytes(),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["summary"]["imported"] == 100
    assert payload["data"]["summary"]["skipped"] == 0
    assert payload["data"]["summary"]["failed"] == 0
    assert len(payload["data"]["items"]) == 100
    assert payload["data"]["items"][0]["id"] == "csv-lead-1"
    assert payload["data"]["items"][0]["company_name"] == "深圳SaaS样本企业001"
    assert payload["data"]["items"][-1]["id"] == "csv-lead-100"
    assert payload["data"]["items"][-1]["company_name"] == "北京企业服务样本企业100"


def test_list_available_data_sources_returns_mock_seed_and_csv_import() -> None:
    response = client.get("/api/v1/prospects/sources")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "OK"
    assert payload["message"] == "prospect data sources listed"
    assert payload["data"]["items"] == [
        {
            "key": "mock_seed",
            "label": "Mock seed",
            "type": "seed",
            "status": "available",
            "description": "内置示例线索数据，可直接用于 Phase 0/1 MVP 验证。",
        },
        {
            "key": "csv_import",
            "label": "CSV import",
            "type": "import",
            "status": "available",
            "description": "上传企业名单 CSV，走最小导入闭环并生成线索画像。",
        },
    ]



def test_export_prospects_supports_overridden_profile_generator_dependency() -> None:
    app.dependency_overrides[get_profile_generator] = lambda: ApiStubProfileGenerator()
    try:
        response = client.get("/api/v1/prospects/export")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    csv_text = response.text
    assert "profile_industry" in csv_text
    assert "api-SaaS" in csv_text
    assert "API 自定义需求" in csv_text



def test_export_prospects_returns_csv_attachment() -> None:
    response = client.get(
        "/api/v1/prospects/export",
        params={
            "industry": "跨境电商",
            "region": "深圳,杭州",
            "roles": "创始人,销售总监",
            "limit": "5",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment;" in response.headers["content-disposition"]
    assert ".csv" in response.headers["content-disposition"]

    lines = [line for line in response.text.strip().splitlines() if line]
    assert lines[0].startswith("id,company_name,region,industry,role")
    assert len(lines) == 6
    assert all(",跨境电商," in line or line.endswith(",跨境电商") or ",跨境电商," in f"{line}," for line in lines[1:])
    assert any(",深圳," in f"{line}," for line in lines[1:])
    assert any(",杭州," in f"{line}," for line in lines[1:])



def test_export_prospects_rejects_limit_below_one_with_standard_envelope() -> None:
    response = client.get("/api/v1/prospects/export", params={"limit": "0"})

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert "limit" in payload["message"]
    assert payload["data"] is None



def test_export_prospects_rejects_blank_region_query_with_standard_envelope() -> None:
    response = client.get(
        "/api/v1/prospects/export",
        params={
            "industry": "SaaS",
            "region": " , ",
            "roles": "CTO",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert "region" in payload["message"]
    assert payload["data"] is None



def test_import_prospects_endpoint_rejects_non_csv_upload_with_standard_envelope() -> None:
    response = client.post(
        "/api/v1/prospects/import",
        files={
            "file": (
                "prospects.txt",
                b"not,csv\n",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "BAD_REQUEST"
    assert payload["message"] == "csv file is required"
    assert payload["data"] is None


def test_import_prospects_endpoint_rejects_missing_file_with_standard_envelope() -> None:
    response = client.post("/api/v1/prospects/import")

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert "file" in payload["message"]
    assert payload["data"] is None


def test_import_prospects_endpoint_rejects_missing_required_headers_with_standard_envelope() -> None:
    response = client.post(
        "/api/v1/prospects/import",
        files={
            "file": (
                "prospects.csv",
                "company_name,website,region,industry,role\n深圳样例科技,example.com,深圳,SaaS,CTO\n".encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "BAD_REQUEST"
    assert "contact_email" in payload["message"]
    assert payload["data"] is None


def test_collect_prospects_rejects_blank_industry_with_standard_envelope() -> None:
    response = client.post(
        "/api/v1/prospects/collect",
        json={
            "industry": "   ",
            "regions": ["深圳"],
            "roles": ["CTO"],
            "limit": 3,
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert "industry" in payload["message"]
    assert payload["data"] is None


def test_collect_prospects_rejects_empty_roles_with_standard_envelope() -> None:
    response = client.post(
        "/api/v1/prospects/collect",
        json={
            "industry": "SaaS",
            "regions": ["深圳"],
            "roles": [],
            "limit": 3,
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert "roles" in payload["message"]
    assert payload["data"] is None
