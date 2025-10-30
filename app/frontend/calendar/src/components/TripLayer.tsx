
// Phase 3.4 Layout Stabilization

import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MouseEvent as ReactMouseEvent } from "react";
import { addDays, formatISO, isAfter, isBefore, parseISO } from "date-fns";

import type { TripRecord } from "../hooks/useTrips";
import type { EmployeeRecord } from "../hooks/useEmployees";
import { TripBlock } from "./TripBlock";
import type { TripRenderShape } from "./TripBlock";

const HORIZONTAL_PADDING = 4;

export type TripLayerDay = {
  date: Date;
  iso: string;
  columnIndex: number;
  weekIndex: number;
  weekdayLabel: string;
  dateLabel: string;
  fullLabel: string;
  isWeekend: boolean;
};

type TripLayerUpdateArgs = {
  id: number | string;
  patch: Partial<Pick<TripRecord, "start_date" | "end_date">>;
};

type TripLayerProps = {
  weekStartISO: string;
  daySlots: TripLayerDay[];
  colWidth: number;
  rowHeight: number;
  employees: EmployeeRecord[];
  trips: TripRecord[];
  offsetLeft: number;
  offsetTop: number;
  calendarWidth: number;
  getTripColor: (trip: TripRecord) => string;
  onTripUpdate: (args: TripLayerUpdateArgs) => void;
  onTripEdit: (trip: TripRecord) => void;
  onTripDuplicate: (trip: TripRecord) => void;
  onTripDelete: (trip: TripRecord) => void;
  onTripGhostToggle: (trip: TripRecord) => void;
  onTripCopy: (trip: TripRecord) => void;
  onTripPaste: (trip: TripRecord) => void;
  canPaste: () => boolean;
  onTripClick?: (trip: TripRecord) => void;
};

