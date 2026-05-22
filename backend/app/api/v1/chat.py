from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.chat_service import RepositoryChatService

router = APIRouter(prefix="/chat", tags=["chat"])
limiter = Limiter(key_func=get_remote_address)


def get_repository_chat_service() -> RepositoryChatService:
    return RepositoryChatService()


@router.post("/query", response_model=ChatQueryResponse)
@limiter.limit("10/minute")
async def query_repository(
    request: Request,
    payload: ChatQueryRequest,
    service: RepositoryChatService = Depends(get_repository_chat_service),
) -> ChatQueryResponse:
    try:
        return await service.ask(str(payload.repo_url), payload.question)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
