// src/components/SpleenViewer3D.jsx
//
// Real 3D viewer — replaces Placeholder3DViewer.jsx.
// Same contract, so swapping it in Workspace.jsx is a one-line change:
//   - meshUrl (string | null)
//   - onStructureClick(structureName: string)
//
// KNOWN GAP (see API_CONTRACT.md): the mesh does NOT come from Dev C's
// backend. It's Dev D's marching-cubes output, and there is currently no
// endpoint anywhere in the contract that serves it. meshUrl being null
// is the expected/default state until that's resolved — this component
// shows an honest "waiting" state rather than pretending a mesh exists.
//
// This MVP only ever segments one organ (see App.jsx: organ is hardcoded
// to "spleen"), so a click anywhere on the mesh reports "spleen" — same
// behavior as the placeholder. If multi-structure picking is ever added,
// this is the spot to swap in per-submesh names from the mesh itself.

import { Suspense, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";

function Mesh({ url, onStructureClick }) {
  const { scene } = useGLTF(url);
  const meshRef = useRef();

  return (
    <primitive
      ref={meshRef}
      object={scene}
      onClick={(e) => {
        e.stopPropagation();
        onStructureClick("spleen");
      }}
      onPointerOver={() => (document.body.style.cursor = "pointer")}
      onPointerOut={() => (document.body.style.cursor = "default")}
    />
  );
}

function Loading() {
  return null; // Suspense fallback inside the Canvas must be a 3D-safe no-op
}

export default function SpleenViewer3D({ meshUrl, onStructureClick }) {
  if (!meshUrl) {
    return (
      <div className="panel viewer-3d">
        <h4>3D Anatomy View</h4>
        <p className="subtitle">
          Waiting on the 3D mesh (Dev D's segmentation pipeline hasn't
          produced one for this study yet).
        </p>
      </div>
    );
  }

  return (
    <div className="panel viewer-3d">
      <h4>3D Anatomy View</h4>
      <div className="viewer-3d-canvas">
        <Canvas camera={{ position: [0, 0, 150], fov: 45 }}>
          <ambientLight intensity={0.6} />
          <directionalLight position={[5, 5, 5]} intensity={1} />
          <Suspense fallback={<Loading />}>
            <Mesh url={meshUrl} onStructureClick={onStructureClick} />
          </Suspense>
          <OrbitControls enableDamping dampingFactor={0.1} />
        </Canvas>
      </div>
      <p className="subtitle">Drag to rotate · scroll to zoom · click the organ</p>
    </div>
  );
}
