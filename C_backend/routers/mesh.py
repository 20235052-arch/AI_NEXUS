from fastapi import APIRouter

from services.meshing import MeshService

router = APIRouter(
    prefix="/mesh",
    tags=["Mesh"]
)

@router.get("/{study_id}/{structure}")
def get_mesh(study_id: str, structure: str):

    service = MeshService(study_id)

    service.create_mesh()

    return {
    "study_id": study_id,
    "structure": structure,
    "mesh_url": f"http://localhost:8000/storage/{study_id}/spleen.obj",
    "format": "obj",
}