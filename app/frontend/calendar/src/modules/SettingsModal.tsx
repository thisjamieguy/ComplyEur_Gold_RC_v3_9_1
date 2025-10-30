import * as Dialog from "@radix-ui/react-dialog";

export type CalendarSettings = {
  showWeekNumbers: boolean;
  firstDayIsMonday: boolean;
  dateFormat: "EEE dd-MMM" | "dd/MM (EEE)";
  zoom: 0.75 | 1 | 1.25 | 1.5;
  visibleWeeks: 1 | 2 | 3;
};

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
  settings: CalendarSettings;
  onChange: (patch: Partial<CalendarSettings>) => void;
}

export function SettingsModal({ open, onClose, settings, onChange }: SettingsModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={(v) => !v && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/20" />
        <Dialog.Content className="fixed top-[10%] left-1/2 -translate-x-1/2 w-[520px] rounded-lg bg-white p-4 shadow-xl border border-gray-100">
          <Dialog.Title className="text-lg font-semibold mb-3">
            Calendar Settings
          </Dialog.Title>
          <div className="space-y-4">
            <label className="flex items-center justify-between">
              <span>Show week numbers</span>
              <input
                type="checkbox"
                checked={settings.showWeekNumbers}
                onChange={(e) => onChange({ showWeekNumbers: e.target.checked })}
                className="rounded"
              />
            </label>
            <label className="flex items-center justify-between">
              <span>First day is Monday</span>
              <input
                type="checkbox"
                checked={settings.firstDayIsMonday}
                onChange={(e) => onChange({ firstDayIsMonday: e.target.checked })}
                className="rounded"
              />
            </label>
            <label className="flex items-center justify-between">
              <span>Date format</span>
              <select
                className="border rounded px-2 py-1"
                value={settings.dateFormat}
                onChange={(e) => onChange({ dateFormat: e.target.value as CalendarSettings["dateFormat"] })}
              >
                <option value="EEE dd-MMM">Mon 13-Oct</option>
                <option value="dd/MM (EEE)">13/10 (Mon)</option>
              </select>
            </label>
            <label className="flex items-center justify-between">
              <span>Weeks visible</span>
              <select
                className="border rounded px-2 py-1"
                value={settings.visibleWeeks}
                onChange={(e) =>
                  onChange({ visibleWeeks: Number(e.target.value) as CalendarSettings["visibleWeeks"] })
                }
              >
                <option value={1}>1 week</option>
                <option value={2}>2 weeks</option>
                <option value={3}>3 weeks</option>
              </select>
            </label>
            <label className="flex items-center justify-between">
              <span>Zoom</span>
              <select
                className="border rounded px-2 py-1"
                value={settings.zoom}
                onChange={(e) =>
                  onChange({ zoom: Number(e.target.value) as CalendarSettings["zoom"] })
                }
              >
                <option value={0.75}>75%</option>
                <option value={1}>100%</option>
                <option value={1.25}>125%</option>
                <option value={1.5}>150%</option>
              </select>
            </label>
          </div>
          <div className="mt-6 flex justify-end gap-2">
            <button
              className="px-3 py-1 rounded bg-gray-100 hover:bg-gray-200"
              onClick={onClose}
            >
              Close
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
