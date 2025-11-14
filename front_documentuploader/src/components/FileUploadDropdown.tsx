// FileUploadDropdown.tsx
import { useState } from "react";

export function FileUploadDropdown({ onFileSelect }: { onFileSelect: (file: File) => void }) {
  const [file, setFile] = useState<File | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      onFileSelect(e.target.files[0]);
    }
  };

  return (
      <input type="file" onChange={handleChange} accept=".pdf,.docx,.md,.mp3" />
  );
}
