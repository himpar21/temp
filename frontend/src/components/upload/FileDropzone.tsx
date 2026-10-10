import { useRef, useState, DragEvent } from "react";
import { UploadCloud, FileSpreadsheet } from "lucide-react";

export default function FileDropzone({ onFile }: { onFile: (file: File) => void }) {
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFiles(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    setFileName(file.name);
    onFile(file);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded border border-dashed px-6 py-10 text-center transition-colors ${
        dragging ? "border-accent bg-accent-soft" : "border-line bg-surface"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.json,.jsonl,.md,.txt,.pdf,.xlsx,.docx,.png,.jpg,.jpeg"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      {fileName ? (
        <>
          <FileSpreadsheet size={22} className="text-accent" />
          <p className="text-sm text-ink">{fileName}</p>
          <p className="text-xs text-slate">Click to choose a different file</p>
        </>
      ) : (
        <>
          <UploadCloud size={22} className="text-slate" />
          <p className="text-sm text-ink">Drag a supported document here, or click to browse</p>
          <p className="text-xs text-slate">CSV, JSON, Markdown, PDF, Excel, DOCX, PNG, or JPEG</p>
        </>
      )}
    </div>
  );
}
