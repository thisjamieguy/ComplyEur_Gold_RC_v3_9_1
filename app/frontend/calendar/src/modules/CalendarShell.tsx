import React, { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { addDays, addWeeks, differenceInCalendarDays, eachDayOfInterval, format, formatISO, isWeekend, parseISO, startOfWeek } from "date-fns";
import { DndProvider } from "react-dnd";
import { TouchBackend } from "react-dnd-touch-backend";
import ColorHash from "color-hash";
import toast, { Toaster } from "react-hot-toast";

import { Toolbar } from "../ui/Toolbar";
import { FilterBar, type Filters } from "../ui/FilterBar";
import { QuickSearch } from "../ui/QuickSearch";

import {
  useTrips,
  useUpdateTrip,
  useCreateTrip,
  useDeleteTrip,
  useDuplicateTrip,
  useToggleGhost,
} from "../hooks/useTrips";
import { useEmployees } from "../hooks/useEmployees";
import type { TripRecord } from "../hooks/useTrips";
import type { EmployeeRecord } from "../hooks/useEmployees";
import { TripLayer, type TripLayerDay } from "../components/TripLayer";
import { LegendModal } from "../components/LegendModal";
import { ExportDialog } from "../components/ExportDialog";
import { TripEditor } from "../components/TripEditor";
import type { TripFormState } from "../components/TripEditor";
import { SettingsModal } from "./SettingsModal";
import type { CalendarSettings } from "./SettingsModal";
import { WelcomeSplash } from "../components/WelcomeSplash";

// Constants for unified coordinate system
const BASE_COL = 140;   // Base column width in pixels
const BASE_ROW = 44;    // Base row height in pixels
const UNASSIGNED_EMPLOYEE: EmployeeRecord = { id: -1, name: "Unassigned" };

const DEFAULT_SETTINGS: CalendarSettings = {
  showWeekNumbers: true,
  firstDayIsMonday: true,
  dateFormat: "EEE dd-MMM",
  zoom: 1,
  visibleWeeks: 1,
};

const loadSettings = (): CalendarSettings => {
  try {
    const stored = localStorage.getItem("calendar:settings");
    if (!stored) {
      return DEFAULT_SETTINGS;
    }
    const parsed = JSON.parse(stored);
    return { ...DEFAULT_SETTINGS, ...parsed } satisfies CalendarSettings;
  } catch (error) {
    console.warn("Failed to load calendar settings", error);
    return DEFAULT_SETTINGS;
  }
};

const saveSettings = (settings: CalendarSettings) => {
  localStorage.setItem("calendar:settings", JSON.stringify(settings));
};

export const CalendarShell: React.FC = () => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  // Week + zoom state
  const [anchorDate, setAnchorDate] = useState(() => new Date());
  const [settings, setSettings] = useState<CalendarSettings>(loadSettings);
  const [showSettings, setShowSettings] = useState(false);
  const [legendOpen, setLegendOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [showWelcome, setShowWelcome] = useState<boolean>(() => {
    try {
      return localStorage.getItem("calendarSplashDismissed") !== "true";
    } catch {
      return true;
    }
  });
  const [clipboardTrip, setClipboardTrip] = useState<TripRecord | null>(null);
  const [editorTrip, setEditorTrip] = useState<TripRecord | null>(null);
  
  // Filter and search state
  const [filters, setFiltersState] = useState<Filters>({ q: "", country: "", job: "", showGhosted: true });
  const setFilters = (f: Partial<Filters>) => setFiltersState(s => ({ ...s, ...f }));
  const [qsOpen, setQsOpen] = useState(false);

  // Data hooks
  const { data: employees = [], isLoading: employeesLoading, error: employeesError } = useEmployees();
  const { data: trips = [], isLoading: tripsLoading, error: tripsError } = useTrips();
  const updateTrip = useUpdateTrip();
  const createTrip = useCreateTrip();
  const deleteTrip = useDeleteTrip();
  const duplicateTrip = useDuplicateTrip();
  const toggleGhost = useToggleGhost();

  // Week calculation
  const weekStart = startOfWeek(anchorDate, { weekStartsOn: settings.firstDayIsMonday ? 1 : 0 });
  const weekStartISO = formatISO(weekStart, { representation: "date" });

  const calendarDays = useMemo(() => {
    const visibleWeeks = Math.max(1, settings.visibleWeeks);
    const lastVisibleDay = addDays(weekStart, visibleWeeks * 7 - 1);
    return eachDayOfInterval({ start: weekStart, end: lastVisibleDay });
  }, [weekStart, settings.visibleWeeks]);

  // Pixel sizes (NO transforms) - computed from zoom
  const colWidth = Math.round(BASE_COL * settings.zoom);
  const rowHeight = Math.round(BASE_ROW * settings.zoom);
  const [stickyLeftWidth, setStickyLeftWidth] = useState(260); // employee name column
  const headerHeight = Math.round(64 * settings.zoom);
  const weekBandHeight = settings.showWeekNumbers ? Math.round(28 * settings.zoom) : 0;

  // Grid template for consistent alignment
  const columnCount = Math.max(calendarDays.length, 1);
  const gridTemplate = `${stickyLeftWidth}px repeat(${columnCount}, ${colWidth}px)`;
  const calendarMinWidth = stickyLeftWidth + columnCount * colWidth;

  const derivedDateFormat = useMemo(() => {
    const sanitized = settings.dateFormat
      .replace(/\(?(EEE)\)?/g, "")
      .replace(/\s+/g, " ")
      .trim();
    return sanitized.length > 0 ? sanitized : "dd MMM";
  }, [settings.dateFormat]);

  const daySlots = useMemo<TripLayerDay[]>(() => {
    return calendarDays.map((date, index) => {
      const iso = formatISO(date, { representation: "date" });
      return {
        date,
        iso,
        columnIndex: index,
        weekIndex: Math.floor(index / 7),
        weekdayLabel: format(date, "EEE"),
        dateLabel: format(date, derivedDateFormat),
        fullLabel: format(date, settings.dateFormat),
        isWeekend: isWeekend(date),
      };
    });
  }, [calendarDays, derivedDateFormat, settings.dateFormat]);

  const weekSegments = useMemo(() => {
    if (!settings.showWeekNumbers) {
      return [] as Array<{ label: string; iso: string; span: number }>;
    }

    const segments: Array<{ label: string; iso: string; span: number }> = [];
    const visibleWeeks = Math.max(1, settings.visibleWeeks);

    for (let weekIndex = 0; weekIndex < visibleWeeks; weekIndex += 1) {
      const weekStartDate = addWeeks(weekStart, weekIndex);
      const remainingColumns = Math.max(calendarDays.length - weekIndex * 7, 0);
      if (remainingColumns <= 0) {
        break;
      }

      segments.push({
        label: `Week ${format(weekStartDate, "II")}`,
        iso: formatISO(weekStartDate, { representation: "date" }),
        span: Math.min(7, remainingColumns),
      });
    }

    return segments;
  }, [calendarDays, settings.showWeekNumbers, settings.visibleWeeks, weekStart]);

  // Filter employees
  const filteredEmployees = useMemo(() => {
    const activeEmployees = employees.filter(e => e.active !== false);
    const allEmployees = [UNASSIGNED_EMPLOYEE, ...activeEmployees];
    
    if (filters.q.trim()) {
      const query = filters.q.trim().toLowerCase();
      return allEmployees.filter(e => e.name.toLowerCase().includes(query));
    }
    return allEmployees;
  }, [employees, filters.q]);

  // Filter trips
  const filteredTrips = useMemo(() => {
    let result = trips;
    
    if (filters.country) {
      result = result.filter(t => t.country === filters.country);
    }
    if (filters.job) {
      result = result.filter(t => t.job_ref === filters.job);
    }
    if (!filters.showGhosted) {
      result = result.filter(t => !t.ghosted);
    }
    
    return result;
  }, [trips, filters]);

  // Color hash for trip colors
  const colorHash = useMemo(() => new ColorHash({ lightness: 0.55, saturation: 0.65 }), []);
  const getTripColor = useCallback((trip: TripRecord) => {
    const key = trip.job_ref?.trim() || `country:${trip.country}`;
    return colorHash.hex(key);
  }, [colorHash]);

  // Countries and jobs for filter bar
  const countries = useMemo(() => 
    Array.from(new Set(trips.map(t => t.country).filter(Boolean))) as string[], 
    [trips]
  );
  const jobs = useMemo(() => 
    Array.from(new Set(trips.map(t => t.job_ref).filter(Boolean))) as string[], 
    [trips]
  );

  // Legend entries
  const legendEntries = useMemo(() => {
    const counts = new Map<string, { label: string; color: string; count: number }>();
    trips.forEach((trip) => {
      const label = trip.job_ref?.trim() || "No job ref";
      const key = label.toLowerCase();
      const color = getTripColor(trip);
      const current = counts.get(key);
      if (current) {
        current.count += 1;
      } else {
        counts.set(key, { label, color, count: 1 });
      }
    });
    return Array.from(counts.values());
  }, [trips, getTripColor]);

  // Job color map
  const jobColourMap = useMemo(() => {
    const map: Record<string, string> = {};
    trips.forEach((trip) => {
      const key = trip.job_ref?.trim() || `country:${trip.country}`;
      if (!map[key]) {
        map[key] = getTripColor(trip);
      }
    });
    return map;
  }, [trips, getTripColor]);

  // Measure grid dimensions
  useLayoutEffect(() => {
    const measure = () => {
      const stickyCell = document.querySelector("[data-sticky-left]") as HTMLElement | null;
      if (stickyCell) {
        const width = stickyCell.getBoundingClientRect().width;
        if (Number.isFinite(width) && width > 0) {
          setStickyLeftWidth((prev) => (Math.abs(prev - width) > 0.5 ? width : prev));
        }
      }
    };

    const raf = requestAnimationFrame(measure);
    window.addEventListener("resize", measure);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", measure);
    };
  }, [colWidth, filteredEmployees.length, calendarDays.length]);

  // Settings management
  const updateSettings = useCallback(
    (patch: Partial<CalendarSettings>) => {
      setSettings((prev: CalendarSettings) => {
        const next = { ...prev, ...patch } as CalendarSettings;
        saveSettings(next);
        return next;
      });
    },
    []
  );


  const handleEdit = useCallback((trip: TripRecord) => {
    setEditorTrip(trip);
  }, []);

  const handleDuplicate = useCallback((trip: TripRecord) => {
    duplicateTrip.mutate({ id: trip.id });
  }, [duplicateTrip]);

  const handleDelete = useCallback((trip: TripRecord) => {
    deleteTrip.mutate(trip.id);
  }, [deleteTrip]);

  const handleGhostToggle = useCallback((trip: TripRecord) => {
    toggleGhost(trip);
  }, [toggleGhost]);

  const handleCopy = useCallback((trip: TripRecord) => {
    setClipboardTrip(trip);
    toast.success("Trip copied");
  }, []);

  const handlePaste = useCallback((target: TripRecord) => {
    if (!clipboardTrip) return;
    const startDate = parseISO(clipboardTrip.start_date);
    const endDate = parseISO(clipboardTrip.end_date);
    const duration = differenceInCalendarDays(endDate, startDate);
    const targetStart = parseISO(target.start_date);
    const targetEnd = addDays(targetStart, duration);
    
    createTrip.mutate({
      employee_id: target.employee_id,
      country: clipboardTrip.country,
      start_date: formatISO(targetStart, { representation: "date" }),
      end_date: formatISO(targetEnd, { representation: "date" }),
      job_ref: clipboardTrip.job_ref,
      ghosted: clipboardTrip.ghosted,
      purpose: clipboardTrip.purpose || "",
    });
  }, [clipboardTrip, createTrip]);

  const handleEditorSubmit = useCallback(
    (tripId: number, formData: TripFormState) => {
      updateTrip.mutate({
        id: tripId,
        patch: {
          employee_id: formData.employee_id,
          job_ref: formData.job_ref,
          country: formData.country,
          start_date: formData.start_date,
          end_date: formData.end_date,
          purpose: formData.purpose,
          ghosted: formData.ghosted,
        },
      });
      setEditorTrip(null);
    },
    [updateTrip]
  );

  const handleCellClick = useCallback((_employee: EmployeeRecord, _isoDate: string) => {
    // Phase 3.4 Layout Stabilization: reserved for Phase 3.6 interactivity hooks.
  }, []);

  const handleTripClick = useCallback((_trip: TripRecord) => {
    // Phase 3.4 Layout Stabilization: reserved for Phase 3.6 interactivity hooks.
  }, []);

  // Search items
  const searchItems = useMemo(() => {
    const employeeItems = filteredEmployees.map(emp => ({
      label: emp.name,
      value: String(emp.id),
    }));
    const jobItems = jobs.map(job => ({
      label: `Job ${job}`,
      value: `job:${job}`,
      meta: "Job" as const,
    }));
    return [...employeeItems, ...jobItems];
  }, [filteredEmployees, jobs]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setQsOpen(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const isLoading = employeesLoading || tripsLoading;
  const error = employeesError || tripsError;

  // Title
  const title = `Week beginning ${format(weekStart, "dd MMM yyyy")}`;

  return (
    <DndProvider backend={TouchBackend} options={{ enableMouseEvents: true }}>
      <div className="flex h-full w-full flex-col" data-calendar-shell>
        <Toaster position="bottom-right" />
        <WelcomeSplash
          open={showWelcome}
          onClose={(doNotShow) => {
            if (doNotShow) {
              try { localStorage.setItem("calendarSplashDismissed", "true"); } catch {}
            }
            setShowWelcome(false);
          }}
        />
        
        <Toolbar
          onPrev={() => setAnchorDate(prev => addWeeks(prev, -1))}
          onToday={() => setAnchorDate(new Date())}
          onNext={() => setAnchorDate(prev => addWeeks(prev, 1))}
          title={title}
          zoom={settings.zoom}
          setZoom={(zoom) => updateSettings({ zoom: zoom as 0.75 | 1 | 1.25 | 1.5 })}
          onOpenLegend={() => setLegendOpen(true)}
          onOpenPrint={() => window.print()}
          onOpenSettings={() => setShowSettings(true)}
          onOpenSearch={() => setQsOpen(true)}
          onOpenExport={() => setExportOpen(true)}
        />

        <FilterBar 
          filters={filters} 
          setFilters={setFilters} 
          countries={countries} 
          jobs={jobs} 
        />

        <main
          className="relative flex-1 overflow-y-auto"
          ref={scrollRef}
          style={{ scrollBehavior: "smooth" }}
        >
          {error && (
            <div className="p-4 text-sm text-red-600">
              Failed to load data: {error instanceof Error ? error.message : String(error)}
            </div>
          )}
          {isLoading && !error && (
            <div className="flex items-center justify-center gap-2 p-6 text-sm text-slate-600">
              <span className="h-2 w-2 animate-ping rounded-full bg-blue-500" />
              Loading calendar…
            </div>
          )}

          <div className="relative">
            <div className="sticky top-[76px] z-30 bg-white maavsi-sticky" data-header-block>
              {settings.showWeekNumbers && weekSegments.length > 0 && (
                <div
                  className="grid maavsi-grid maavsi-top text-xs uppercase tracking-wide"
                  style={{ gridTemplateColumns: gridTemplate, minWidth: calendarMinWidth, height: weekBandHeight }}
                  data-week-band
                >
                  <div className="flex items-center pl-3 text-[11px] font-semibold text-slate-600 maavsi-left">
                    Weeks
                  </div>
                  {weekSegments.map((segment) => (
                    <div
                      key={segment.iso}
                      className="flex items-center justify-center px-2 text-[11px] font-semibold text-slate-500 maavsi-col"
                      style={{ gridColumn: `span ${segment.span}` }}
                      data-week-segment={segment.iso}
                    >
                      {segment.label}
                    </div>
                  ))}
                </div>
              )}

              <div
                className="grid maavsi-grid"
                style={{ gridTemplateColumns: gridTemplate, minWidth: calendarMinWidth, height: headerHeight }}
                data-day-header
              >
                <div className="flex items-center pl-3 text-sm font-semibold text-slate-700 maavsi-left">
                  Employees
                </div>
                {daySlots.map((slot) => (
                  <div
                    key={slot.iso}
                    className="flex flex-col items-center justify-center gap-1 px-2 text-center maavsi-col"
                    data-date={slot.iso}
                    data-column-index={slot.columnIndex}
                    data-week-index={slot.weekIndex}
                    title={slot.fullLabel}
                  >
                    <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      {slot.weekdayLabel}
                    </span>
                    <span className="text-sm font-semibold text-slate-900">
                      {slot.dateLabel}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative" data-grid-region>
              <div className="relative overflow-x-auto" data-grid-scroll>
                <div
                  ref={gridRef}
                  className="relative bg-white"
                  data-calendar-grid
                  style={{ minWidth: calendarMinWidth }}
                >
                  {filteredEmployees.map((employee, rowIdx) => (
                    <div
                      key={employee.id}
                      className="grid maavsi-grid"
                      style={{ gridTemplateColumns: gridTemplate, minHeight: rowHeight, height: rowHeight }}
                      data-calendar-row
                      data-employee-row={employee.id}
                    >
                      <div
                        className="maavsi-left flex h-full items-center pl-3 pr-4 text-sm font-medium text-slate-700"
                        style={{ width: stickyLeftWidth }}
                        data-sticky-left
                        data-employee={employee.id}
                        data-stripe={rowIdx % 2 === 1 ? "odd" : "even"}
                      >
                        {employee.name}
                      </div>
                      {daySlots.map((slot) => (
                        <div
                          key={`${employee.id}-${slot.iso}`}
                          className="maavsi-cell"
                          data-employee={employee.id}
                          data-date={slot.iso}
                          data-weekend={slot.isWeekend ? "true" : undefined}
                          data-stripe={rowIdx % 2 === 1 ? "odd" : "even"}
                          role="presentation"
                          tabIndex={-1}
                          onClick={() => handleCellClick(employee, slot.iso)}
                        />
                      ))}
                    </div>
                  ))}

                  <TripLayer
                    weekStartISO={weekStartISO}
                    daySlots={daySlots}
                    colWidth={colWidth}
                    rowHeight={rowHeight}
                    employees={filteredEmployees}
                    trips={filteredTrips}
                    offsetLeft={stickyLeftWidth}
                    offsetTop={weekBandHeight + headerHeight}
                    calendarWidth={calendarMinWidth}
                    getTripColor={getTripColor}
                    onTripUpdate={({ id, patch }) =>
                      updateTrip.mutate({
                        id: Number(id),
                        patch: {
                          ...(patch.start_date ? { start_date: patch.start_date } : {}),
                          ...(patch.end_date ? { end_date: patch.end_date } : {}),
                        },
                      })
                    }
                    onTripEdit={handleEdit}
                    onTripDuplicate={handleDuplicate}
                    onTripDelete={handleDelete}
                    onTripGhostToggle={handleGhostToggle}
                    onTripCopy={handleCopy}
                    onTripPaste={handlePaste}
                    canPaste={() => Boolean(clipboardTrip)}
                    onTripClick={handleTripClick}
                  />
                </div>
              </div>
            </div>
          </div>
        </main>

        <SettingsModal
          open={showSettings}
          onClose={() => setShowSettings(false)}
          settings={settings}
          onChange={updateSettings}
        />

        <LegendModal open={legendOpen} onClose={() => setLegendOpen(false)} entries={legendEntries} />

        <ExportDialog
          open={exportOpen}
          onClose={() => setExportOpen(false)}
          employees={employees}
          trips={trips}
          startDate={weekStart}
          jobColours={jobColourMap}
        />

        <TripEditor
          open={Boolean(editorTrip)}
          trip={editorTrip}
          employees={employees}
          onClose={() => setEditorTrip(null)}
          onSubmit={handleEditorSubmit}
        />

        {/* Cmd+K Quick Search */}
        <QuickSearch
          open={qsOpen}
          onOpenChange={setQsOpen}
          items={searchItems}
          onSelect={(val) => {
            if (val.startsWith("job:")) {
              setFilters({ job: val.slice(4) });
            } else {
              // Scroll to employee row
              const idx = filteredEmployees.findIndex(e => String(e.id) === val);
              if (idx >= 0) {
                scrollRef.current?.scrollTo({ top: idx * rowHeight - 80, behavior: "smooth" });
              }
            }
            setQsOpen(false);
          }}
        />
      </div>
    </DndProvider>
  );
};