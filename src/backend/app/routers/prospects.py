from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from fastapi.responses import PlainTextResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.schemas.common import ApiErrorResponse, ApiResponse
from app.schemas.prospects import (
    CollectProspectsRequest,
    ProspectCollectionResult,
    ProspectDataSourceListResult,
    ProspectImportResult,
    ProspectItem,
    ProspectListQuery,
    ProspectListResult,
    ProspectReportView,
)
from app.services.prospect_service import (
    MockProspectProfileGenerator,
    ProspectProfileGenerator,
    collect_prospects,
    export_prospects_to_csv,
    get_prospect_by_id,
    get_prospect_report_by_id,
    import_prospects_from_csv,
    list_available_data_sources,
    list_prospects,
)

router = APIRouter(prefix="/prospects", tags=["prospects"])

ERROR_RESPONSES = {
    400: {"model": ApiErrorResponse, "description": "Bad request"},
    404: {"model": ApiErrorResponse, "description": "Not found"},
    422: {"model": ApiErrorResponse, "description": "Validation error"},
}

LIST_ERROR_RESPONSES = {422: ERROR_RESPONSES[422]}
DETAIL_ERROR_RESPONSES = {404: ERROR_RESPONSES[404], 422: ERROR_RESPONSES[422]}
IMPORT_ERROR_RESPONSES = {400: ERROR_RESPONSES[400], 422: ERROR_RESPONSES[422]}


def get_profile_generator() -> ProspectProfileGenerator:
    return MockProspectProfileGenerator()


def get_prospect_list_query(
    industry: Annotated[
        str,
        Query(
            min_length=1,
            description="目标行业，不能为空。",
            openapi_examples={"default": {"summary": "示例", "value": "SaaS"}},
        ),
    ] = "SaaS",
    region: Annotated[
        str,
        Query(
            min_length=1,
            description="目标地区，使用逗号分隔，例如：深圳,杭州。",
            openapi_examples={"csv": {"summary": "逗号分隔地区", "value": "深圳,杭州"}},
        ),
    ] = "深圳, 广州",
    roles: Annotated[
        str,
        Query(
            min_length=1,
            description="目标角色，使用逗号分隔，例如：CTO,技术副总裁。",
            openapi_examples={"csv": {"summary": "逗号分隔角色", "value": "CTO,技术副总裁"}},
        ),
    ] = "CTO, 技术副总裁",
    limit: Annotated[int, Query(ge=1, le=100, description="返回条数，范围 1-100。")] = 100,
) -> ProspectListQuery:
    try:
        return ProspectListQuery(industry=industry, region=region, roles=roles, limit=limit)
    except ValidationError as error:
        normalized_errors = [
            {
                **detail,
                "loc": ("query", *detail["loc"]),
            }
            for detail in error.errors()
        ]
        raise RequestValidationError(normalized_errors) from error


@router.get("", response_model=ApiResponse[ProspectListResult], responses=LIST_ERROR_RESPONSES)
def list_prospect_route(
    query: ProspectListQuery = Depends(get_prospect_list_query),
    generator: ProspectProfileGenerator = Depends(get_profile_generator),
) -> ApiResponse[ProspectListResult]:
    result = list_prospects(
        industry=query.industry,
        regions=query.regions,
        roles=query.normalized_roles,
        limit=query.limit,
        generator=generator,
    )
    return ApiResponse(code="OK", message="prospects listed", data=result)


@router.get("/sources", response_model=ApiResponse[ProspectDataSourceListResult])
def list_prospect_data_sources_route() -> ApiResponse[ProspectDataSourceListResult]:
    result = list_available_data_sources()
    return ApiResponse(code="OK", message="prospect data sources listed", data=result)


@router.get(
    "/export",
    response_class=PlainTextResponse,
    responses={
        200: {
            "description": "Prospects exported as CSV",
            "content": {"text/csv": {"schema": {"type": "string", "format": "binary"}}},
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/ApiErrorResponse"}}
            },
        },
    },
)
def export_prospect_route(
    query: ProspectListQuery = Depends(get_prospect_list_query),
    generator: ProspectProfileGenerator = Depends(get_profile_generator),
) -> PlainTextResponse:
    csv_text = export_prospects_to_csv(
        industry=query.industry,
        regions=query.regions,
        roles=query.normalized_roles,
        limit=query.limit,
        generator=generator,
    )
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="prospects-export.csv"'},
    )


@router.get("/{prospect_id}", response_model=ApiResponse[ProspectItem], responses=DETAIL_ERROR_RESPONSES)
def get_prospect_route(
    prospect_id: str,
    response: Response,
    generator: ProspectProfileGenerator = Depends(get_profile_generator),
) -> ApiResponse[ProspectItem]:
    result = get_prospect_by_id(prospect_id, generator=generator)
    if result is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ApiResponse(code="NOT_FOUND", message="prospect not found", data=None)
    return ApiResponse(code="OK", message="prospect retrieved", data=result)


@router.get(
    "/{prospect_id}/report",
    response_model=ApiResponse[ProspectReportView],
    responses=DETAIL_ERROR_RESPONSES,
)
def get_prospect_report_route(
    prospect_id: str,
    response: Response,
    generator: ProspectProfileGenerator = Depends(get_profile_generator),
) -> ApiResponse[ProspectReportView]:
    result = get_prospect_report_by_id(prospect_id, generator=generator)
    if result is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ApiResponse(code="NOT_FOUND", message="prospect report not found", data=None)
    return ApiResponse(code="OK", message="prospect report retrieved", data=result)


@router.post("/collect", response_model=ApiResponse[ProspectCollectionResult], responses=LIST_ERROR_RESPONSES)
def collect_prospect_route(
    request: CollectProspectsRequest,
    generator: ProspectProfileGenerator = Depends(get_profile_generator),
) -> ApiResponse[ProspectCollectionResult]:
    result = collect_prospects(request, generator=generator)
    return ApiResponse(code="OK", message="prospects collected", data=result)


@router.post(
    "/import",
    response_model=ApiResponse[ProspectImportResult],
    responses=IMPORT_ERROR_RESPONSES,
)
def import_prospect_route(
    response: Response,
    file: UploadFile = File(...),
    generator: ProspectProfileGenerator = Depends(get_profile_generator),
) -> ApiResponse[ProspectImportResult]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ApiResponse(code="BAD_REQUEST", message="csv file is required", data=None)

    try:
        result = import_prospects_from_csv(file.file, generator=generator)
    except (UnicodeDecodeError, ValueError) as error:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ApiResponse(code="BAD_REQUEST", message=str(error), data=None)

    return ApiResponse(code="OK", message="prospects imported", data=result)
