interface FileUploadFieldProps {
    label: string;
    onFilesChange: (files: File[]) => void;
    multiple?: boolean;
    accept?: string;
  }
  
  export function FileUploadField({
    label,
    onFilesChange,
    multiple = true,
    accept,
  }: FileUploadFieldProps) {
    const handleChange = (
      e: React.ChangeEvent<HTMLInputElement>
    ) => {
      const list = e.target.files;
      if (!list) {
        onFilesChange([]);
        return;
      }
      const files: File[] = [];
      for (let i = 0; i < list.length; i += 1) {
        const f = list.item(i);
        if (f) files.push(f);
      }
      onFilesChange(files);
    };
  
    return (
      <div className="flex flex-col gap-1">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
          {label}
        </span>
        <input
          type="file"
          multiple={multiple}
          accept={accept}
          onChange={handleChange}
          className="block w-full text-sm text-gray-900 dark:text-gray-100
            file:mr-4 file:py-2 file:px-3
            file:rounded file:border-0
            file:text-sm file:font-semibold
            file:bg-primary file:text-white
            hover:file:bg-primary-dark
            dark:file:bg-primary-dark dark:hover:file:bg-primary"
        />
      </div>
    );
  }
  