const TripLayerComponent: React.FC<TripLayerProps> = ({
  weekStartISO: _weekStartISO,
  daySlots,
  colWidth,
  rowHeight,
  employees,
  trips,
  offsetLeft,
  offsetTop,
  calendarWidth,
  getTripColor,
  onTripUpdate,
  onTripEdit,
  onTripDuplicate,
  onTripDelete,
  onTripGhostToggle,
  onTripCopy,
  onTripPaste,
  canPaste,
  onTripClick,
}) => {
  type ContextMenuState = {
    trip: TripRecord;
    x: number;
    y: number;
  };

  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);
  const resizeStateRef = useRef<{
    trip: TripRecord;
    edge: "start" | "end";
    originX: number;
    startDate: Date;
    endDate: Date;
  } | null>(null);

  const rowIndexMap = useMemo(() => {
    const map = new Map<number, number>();
    employees.forEach((employee, index) => {
      map.set(employee.id, index);
    });
    return map;
  }, [employees]);

  const dayIndexMap = useMemo(() => {
    const map = new Map<string, number>();
    daySlots.forEach((slot, index) => {
      map.set(slot.iso, index);
    });
    return map;
  }, [daySlots]);

  const renderedTrips = useMemo<TripRenderShape[]>(() => {
    if (!daySlots.length || !employees.length) {
      return [];
    }

    const firstVisibleDate = parseISO(daySlots[0].iso);
    const lastVisibleDate = parseISO(daySlots[daySlots.length - 1].iso);

    const shapes: TripRenderShape[] = [];

    trips.forEach((trip) => {
      const rowIndex = rowIndexMap.get(trip.employee_id) ?? rowIndexMap.get(-1);
      if (rowIndex === undefined) {
        return;
      }

      const start = parseISO(trip.start_date);
      const end = parseISO(trip.end_date);
      if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
        return;
      }

      if (isAfter(start, lastVisibleDate) || isBefore(end, firstVisibleDate)) {
        return;
      }

      const startIso = formatISO(start, { representation: "date" });
      const endIso = formatISO(end, { representation: "date" });

      let startIndex = dayIndexMap.get(startIso);
      let endIndex = dayIndexMap.get(endIso);

      const overflowStart = startIndex === undefined && isBefore(start, firstVisibleDate);
      const overflowEnd = endIndex === undefined && isAfter(end, lastVisibleDate);

      if (startIndex === undefined) {
        startIndex = overflowStart ? 0 : dayIndexMap.get(startIso);
      }
      if (endIndex === undefined) {
        endIndex = overflowEnd ? daySlots.length - 1 : dayIndexMap.get(endIso);
      }

      if (startIndex === undefined || endIndex === undefined) {
        return;
      }

      if (endIndex < startIndex) {
        const temp = startIndex;
        startIndex = endIndex;
        endIndex = temp;
      }

      const span = Math.max(endIndex - startIndex + 1, 1);
      const width = Math.max(span * colWidth - HORIZONTAL_PADDING * 2, Math.min(colWidth, 32));
      const left = offsetLeft + startIndex * colWidth + HORIZONTAL_PADDING;
      const top = rowIndex * rowHeight;

      shapes.push({
        trip,
        color: getTripColor(trip),
        layout: {
          left,
          width,
          top,
          overflowStart,
          overflowEnd,
        },
      });
    });

    return shapes.sort((a, b) => {
      if (a.layout.top === b.layout.top) {
        return a.layout.left - b.layout.left;
      }
      return a.layout.top - b.layout.top;
    });
  }, [daySlots, employees.length, trips, rowIndexMap, dayIndexMap, colWidth, offsetLeft, rowHeight, getTripColor]);

  const closeContextMenu = useCallback(() => {
    setContextMenu(null);
  }, []);

  useEffect(() => {
    if (!contextMenu) {
      return;
    }
    const handleGlobalClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.closest?.("[data-calendar-context-menu]")) {
        return;
      }
      closeContextMenu();
    };
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        closeContextMenu();
      }
    };

    window.addEventListener("click", handleGlobalClick, true);
    window.addEventListener("contextmenu", closeContextMenu);
    window.addEventListener("keydown", handleEscape);
    return () => {
      window.removeEventListener("click", handleGlobalClick, true);
      window.removeEventListener("contextmenu", closeContextMenu);
      window.removeEventListener("keydown", handleEscape);
    };
  }, [contextMenu, closeContextMenu]);

  const handleContextMenu = useCallback(
    (event: ReactMouseEvent<HTMLDivElement>, trip: TripRecord) => {
      event.preventDefault();
      event.stopPropagation();
      setContextMenu({
        trip,
        x: event.clientX,
        y: event.clientY,
      });
    },
    []
  );

  const handleTripEdit = useCallback(() => {
    if (!contextMenu) return;
    onTripEdit(contextMenu.trip);
    closeContextMenu();
  }, [contextMenu, onTripEdit, closeContextMenu]);

  const handleTripDuplicate = useCallback(() => {
    if (!contextMenu) return;
    onTripDuplicate(contextMenu.trip);
    closeContextMenu();
  }, [contextMenu, onTripDuplicate, closeContextMenu]);

  const handleTripDelete = useCallback(() => {
    if (!contextMenu) return;
    onTripDelete(contextMenu.trip);
    closeContextMenu();
  }, [contextMenu, onTripDelete, closeContextMenu]);

  const handleTripToggleGhost = useCallback(() => {
    if (!contextMenu) return;
    onTripGhostToggle(contextMenu.trip);
    closeContextMenu();
  }, [contextMenu, onTripGhostToggle, closeContextMenu]);

  const handleTripCopy = useCallback(() => {
    if (!contextMenu) return;
    onTripCopy(contextMenu.trip);
    closeContextMenu();
  }, [contextMenu, onTripCopy, closeContextMenu]);

  const handleTripPaste = useCallback(() => {
    if (!contextMenu) return;
    onTripPaste(contextMenu.trip);
    closeContextMenu();
  }, [contextMenu, onTripPaste, closeContextMenu]);

  const handleResizeStart = useCallback(
    (trip: TripRecord, edge: "start" | "end", clientX: number) => {
      const startDate = parseISO(trip.start_date);
      const endDate = parseISO(trip.end_date);
      if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
        return;
      }

      const state = { trip, edge, originX: clientX, startDate, endDate };
      resizeStateRef.current = state;

      const handlePointerUp = (event: PointerEvent) => {
        if (!resizeStateRef.current) {
          return;
        }

        const current = resizeStateRef.current;
        const deltaX = event.clientX - current.originX;
        const deltaDays = Math.round(deltaX / colWidth);

        if (deltaDays === 0) {
          resizeStateRef.current = null;
          return;
        }

        let nextStart = current.startDate;
        let nextEnd = current.endDate;

        if (current.edge === "start") {
          nextStart = addDays(current.startDate, deltaDays);
          if (isAfter(nextStart, nextEnd)) {
            nextStart = nextEnd;
          }
        } else {
          nextEnd = addDays(current.endDate, deltaDays);
          if (isBefore(nextEnd, nextStart)) {
            nextEnd = nextStart;
          }
        }

        const patch: TripLayerUpdateArgs["patch"] = {};
        const nextStartIso = formatISO(nextStart, { representation: "date" });
        const nextEndIso = formatISO(nextEnd, { representation: "date" });

        if (nextStartIso !== current.trip.start_date) {
          patch.start_date = nextStartIso;
        }
        if (nextEndIso !== current.trip.end_date) {
          patch.end_date = nextEndIso;
        }

        if (patch.start_date || patch.end_date) {
          onTripUpdate({ id: current.trip.id, patch });
        }

        resizeStateRef.current = null;
      };

      window.addEventListener("pointerup", handlePointerUp, { once: true });
    },
    [colWidth, onTripUpdate]
  );

  const handleTripClick = useCallback(
    (trip: TripRecord) => {
      if (onTripClick) {
        onTripClick(trip);
      }
    },
    [onTripClick]
  );

  const layerHeight = employees.length * rowHeight;

  return (
    <div
      className="trip-layer"
      data-trip-layer
      style={{
        top: offsetTop,
        left: 0,
        width: calendarWidth,
        height: layerHeight,
      }}
    >
      <div className="trip-layer__canvas" style={{ minWidth: calendarWidth, height: layerHeight }}>
        {renderedTrips.map((render) => (
          <TripBlock
            key={render.trip.id}
            render={render}
            rowHeight={rowHeight}
            onResizeStart={handleResizeStart}
            onContextMenu={handleContextMenu}
            onClick={onTripClick ? handleTripClick : undefined}
          />
        ))}
      </div>

      {contextMenu && (
        <div
          className="calendar-context-menu absolute z-50 min-w-[160px] rounded-md border border-slate-200 bg-white py-1 text-sm shadow-xl"
          data-calendar-context-menu
          style={{
            top: contextMenu.y,
            left: contextMenu.x,
            pointerEvents: "auto",
          }}
        >
          <button className="block w-full px-3 py-2 text-left hover:bg-slate-100" onClick={handleTripEdit}>
            Edit trip
          </button>
          <button className="block w-full px-3 py-2 text-left hover:bg-slate-100" onClick={handleTripDuplicate}>
            Duplicate
          </button>
          <button className="block w-full px-3 py-2 text-left hover:bg-slate-100" onClick={handleTripCopy}>
            Copy
          </button>
          <button
            className="block w-full px-3 py-2 text-left hover:bg-slate-100 disabled:cursor-not-allowed disabled:text-slate-400"
            onClick={handleTripPaste}
            disabled={!canPaste()}
          >
            Paste
          </button>
          <button className="block w-full px-3 py-2 text-left hover:bg-slate-100" onClick={handleTripToggleGhost}>
            {contextMenu.trip.ghosted ? "Unmark ghost" : "Mark as ghost"}
          </button>
          <button className="block w-full px-3 py-2 text-left text-red-600 hover:bg-red-50" onClick={handleTripDelete}>
            Delete
          </button>
        </div>
      )}
    </div>
  );
};

export const TripLayer = memo(TripLayerComponent);
