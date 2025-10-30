import { memo, useCallback, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { useDrag } from "react-dnd";
import { getEmptyImage } from "react-dnd-html5-backend";
import clsx from "clsx";
import * as Tooltip from "@radix-ui/react-tooltip";

import type { TripRecord } from "../hooks/useTrips";

export type DragItem = {
  trip: TripRecord;
};

export type TripRenderShape = {
  trip: TripRecord;
  color: string;
  layout: {
    left: number;
    width: number;
    top: number;
    overflowStart: boolean;
    overflowEnd: boolean;
  };
  isPreview?: boolean;
};

const BLOCK_VARIANTS = {
  active: { opacity: 1, scale: 1 },
  ghosted: { opacity: 0.46, scale: 0.97 },
  preview: { opacity: 0.35, scale: 0.985 },
  dragging: { opacity: 0.22, scale: 0.96 },
} as const;

interface TripBlockProps {
  render: TripRenderShape;
  rowHeight: number;
  onContextMenu?: (event: React.MouseEvent<HTMLDivElement>, trip: TripRecord) => void;
  onResizeStart: (trip: TripRecord, edge: "start" | "end", clientX: number) => void;
  onDragStart?: (trip: TripRecord) => void;
  onDragEnd?: (trip: TripRecord) => void;
  onClick?: (trip: TripRecord) => void;
}

export const TripBlock = memo(
  ({ render, rowHeight, onContextMenu, onResizeStart, onDragStart, onDragEnd, onClick }: TripBlockProps) => {
    const blockRef = useRef<HTMLDivElement | null>(null);

    const [{ isDragging }, drag, preview] = useDrag(
      () => ({
        type: "TRIP",
        item: () => {
          if (onDragStart) {
            onDragStart(render.trip);
          }
          return { trip: render.trip } as DragItem;
        },
        collect: (monitor) => ({
          isDragging: monitor.isDragging(),
        }),
        end: (_item, monitor) => {
          if (!monitor.didDrop() && onDragEnd) {
            onDragEnd(render.trip);
          }
        },
      }),
      [render.trip, onDragStart, onDragEnd]
    );

    useEffect(() => {
      if (!blockRef.current || render.isPreview) {
        return;
      }
      drag(blockRef.current);
    }, [drag, render.trip, render.isPreview]);

    useEffect(() => {
      if (render.isPreview) {
        return;
      }
      preview(getEmptyImage(), { captureDraggingState: true });
    }, [preview, render.isPreview]);

    const handleResize = useCallback(
      (edge: "start" | "end", event: React.PointerEvent<HTMLDivElement>) => {
        event.stopPropagation();
        event.preventDefault();
        onResizeStart(render.trip, edge, event.clientX);
      },
      [render.trip, onResizeStart]
    );

    const { trip, layout, color, isPreview } = render;
    const minWidth = Math.max(layout.width, 32);

    const animationState = isPreview ? "preview" : trip.ghosted ? "ghosted" : "active";
    const animateVariant = isDragging ? "dragging" : animationState;

    const className = clsx(
      "trip-block absolute rounded-md shadow-sm z-20",
      "transition-[box-shadow,transform] duration-150",
      trip.ghosted && !isPreview && "ring-2 ring-offset-1 ring-white/70",
      isDragging ? "cursor-grabbing" : "cursor-grab",
      isPreview && "pointer-events-none border border-dashed border-white/70"
    );

    const tooltipLabel = trip.job_ref?.trim() || "No job reference";
    const tooltipDescription = `${trip.country} · ${trip.employee ?? "Unassigned"}`;

    const contextMenuHandler =
      isPreview || !onContextMenu
        ? undefined
        : (event: React.MouseEvent<HTMLDivElement>) => {
            event.preventDefault();
            onContextMenu(event, trip);
          };

    const content = (
      <motion.div
        ref={blockRef}
        layout
        layoutId={`trip-${trip.id}`}
        initial={false}
        variants={BLOCK_VARIANTS}
        animate={animateVariant}
        transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
        className={className}
        style={{
          left: layout.left,
          width: minWidth,
          top: layout.top + 4,
          height: rowHeight - 8,
          backgroundColor: color,
        }}
        title={`${trip.employee ?? ""} · ${trip.country} · ${trip.start_date} → ${trip.end_date}`}
        onContextMenu={contextMenuHandler}
        onClick={onClick ? () => onClick(trip) : undefined}
        data-trip-id={trip.id}
        data-employee-id={trip.employee_id}
        data-trip-country={trip.country}
      >
        <div className="flex h-full w-full flex-col justify-between overflow-hidden px-3 py-2 text-white">
          <div className="flex w-full items-center justify-between gap-2 text-xs font-semibold">
            <span className="truncate" aria-label="Job reference">
              {trip.job_ref || trip.country}
            </span>
            {trip.ghosted && !isPreview && (
              <span className="text-[10px] uppercase tracking-wide">Ghost</span>
            )}
            {isPreview && <span className="text-[10px] uppercase tracking-wide">Preview</span>}
          </div>
          <div className="text-[11px] leading-tight">
            <span>{trip.country}</span>
            <span className="mx-1">·</span>
            <span>
              {trip.start_date} → {trip.end_date}
            </span>
          </div>
        </div>
        {!isPreview && (
          <>
            <div
              className="trip-block__handle trip-block__handle--start"
              onPointerDown={(event) => handleResize("start", event)}
            />
            <div
              className="trip-block__handle trip-block__handle--end"
              onPointerDown={(event) => handleResize("end", event)}
            />
          </>
        )}
        {layout.overflowStart && <span className="trip-block__overflow trip-block__overflow--start" />}
        {layout.overflowEnd && <span className="trip-block__overflow trip-block__overflow--end" />}
      </motion.div>
    );

    if (isPreview) {
      return content;
    }

    return (
      <Tooltip.Provider delayDuration={60} skipDelayDuration={300} disableHoverableContent>
        <Tooltip.Root>
          <Tooltip.Trigger asChild>{content}</Tooltip.Trigger>
          <Tooltip.Portal>
            <Tooltip.Content
              side="top"
              align="center"
              className="z-50 rounded-md bg-slate-900 px-3 py-2 text-xs font-medium text-white shadow-lg"
              sideOffset={8}
            >
              <div className="flex flex-col gap-1">
                <span>{tooltipLabel}</span>
                <span className="text-[11px] font-normal text-slate-200">{tooltipDescription}</span>
              </div>
              <Tooltip.Arrow className="fill-slate-900" />
            </Tooltip.Content>
          </Tooltip.Portal>
        </Tooltip.Root>
      </Tooltip.Provider>
    );
  }
);

TripBlock.displayName = "TripBlock";


