import { Canvas } from "@react-three/fiber";
import { useGLTF, OrbitControls } from "@react-three/drei";

function Model() {
  const { scene } = useGLTF("/realistic_human_heart.glb");
  return <primitive object={scene} onClick={() => console.log("clicked!")} />;
}

export default function Viewer() {
  return (
    <Canvas camera={{ position: [0, 0, 5] }}>
      <ambientLight />
      <Model />
      <OrbitControls />
    </Canvas>
  );
}