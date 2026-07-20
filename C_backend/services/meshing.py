"""
Generate a 3D mesh from a segmented spleen mask.
Input:
    storage/<study_id>/mask.npy
    storage/<study_id>/spacing.npy
Output:
    storage/<study_id>/spleen.obj
"""
from pathlib import Path

import numpy as np
from skimage.measure import marching_cubes 
'''This is the algorithm that converts voxels
into triangles'''

STORAGE = Path("storage")

class MeshService:

    def __init__(self, study_id: str):
        self.study_id = study_id
        self.study_dir = STORAGE / study_id

    def load_data(self):
        """
        Load the binary spleen mask and voxel spacing.
        """

        mask = np.load(self.study_dir / "mask.npy")
        spacing = np.load(self.study_dir / "spacing.npy")

        return mask, spacing
    
    def generate_mesh(self, mask, spacing):
        """
        Generate a triangle mesh using Marching Cubes.
        """

        vertices, faces, normals, values = marching_cubes(
            mask,
            level=0.5,
            spacing=spacing,
        )

        return vertices, faces
    
    def save_obj(self, vertices, faces):
        """
        Save the mesh as an OBJ file.
        """

        obj_path = self.study_dir / "spleen.obj"

        with open(obj_path, "w") as file:

            # Write vertices
            for vertex in vertices:
                file.write(
                    f"v {vertex[0]} {vertex[1]} {vertex[2]}\n"
                )

            # Write triangle faces
            for face in faces:
                file.write(
                    f"f {face[0]+1} {face[1]+1} {face[2]+1}\n"
                )
    
    def create_mesh(self):
        """
        Complete 3D reconstruction pipeline.
        """

        mask, spacing = self.load_data()

        vertices, faces = self.generate_mesh(
            mask,
            spacing,
        )

        self.save_obj(
            vertices,
            faces,
        )

        return vertices, faces