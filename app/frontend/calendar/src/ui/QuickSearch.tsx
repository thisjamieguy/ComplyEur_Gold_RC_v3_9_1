import * as Dialog from "@radix-ui/react-dialog";
import { Command } from "cmdk";

export function QuickSearch({open,onOpenChange,items,onSelect}:{open:boolean;onOpenChange:(v:boolean)=>void;items:{label:string,value:string,meta?:string}[];onSelect:(v:string)=>void;}){
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30" />
        <Dialog.Content className="fixed top-[15%] left-1/2 -translate-x-1/2 w-[600px] rounded-xl overflow-hidden shadow-2xl">
          <Command filter={(v: string, s: string) => s.includes(v.toLowerCase()) ? 1 : 0} className="bg-white">
            <Command.Input placeholder="Search employees or jobs…" className="w-full px-3 py-2 border-b outline-none"/>
            <Command.List className="max-h-[360px] overflow-auto">
              {items.length===0 && <Command.Empty className="p-3 text-sm text-slate-500">No results</Command.Empty>}
              <Command.Group>
                {items.map(it=>(
                  <Command.Item key={it.value} value={it.label.toLowerCase()} onSelect={()=>onSelect(it.value)} className="px-3 py-2 cursor-pointer hover:bg-slate-50">
                    <div className="text-sm font-medium">{it.label}</div>
                    {it.meta && <div className="text-xs text-slate-500">{it.meta}</div>}
                  </Command.Item>
                ))}
              </Command.Group>
            </Command.List>
          </Command>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
