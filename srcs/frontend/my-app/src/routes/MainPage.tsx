import { useState } from "react";
import type { FormEvent } from "react";
import { FileUploadField } from "../components/form/FileUploadField";
import { uploadDocuments } from "../utils/api";

export function MainPage() {
  const [region, setRegion] = useState("");
  const [school, setSchool] = useState("");
  const [activity, setActivity] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setStatus(null);
    setError(null);

    if (!region || !school || !activity) {
      setError("Region, school and activity are required");
      return;
    }
    if (!files.length) {
      setError("Select at least one file to upload");
      return;
    }

    try {
      setSubmitting(true);
      await uploadDocuments({
        region,
        school,
        activity,
        files,
      });
      setStatus("Files uploaded successfully");
      setFiles([]);
    } catch (err: any) {
      setError(err?.message || "Upload failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl shadow-sm p-6">
        <h1 className="text-xl font-semibold mb-1">Upload documents</h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Provide context and upload one or more files
        </p>

        {error && (
          <div className="mb-3 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        {status && (
          <div className="mb-3 text-sm text-emerald-600 dark:text-emerald-400">
            {status}
          </div>
        )}

        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-200">
                Region
              </label>
              <input
                type="text"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="px-3 py-2 rounded border text-sm bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-200">
                School
              </label>
              <input
                type="text"
                value={school}
                onChange={(e) => setSchool(e.target.value)}
                className="px-3 py-2 rounded border text-sm bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-200">
                Activity
              </label>
              <input
                type="text"
                value={activity}
                onChange={(e) => setActivity(e.target.value)}
                className="px-3 py-2 rounded border text-sm bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
          </div>

          <FileUploadField label="Files" multiple onFilesChange={setFiles} />

          {files.length > 0 && (
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Selected files: {files.length}
            </p>
          )}

          <div className="mt-2">
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex justify-center items-center px-4 py-2 rounded-md text-sm font-medium text-white bg-primary hover:bg-primary-dark disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {submitting ? "Uploading..." : "Upload"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
