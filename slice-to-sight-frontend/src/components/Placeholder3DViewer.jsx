// src/components/Placeholder3DViewer.jsx
//
// STAND-IN for Dev B's real Three.js/React-Three-Fiber viewer.
// This lets you build and test the "click organ -> see explanation" flow
// (Step 5) right now, without waiting for the real 3D mesh to exist.
//
// CONTRACT: Dev B's real component must accept the same props:
//   - meshUrl (string | null)
//   - onStructureClick(structureName: string)
// so swapping this out later is a one-line change in Workspace.jsx.

export default function Placeholder3DViewer({ meshUrl, onStructureClick }) {
  return (
    <div className="panel viewer-3d-placeholder">
      <h4>3D Anatomy View</h4>
      <div
        className="fake-organ"
        onClick={() => onStructureClick("spleen")}
        title="Click to simulate selecting the spleen"
      >
        🫘
      </div>
      <p className="subtitle">
        {meshUrl ? "Real mesh loaded (render it here, Dev B)" : "Placeholder — click the icon above"}
      </p>
    </div>
  );
}
