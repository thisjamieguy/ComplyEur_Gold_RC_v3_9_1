import * as Dialog from "@radix-ui/react-dialog";

interface LegendEntry {
  label: string;
  color: string;
  count: number;
}

interface LegendModalProps {
  open: boolean;
  onClose: () => void;
  entries: LegendEntry[];
}

export function LegendModal({ open, onClose, entries }: LegendModalProps) {
  const sorted = [...entries].sort((a, b) => a.label.localeCompare(b.label));

  return (
    <Dialog.Root open={open} onOpenChange={(value) => !value && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/20" />
        <Dialog.Content className="fixed top-16 left-1/2 w-[420px] -translate-x-1/2 rounded-lg bg-white p-6 shadow-xl">
          <Dialog.Title className="text-lg font-semibold">Job Colour Legend</Dialog.Title>
          <p className="mt-1 text-sm text-slate-600">
            Colours are generated from job references so they remain consistent wherever they appear.
          </p>
          <div className="mt-4 max-h-[360px] overflow-auto pr-1">
            {sorted.length === 0 ? (
              <div className="rounded-md border border-dashed border-slate-200 p-4 text-center text-sm text-slate-500">
                No job references yet. Trip colours will appear once jobs are assigned.
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                {sorted.map((entry) => (
                  <div
                    key={entry.label}
                    className="flex items-center gap-3 rounded-md border border-slate-200 bg-slate-50/80 px-3 py-2 shadow-sm"
                  >
                    <span
                      className="h-4 w-4 rounded-sm border border-black/10"
                      style={{ backgroundColor: entry.color }}
                      aria-hidden
                    />
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-slate-700">{entry.label}</span>
                      <span className="text-xs text-slate-500">
                        {entry.count} trip{entry.count === 1 ? "" : "s"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="mt-5 flex justify-end">
            <button
              className="rounded bg-blue-600 px-3 py-1 text-sm text-white transition-colors hover:bg-blue-700"
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

