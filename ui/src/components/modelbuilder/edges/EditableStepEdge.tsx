import {
  BaseEdge,
  type Edge,
  type EdgeProps,
  useReactFlow,
} from '@xyflow/react';
import { useState } from 'react';
import { useModelStore } from '../../../store/useModelStore';

type StepData = {
  viaX?: number;
  viaY?: number;
};

export function EditableStepEdge(props: EdgeProps<Edge<StepData>>) {
  const { id, sourceX, sourceY, targetX, targetY, markerEnd, style, selected } = props;
  const setEdges = useModelStore((s) => s.setEdges);
  const { screenToFlowPosition } = useReactFlow();
  const [isHovered, setIsHovered] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const dx = targetX - sourceX;
  const dy = targetY - sourceY;

  const data = props.data ?? {};
  const viaX = data.viaX ?? sourceX + dx * 0.5;
  const viaY = data.viaY ?? sourceY + dy * 0.5;

  const path = [
    `M ${sourceX},${sourceY}`,
    `L ${viaX},${sourceY}`,
    `L ${viaX},${viaY}`,
    `L ${targetX},${viaY}`,
    `L ${targetX},${targetY}`,
  ].join(' ');

  const updateEdge = (patch: Partial<StepData>) => {
    setEdges((prev) =>
      prev.map((edge) =>
        edge.id === id
          ? {
              ...edge,
              data: {
                ...(edge.data ?? {}),
                ...patch,
              },
            }
          : edge
      )
    );
  };

  const bindDrag = (onMove: (x: number, y: number) => void) => (e: React.MouseEvent<SVGCircleElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
    setIsHovered(true);

    const onMouseMove = (evt: MouseEvent) => {
      const pos = screenToFlowPosition({ x: evt.clientX, y: evt.clientY });
      onMove(pos.x, pos.y);
    };

    const onMouseUp = () => {
      setIsDragging(false);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  // Two central controls to avoid overlap with node-side reconnect points.
  const viaXHandle = { x: viaX, y: sourceY + (viaY - sourceY) * 0.5 };
  const viaYHandle = { x: viaX + (targetX - viaX) * 0.5, y: viaY };

  const handleVisible = selected || isHovered || isDragging;
  const visualClass = `mb-step-edge__handle nodrag nopan${selected || isHovered || isDragging ? ' mb-step-edge__handle--active' : ''}`;

  return (
    <>
      <BaseEdge id={id} path={path} markerEnd={markerEnd} style={style} />

      <path
        d={path}
        fill="none"
        stroke="transparent"
        strokeWidth={18}
        className="mb-step-edge__hover-band"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => {
          if (!isDragging) setIsHovered(false);
        }}
      />

      {handleVisible && (
        <>
          <circle
            className="mb-step-edge__handle-hit nodrag nopan"
            cx={viaXHandle.x}
            cy={viaXHandle.y}
            r={9}
            style={{ pointerEvents: 'all', cursor: 'ew-resize' }}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => {
              if (!isDragging) setIsHovered(false);
            }}
            onMouseDown={bindDrag((x) => updateEdge({ viaX: x }))}
          />
          <circle
            className="mb-step-edge__handle-hit nodrag nopan"
            cx={viaYHandle.x}
            cy={viaYHandle.y}
            r={9}
            style={{ pointerEvents: 'all', cursor: 'ns-resize' }}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => {
              if (!isDragging) setIsHovered(false);
            }}
            onMouseDown={bindDrag((_, y) => updateEdge({ viaY: y }))}
          />

          <circle className={visualClass} cx={viaXHandle.x} cy={viaXHandle.y} r={3} />
          <circle className={visualClass} cx={viaYHandle.x} cy={viaYHandle.y} r={3} />
        </>
      )}
    </>
  );
}
