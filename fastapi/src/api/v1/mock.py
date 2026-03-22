from fastapi import APIRouter, Depends

from src.schemas.mock import MockDocument, MockProject, MockReport
from src.utils.auth import RequestUser
from src.utils.permissions import require_permission

router = APIRouter(prefix="/mock", tags=["mock"])

MOCK_401_RESPONSE = {
    "description": "Пользователь не аутентифицирован или access token невалиден.",
}
MOCK_403_RESPONSE = {
    "description": "У текущего пользователя нет права доступа к запрашиваемому mock-ресурсу.",
}


@router.get(
    "/projects",
    response_model=list[MockProject],
    summary="Получить mock-проекты",
    description=(
        "Возвращает список mock-проектов. Доступ разрешен только пользователям с правом `mock:projects:list/read`."
    ),
    responses={
        401: MOCK_401_RESPONSE,
        403: MOCK_403_RESPONSE,
    },
)
async def list_mock_projects(
    current_user: RequestUser = Depends(require_permission("mock:projects:list", "read")),
) -> list[MockProject]:
    """Возвращает список mock-проектов для демонстрации RBAC."""

    return [
        MockProject(id=1, name="Mobile Banking", status="active"),
        MockProject(id=2, name="Admin Portal", status="draft"),
    ]


@router.get(
    "/reports",
    response_model=list[MockReport],
    summary="Получить mock-отчеты",
    description=(
        "Возвращает список mock-отчетов. Доступ разрешен только пользователям с правом `mock:reports:list/read`."
    ),
    responses={
        401: MOCK_401_RESPONSE,
        403: MOCK_403_RESPONSE,
    },
)
async def list_mock_reports(
    current_user: RequestUser = Depends(require_permission("mock:reports:list", "read")),
) -> list[MockReport]:
    """Возвращает список mock-отчетов для демонстрации RBAC."""

    return [
        MockReport(id=1, title="Weekly KPI", period="2026-W11"),
        MockReport(id=2, title="Monthly Revenue", period="2026-03"),
    ]


@router.get(
    "/documents",
    response_model=list[MockDocument],
    summary="Получить mock-документы",
    description=(
        "Возвращает список mock-документов. Доступ разрешен только пользователям с правом `mock:documents:list/read`."
    ),
    responses={
        401: MOCK_401_RESPONSE,
        403: MOCK_403_RESPONSE,
    },
)
async def list_mock_documents(
    current_user: RequestUser = Depends(require_permission("mock:documents:list", "read")),
) -> list[MockDocument]:
    """Возвращает список mock-документов для демонстрации RBAC."""

    return [
        MockDocument(id=1, filename="security-policy.pdf", owner="admin1@em.ru"),
        MockDocument(id=2, filename="roadmap.docx", owner="manager1@em.ru"),
    ]
