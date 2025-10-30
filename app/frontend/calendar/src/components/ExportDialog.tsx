import * as Dialog from "@radix-ui/react-dialog";
import React from "react";
import { PDFDownloadLink } from "@react-pdf/renderer";
import { addDays, format } from "date-fns";

import type { TripRecord } from "../hooks/useTrips";
import type { EmployeeRecord } from "../hooks/useEmployees";
import { CalendarPDF } from "./pdf/CalendarPDF";

interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
  employees: EmployeeRecord[];
  trips: TripRecord[];
  startDate: Date;
  jobColours: Record<string, string>;
}

export function ExportDialog({ open, onClose, employees, trips, startDate, jobColours }: ExportDialogProps) {
  const [weeks, setWeeks] = React.useState<1 | 2 | 3>(1);

  React.useEffect(() => {
    if (!open) {
      setWeeks(1);
    }
  }, [open]);

  const filename = React.useMemo(
    () => `Maavsi_Calendar_${format(startDate, "yyyyMMdd")}_${weeks}wks.pdf`,
    [startDate, weeks]
  );

  const rangeLabel = React.useMemo(() => {
    const end = addDays(startDate, weeks * 7 - 1);
    return `${format(startDate, "dd MMM yyyy")} → ${format(end, "dd MMM yyyy")}`;
  }, [startDate, weeks]);

  return (
    <Dialog.Root open={open} onOpenChange={(value) => !value && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/20" />
        <Dialog.Content className="fixed top-24 left-1/2 w-[360px] -translate-x-1/2 rounded-lg bg-white p-5 shadow-xl">
          <Dialog.Title className="text-lg font-semibold">Export to PDF</Dialog.Title>
          <p className="mt-1 text-sm text-slate-600">
            Choose how many upcoming weeks to include. The file will open with the current calendar snapshot.
          </p>
          <div className="mt-4 space-y-3">
            <label className="block text-sm font-medium text-slate-700" htmlFor="export-weeks">
              Weeks to include
            </label>
            <select
              id="export-weeks"
              value={weeks}
              onChange={(event) => setWeeks(Number(event.target.value) as 1 | 2 | 3)}
              className="w-full rounded border border-slate-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={1}>1 Week</option>
              <option value={2}>2 Weeks</option>
              <option value={3}>3 Weeks</option>
            </select>
            <div className="rounded border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
              Range preview: {rangeLabel}
            </div>
          </div>
          <div className="mt-5 flex items-center justify-end gap-2">
            <button
              className="rounded bg-gray-100 px-3 py-1 text-sm font-medium text-slate-700 transition-colors hover:bg-gray-200"
              onClick={onClose}
            >
              Cancel
            </button>
            <PDFDownloadLink
              document={
                <CalendarPDF
                  employees={employees}
                  trips={trips}
                  startDate={startDate}
                  weeks={weeks}
                  jobColours={jobColours}
                />
              }
              fileName={filename}
              className="inline-flex items-center justify-center rounded bg-blue-600 px-3 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
              onClick={() => setTimeout(onClose, 150)}
            >
              {({ loading }) => (loading ? "Preparing…" : "Download PDF")}
            </PDFDownloadLink>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

