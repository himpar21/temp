import { Search } from "lucide-react";

export interface FilterOption {
  key: string;
  label: string;
  options: string[];
}

export default function FilterBar({
  search,
  onSearchChange,
  filters,
  values,
  onFilterChange,
}: {
  search: string;
  onSearchChange: (v: string) => void;
  filters: FilterOption[];
  values: Record<string, string>;
  onFilterChange: (key: string, value: string) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="relative">
        <Search size={14} className="pointer-events-none absolute left-2.5 top-2.5 text-slate" />
        <input
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search…"
          className="w-56 rounded border border-line bg-surface py-2 pl-8 pr-3 text-xs text-ink placeholder:text-slate focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>
      {filters.map((f) => (
        <select
          key={f.key}
          value={values[f.key] ?? ""}
          onChange={(e) => onFilterChange(f.key, e.target.value)}
          className="rounded border border-line bg-surface px-2 py-2 text-xs text-ink focus:outline-none focus:ring-1 focus:ring-accent"
        >
          <option value="">All {f.label}</option>
          {f.options.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      ))}
    </div>
  );
}
