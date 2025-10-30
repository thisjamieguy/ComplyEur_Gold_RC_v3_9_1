import { useEffect, useMemo, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";

import type { TripRecord } from "../hooks/useTrips";
import type { EmployeeRecord } from "../hooks/useEmployees";

interface TripEditorProps {
  open: boolean;
  trip: TripRecord | null;
  employees: EmployeeRecord[];
  onClose: () => void;
  onSubmit: (tripId: number, payload: TripFormState) => void | Promise<void>;
}

export interface TripFormState {
  employee_id: number;
  job_ref: string;
  country: string;
  start_date: string;
  end_date: string;
  purpose: string;
  ghosted: boolean;
}

const emptyForm: TripFormState = {
  employee_id: -1,
  job_ref: "",
  country: "",
  start_date: "",
  end_date: "",
  purpose: "",
  ghosted: false,
};

export function TripEditor({ open, trip, employees, onClose, onSubmit }: TripEditorProps) {
  const [form, setForm] = useState<TripFormState>(emptyForm);

  useEffect(() => {
    if (trip) {
      setForm({
        employee_id: trip.employee_id,
        job_ref: trip.job_ref ?? "",
        country: trip.country ?? "",
        start_date: trip.start_date,
        end_date: trip.end_date,
        purpose: trip.purpose ?? "",
        ghosted: Boolean(trip.ghosted),
      });
    } else {
      setForm(emptyForm);
    }
  }, [trip]);

  const sortedEmployees = useMemo(
    () => [...employees].sort((a, b) => a.name.localeCompare(b.name)),
    [employees]
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!trip) return;
    await onSubmit(trip.id, form);
    onClose();
  };

  const disabled = !trip;

  return (
    <Dialog.Root open={open} onOpenChange={(value) => !value && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/20" />
        <Dialog.Content className="fixed top-[12%] left-1/2 w-[520px] -translate-x-1/2 rounded-lg bg-white p-6 shadow-2xl">
          <Dialog.Title className="text-lg font-semibold">Edit Trip</Dialog.Title>
          <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium">Employee</span>
              <select
                className="rounded border border-slate-200 px-2 py-2"
                value={form.employee_id}
                disabled={disabled}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, employee_id: Number(event.target.value) }))
                }
                required
              >
                <option value="" disabled>
                  Select employee
                </option>
                {sortedEmployees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.name}
                  </option>
                ))}
              </select>
            </label>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <label className="flex flex-col gap-1">
                <span className="font-medium">Job reference</span>
                <input
                  type="text"
                  className="rounded border border-slate-200 px-2 py-2"
                  value={form.job_ref}
                  disabled={disabled}
                  onChange={(event) => setForm((prev) => ({ ...prev, job_ref: event.target.value }))}
                  placeholder="e.g. JOB-4102"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="font-medium">Country</span>
                <input
                  type="text"
                  className="rounded border border-slate-200 px-2 py-2 uppercase"
                  value={form.country}
                  disabled={disabled}
                  onChange={(event) => setForm((prev) => ({ ...prev, country: event.target.value }))}
                  required
                />
              </label>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <label className="flex flex-col gap-1">
                <span className="font-medium">Start date</span>
                <input
                  type="date"
                  className="rounded border border-slate-200 px-2 py-2"
                  value={form.start_date}
                  disabled={disabled}
                  onChange={(event) => setForm((prev) => ({ ...prev, start_date: event.target.value }))}
                  required
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="font-medium">End date</span>
                <input
                  type="date"
                  className="rounded border border-slate-200 px-2 py-2"
                  value={form.end_date}
                  disabled={disabled}
                  min={form.start_date}
                  onChange={(event) => setForm((prev) => ({ ...prev, end_date: event.target.value }))}
                  required
                />
              </label>
            </div>

            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium">Purpose / notes</span>
              <textarea
                className="h-20 rounded border border-slate-200 px-2 py-2"
                value={form.purpose}
                disabled={disabled}
                onChange={(event) => setForm((prev) => ({ ...prev, purpose: event.target.value }))}
                placeholder="Optional notes for this trip"
              />
            </label>

            <label className="flex items-center gap-2 text-sm font-medium">
              <input
                type="checkbox"
                checked={form.ghosted}
                disabled={disabled}
                onChange={(event) => setForm((prev) => ({ ...prev, ghosted: event.target.checked }))}
              />
              Ghost trip (hide from primary metrics)
            </label>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="rounded bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
                onClick={onClose}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="rounded bg-blue-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
                disabled={disabled}
              >
                Save changes
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

