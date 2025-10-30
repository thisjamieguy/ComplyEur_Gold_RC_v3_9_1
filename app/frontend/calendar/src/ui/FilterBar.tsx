
export type Filters = {
  q: string; country: string; job: string; showGhosted: boolean;
};

export function FilterBar({
  filters, setFilters, countries, jobs
}: {
  filters: Filters;
  setFilters: (f: Partial<Filters>)=>void;
  countries: string[];
  jobs: string[];
}) {
  return (
    <div className="px-3 py-2 border-b bg-white/90">
      <div className="flex flex-wrap gap-2 items-center">
        <input
          className="border rounded px-2 py-1 text-sm min-w-[220px]"
          placeholder="Search employees / jobs (⌘K)"
          value={filters.q}
          onChange={e=>setFilters({q: e.target.value})}
        />
        <select className="border rounded px-2 py-1 text-sm" value={filters.country} onChange={e=>setFilters({country:e.target.value})}>
          <option value="">All countries</option>
          {countries.map(c=><option key={c} value={c}>{c}</option>)}
        </select>
        <select className="border rounded px-2 py-1 text-sm" value={filters.job} onChange={e=>setFilters({job:e.target.value})}>
          <option value="">All jobs</option>
          {jobs.map(j=><option key={j} value={j}>{j}</option>)}
        </select>
        <label className="ml-auto text-sm flex items-center gap-2">
          <input type="checkbox" checked={filters.showGhosted} onChange={e=>setFilters({showGhosted:e.target.checked})}/>
          Show ghosted
        </label>
      </div>
    </div>
  );
}
