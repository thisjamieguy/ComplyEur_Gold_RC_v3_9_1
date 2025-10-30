import { ChevronLeft, ChevronRight, Printer, SlidersHorizontal, Palette, Search, Download } from "lucide-react";

export function Toolbar({
  onPrev, onToday, onNext, title, zoom, setZoom, onOpenSettings, onOpenLegend, onOpenPrint, onOpenSearch, onOpenExport
}: {
  onPrev: ()=>void; onToday: ()=>void; onNext: ()=>void;
  title: string; zoom: number; setZoom:(z:number)=>void;
  onOpenSettings: ()=>void; onOpenLegend: ()=>void; onOpenPrint: ()=>void; onOpenSearch: ()=>void; onOpenExport: ()=>void;
}) {
  return (
    <div className="sticky top-0 z-30 bg-white/90 backdrop-blur border-b" style={{boxShadow:"var(--sticky-shadow)"}}>
      <div className="flex items-center gap-2 px-3 py-2">
        <button className="btn" onClick={onPrev}><ChevronLeft size={16}/> Prev</button>
        <button className="btn" onClick={onToday}>Today</button>
        <button className="btn" onClick={onNext}>Next <ChevronRight size={16}/></button>
        <div className="ml-3 text-sm text-slate-700 font-medium">{title}</div>
        <div className="ml-auto flex items-center gap-2">
          <button className="icon-btn" title="Search (⌘K)" onClick={onOpenSearch}><Search size={16}/></button>
          <select className="border rounded px-2 py-1 text-sm" value={zoom} onChange={e=>setZoom(Number(e.target.value))}>
            <option value={0.75}>75%</option><option value={1}>100%</option><option value={1.25}>125%</option><option value={1.5}>150%</option>
          </select>
          <button className="icon-btn" title="Legend" onClick={onOpenLegend}><Palette size={16}/></button>
          <button className="icon-btn" title="Export PDF" onClick={onOpenExport}><Download size={16}/></button>
          <button className="icon-btn" title="Print" onClick={onOpenPrint}><Printer size={16}/></button>
          <button className="btn" onClick={onOpenSettings}><SlidersHorizontal size={16}/> Settings</button>
        </div>
      </div>
      <style>{`
        .btn{display:inline-flex;align-items:center;gap:.4rem;padding:.35rem .6rem;border:1px solid rgba(0,0,0,.08);border-radius:.5rem;background:#f8fafc}
        .btn:hover{background:#eef2f7}
        .icon-btn{display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:.5rem;border:1px solid rgba(0,0,0,.08);background:#fff}
        .icon-btn:hover{background:#f1f5f9}
      `}</style>
    </div>
  );
}
