import type { TestCase } from "../../types";

export default function FailedTestPicker({
  testCases,
  selectedId,
  onSelect,
}: {
  testCases: TestCase[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <select
      value={selectedId ?? ""}
      onChange={(e) => onSelect(e.target.value)}
      className="w-full max-w-md rounded border border-line bg-surface px-3 py-2 text-sm text-ink focus:outline-none focus:ring-1 focus:ring-accent"
    >
      <option value="" disabled>
        Select a failed test case…
      </option>
      {testCases.map((tc) => (
        <option key={tc.id} value={tc.id}>
          {tc.id} — {tc.description}
        </option>
      ))}
    </select>
  );
}
