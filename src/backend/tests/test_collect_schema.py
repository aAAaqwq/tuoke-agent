from app.schemas.prospects import CollectProspectsRequest


def test_collect_request_normalizes_roles_and_limit() -> None:
    request = CollectProspectsRequest(
        industry=" SaaS ",
        regions=[" 深圳 ", "上海"],
        roles=[" CTO ", "技术负责人"],
        limit=250,
    )

    assert request.industry == "SaaS"
    assert request.regions == ["深圳", "上海"]
    assert request.roles == ["CTO", "技术负责人"]
    assert request.limit == 100
