from fastapi import APIRouter

from services.segmentation import SegmentationService

router = APIRouter(
    prefix="/segment",
    tags=["Segmentation"]
)

@router.post("/{study_id}")
def segment(study_id: str):

    service = SegmentationService(study_id)

    service.segment()

    return {
        "message": "Segmentation completed."
    }