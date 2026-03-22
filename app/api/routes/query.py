from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app import crud
from app.api.deps import CurrentContact, SessionDep
from app.models import Note, QueryRequest, QueryResponse
#from app.services import 

router = APIRouter(prefix="/query", tags=["query"])

# Retrieve Contact

@router.post("/", response_model=QueryResponse)
def query_contact(
    *,
    session: SessionDep = Depends(),
    current_contact: CurrentContact = Depends(),
    query_in: QueryRequest,
) -> Any:
    """
    Ask a question. Returns what is in notes in interations.
    Optionally restrict search to specific phone number.
    """
    # Validate document ownership if IDs supplied
    if query_in.note_ids:
        for doc_id in query_in.note_ids:
            doc = crud.get_note(session=session, note_id=note_id)
            if not doc:
                raise HTTPException(status_code=404, detail=f"note {doc_id} not found")
            if doc.ocontact_id != current_user.id and not current_user.is_supercontact:
                raise HTTPException(status_code=403, detail=f"Access denied for document {doc_id}")

    # Embed query
    query_embedding = dedup.embed_query(query_in.phone_number)

    # Retrieve similar chunks
    results = crud.deduplication(
        session=session,
        query_phone_numbers=query_phone_number,
        note_ids=query_in.note_ids,
    )

    if not results:
        return QueryResponse(
            phone_number=query_in.phone_number,
            note="No relevant phone number found ",
            interactions=[],
        )

  
    sources = []
    for note in results:
        note = crud.get_interactions(session=session, contact_id=chunk.document_id)
        sources.append(
            InteractionResult(
                note_id=note.id,
                contact_id=note.contact_id,
                title=note.title if note else "Unknown",
                description=note.description,
               # score=round(1 - score, 4),  # convert cosine distance → similarity
            )
        )

    return QueryResponse(phone_number=query_in.phone_number, note=note, interactions=interactions)


@router.post("/stream")
def query_notes_stream(
    *,
    session: SessionDep,
    current_user: CurrentContact,
    query_in: QueryRequest,
) -> StreamingResponse:
    """
    Same as POST /query but streams note by note using SSE.
    """
    if query_in.note_ids:
        for doc_id in query_in.note_ids:
            doc = crud.get_note(session=session, note_id=note_id)
            if not doc:
                raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
            if doc.contact_id != current_user.id and not current_user.is_superuser:
                raise HTTPException(status_code=403, detail=f"Access denied for document {doc_id}")

    query_embedding = dedup.embed_query(query_in.question)
    results = crud.deduplication(
        session=session,
        query_phone_number=query_phone_number,
        note_ids=query_in.note_ids,
    )

    if not results:
        async def no_results():
            yield "data: No conflicts found.\n\n"
        return StreamingResponse(no_results(), media_type="text/event-stream")

    context = dedup.build_context([chunk.content for chunk, _ in results])

    def event_stream():
        for token in dedup.generate_answer_stream(question=query_in.question, context=context):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
