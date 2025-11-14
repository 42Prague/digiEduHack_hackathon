"use client";

import type React from "react";
import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Upload, X, Plus } from "lucide-react"; // Added Plus icon
import Modal from "@/components/ui/modal";
import { Progress } from "@/components/ui/progress";

interface NewInterventionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface UploadedFile {
  name: string;
  size: number;
  isUploading: boolean;
  uploadProgress: number;
  error: string | null;
}

interface UploadResult {
  fileName: string;
  path: string;
  type: string;
  processed: boolean;
}

// --- NEW PARTICIPANT INTERFACES ---
interface SchoolStaff {
  name: string;
  age: number | "";
  // Changed grade type to a union of literal strings for type safety
  grade: "Teacher" | "Director" | "";
}

interface Mentor {
  name: string;
  subject: string;
}

export default function NewInterventionModal({
  isOpen,
  onClose,
}: NewInterventionModalProps) {
  const [formData, setFormData] = useState({
    schoolName: "",
    interventionType: "",
    // Note: studentCount, duration, focus, description are auxiliary fields
  });

  // --- NEW PARTICIPANT STATE ---
  const [schoolStaff, setSchoolStaff] = useState<SchoolStaff[]>([]);
  const [mentors, setMentors] = useState<Mentor[]>([]);

  const [filesToUpload, setFilesToUpload] = useState<File[]>([]);
  const [uploadStatuses, setUploadStatuses] = useState<UploadedFile[]>([]);

  const [rawData, setRawData] = useState<string>("");

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    const { name, value } = e.target;
    // Check if the change is for the new rawData state
    if (name === "rawData") {
      setRawData(value);
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  // --- NEW PARTICIPANT HANDLERS ---
  const handleAddStaff = () => {
    // Initializing 'grade' to an empty string which is allowed by the interface
    setSchoolStaff((prev) => [...prev, { name: "", age: "", grade: "" }]);
  };

  const handleRemoveStaff = (index: number) => {
    setSchoolStaff((prev) => prev.filter((_, i) => i !== index));
  };

  const handleStaffChange = (
    index: number,
    field: keyof SchoolStaff,
    // The value type is now more specific for 'grade'
    value: string | "Teacher" | "Director"
  ) => {
    setSchoolStaff((prev) =>
      prev.map((staff, i) =>
        i === index
          ? {
              ...staff,
              // Cast value to the specific type for 'grade' or keep as string/number for others
              [field]: field === "age" ? (value ? Number(value) : "") : value,
            }
          : staff
      )
    );
  };

  const handleAddMentor = () => {
    setMentors((prev) => [...prev, { name: "", subject: "" }]);
  };

  const handleRemoveMentor = (index: number) => {
    setMentors((prev) => prev.filter((_, i) => i !== index));
  };

  const handleMentorChange = (
    index: number,
    field: keyof Mentor,
    value: string
  ) => {
    setMentors((prev) =>
      prev.map((mentor, i) =>
        i === index ? { ...mentor, [field]: value } : mentor
      )
    );
  };
  // --- END PARTICIPANT HANDLERS ---

  // ... (handleFileChange and uploadFiles logic remains the same) ...

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setFilesToUpload((prev) => [...prev, ...newFiles]);

      const newStatuses: UploadedFile[] = newFiles.map((file) => ({
        name: file.name,
        size: file.size,
        isUploading: false,
        uploadProgress: 0,
        error: null,
      }));
      setUploadStatuses((prev) => [...prev, ...newStatuses]);

      e.target.value = "";
    }
  };

  // Placeholder for missing function in original code
  const handleRemoveFile = (fileName: string) => {
    setFilesToUpload((prev) => prev.filter((file) => file.name !== fileName));
    setUploadStatuses((prev) =>
      prev.filter((status) => status.name !== fileName)
    );
  };

  const uploadFiles = async (): Promise<UploadResult[]> => {
    if (filesToUpload.length === 0) return [];

    const uploadedFilesData: UploadResult[] = [];

    const getFileExtension = (filename: string): string => {
      // Find the last dot in the filename
      const lastDotIndex = filename.lastIndexOf(".");
      // If no dot or dot is the first character, return 'file' or 'other'
      if (lastDotIndex === -1 || lastDotIndex === 0) {
        return "other";
      }
      // Return the lowercase string after the last dot (e.g., 'pdf', 'csv')
      return filename.substring(lastDotIndex + 1).toLowerCase();
    };

    const uploadPromises = filesToUpload.map((file) => {
      return new Promise<void>(async (resolve) => {
        const fileStatusIndex = uploadStatuses.findIndex(
          (s) => s.name === file.name
        );
        if (fileStatusIndex === -1) return resolve();

        setUploadStatuses((prev) => {
          const newStatuses = [...prev];
          newStatuses[fileStatusIndex] = {
            ...newStatuses[fileStatusIndex],
            isUploading: true,
          };
          return newStatuses;
        });

        try {
          const data = new FormData();
          data.append("file", file);
          data.append("folder", formData.schoolName || "interventions");

          const response = await fetch("/api/upload", {
            method: "POST",
            body: data,
          });

          if (!response.ok) {
            throw new Error("Upload failed on server.");
          }

          const result = await response.json();

          setUploadStatuses((prev) => {
            const newStatuses = [...prev];
            newStatuses[fileStatusIndex] = {
              ...newStatuses[fileStatusIndex],
              isUploading: false,
              uploadProgress: 100,
              error: null,
            };
            return newStatuses;
          });

          const fileType = getFileExtension(file.name);

          uploadedFilesData.push({
            fileName: file.name,
            path: result.blob_name,
            type: fileType,
            processed: false,
          });
        } catch (error) {
          console.error(`Error uploading ${file.name}:`, error);
          setUploadStatuses((prev) => {
            const newStatuses = [...prev];
            newStatuses[fileStatusIndex] = {
              ...newStatuses[fileStatusIndex],
              isUploading: false,
              error: "Upload failed",
              uploadProgress: 0,
            };
            return newStatuses;
          });
        } finally {
          resolve();
        }
      });
    });

    await Promise.all(uploadPromises);
    return uploadedFilesData;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 1. Upload files first
    const uploadedFilesData = await uploadFiles();

    // 2. Now submit the form data along with the uploaded file references
    const finalData = {
      // Top-level Zod fields
      schoolName: formData.schoolName,
      interventionType: formData.interventionType,
      regionName: "Kutnohorsko", // Hardcoded/Defaulted
      guideName: "Josef Pruvodce", // Hardcoded/Defaulted
      rawData: rawData,

      // --- NEW: Use dynamic participant state ---
      listOfParticipants: {
        schoolStaff: schoolStaff.map((staff) => ({
          ...staff,
          age: staff.age === "" ? 0 : (staff.age as number), // Ensure age is number for Zod
        })),
        mentors: mentors,
      },

      // File references for server-side mapping
      listOfFiles: uploadedFilesData,

      // Omitted old auxiliary fields (duration, focus, description) for cleaner Zod mapping.
      // Include them if your server needs them for other tables.
    };

    console.log("Submitting intervention with attachments:", finalData);
    // --- 3. Push form data to the server-side API route ---
    try {
      const response = await fetch("/api/interventions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(finalData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.message || "Failed to save intervention data."
        );
      }

      const result = await response.json();
      console.log("Database submission successful:", result);

      // --- 4. Reset and close on success ---
      // setFilesToUpload([]);
      // setUploadStatuses([]);
      // setFormData(...)
      onClose();
    } catch (error) {
      console.error("Submission error:", error);
      // Display an error message to the user
    }
  };

  // --- Wrap the form in the Modal component ---
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="New Intervention Entry"
      size="lg"
    >
      <form onSubmit={handleSubmit} className="pt-2">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Main Form Content (2/3 width) */}
          <div className="lg:col-span-2 space-y-6">
            {/* School & Intervention Type */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-foreground">
                  School
                </label>
                <select
                  name="schoolName"
                  value={formData.schoolName}
                  onChange={handleInputChange}
                  className="mt-2 w-full rounded-md border border-input bg-card px-4 py-2 text-foreground focus:border-accent focus:outline-none"
                >
                  <option value="">Select school</option>
                  <option value="capek">ZŠ Karla Čapka</option>
                  <option value="jarov">Scio škola Praha Jarov</option>
                  <option value="hostinska">Základní škola Hostýnská</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground">
                  Intervention Type
                </label>
                <select
                  name="interventionType"
                  value={formData.interventionType}
                  onChange={handleInputChange}
                  className="mt-2 w-full rounded-md border border-input bg-card px-4 py-2 text-foreground focus:border-accent focus:outline-none"
                >
                  <option value="">Select type</option>
                  <option value="academic">Academic Support</option>
                  <option value="behavioral">Behavioral Support</option>
                  <option value="social">Social-Emotional</option>
                  <option value="literacy">Literacy Program</option>
                </select>
              </div>
            </div>

            {/* Participants Section */}
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-foreground border-b pb-2">
                School Staff Participants 🧑‍🏫
              </h2>
              <div className="space-y-4">
                {schoolStaff.map((staff, index) => (
                  <Card
                    key={index}
                    className="p-4 border border-border/70 grid gap-3 grid-cols-6 items-end"
                  >
                    <div className="col-span-3">
                      <label className="block text-xs font-medium text-muted-foreground">
                        Name
                      </label>
                      <input
                        type="text"
                        value={staff.name}
                        onChange={(e) =>
                          handleStaffChange(index, "name", e.target.value)
                        }
                        placeholder="Staff Name"
                        className="mt-1 w-full rounded-md border border-input bg-card px-3 py-1.5 text-sm"
                      />
                    </div>
                    {/* The Age input is commented out, leaving it that way */}
                    {/* <div className="col-span-1">
                      <label className="block text-xs font-medium text-muted-foreground">
                        Age
                      </label>
                      <input
                        type="number"
                        value={staff.age === "" ? "" : staff.age.toString()}
                        onChange={(e) =>
                          handleStaffChange(index, "age", e.target.value)
                        }
                        placeholder="Age"
                        className="mt-1 w-full rounded-md border border-input bg-card px-3 py-1.5 text-sm"
                      />
                    </div> */}

                    {/* --- MODIFIED: Grade/Role is now a selectable dropdown --- */}
                    <div className="col-span-2">
                      <label className="block text-xs font-medium text-muted-foreground">
                        Grade/Role
                      </label>
                      <select
                        value={staff.grade}
                        onChange={(e) =>
                          handleStaffChange(index, "grade", e.target.value)
                        }
                        className="mt-1 w-full rounded-md border border-input bg-card px-3 py-1.5 text-sm"
                      >
                        <option value="">Select Role</option>
                        <option value="Teacher">Teacher</option>
                        <option value="Director">Director</option>
                      </select>
                    </div>
                    {/* ----------------- END MODIFIED ----------------- */}

                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 hover:bg-red-100"
                      onClick={() => handleRemoveStaff(index)}
                    >
                      <X className="h-4 w-4 text-muted-foreground" />
                    </Button>
                  </Card>
                ))}
              </div>
              <Button
                type="button"
                variant="outline"
                onClick={handleAddStaff}
                className="w-full justify-center text-sm"
              >
                <Plus className="h-4 w-4 mr-2" /> Add School Staff
              </Button>
            </div>

            {/* The Mentors/Guides section is commented out, leaving it that way */}
            {/*<div className="space-y-6">
               <h2 className="text-lg font-semibold text-foreground border-b pb-2">
                Mentors/Guides 🧠
              </h2>
              <div className="space-y-4">
                {mentors.map((mentor, index) => (
                  <Card
                    key={index}
                    className="p-4 border border-border/70 grid gap-3 grid-cols-6 items-end"
                  >
                    <div className="col-span-3">
                      <label className="block text-xs font-medium text-muted-foreground">
                        Name
                      </label>
                      <input
                        type="text"
                        value={mentor.name}
                        onChange={(e) =>
                          handleMentorChange(index, "name", e.target.value)
                        }
                        placeholder="Mentor Name"
                        className="mt-1 w-full rounded-md border border-input bg-card px-3 py-1.5 text-sm"
                      />
                    </div>
                    <div className="col-span-3">
                      <label className="block text-xs font-medium text-muted-foreground">
                        Subject/Focus
                      </label>
                      <input
                        type="text"
                        value={mentor.subject}
                        onChange={(e) =>
                          handleMentorChange(index, "subject", e.target.value)
                        }
                        placeholder="Subject"
                        className="mt-1 w-full rounded-md border border-input bg-card px-3 py-1.5 text-sm"
                      />
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 hover:bg-red-100"
                      onClick={() => handleRemoveMentor(index)}
                    >
                      <X className="h-4 w-4 text-muted-foreground" />
                    </Button>
                  </Card>
                ))}
              </div> 
              <Button
                type="button"
                variant="outline"
                onClick={handleAddMentor}
                className="w-full justify-center text-sm"
              >
                <Plus className="h-4 w-4 mr-2" /> Add Mentor
              </Button>
            </div>*/}
            {/* End Participants Section */}

            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-foreground border-b pb-2">
                Raw Intervention Text 📝
              </h2>
              <label className="block text-sm font-medium text-muted-foreground">
                Copy/paste the full, unprocessed text (e.g., meeting transcript,
                notes, or focus group data) here.
              </label>
              <textarea
                name="rawData"
                value={rawData}
                onChange={handleInputChange}
                rows={8} // Adjust height as needed
                placeholder="Start typing or paste the intervention data here..."
                className="mt-1 w-full rounded-md border border-input bg-card px-4 py-3 text-sm resize-y focus:border-accent focus:outline-none"
              />
            </div>
          </div>

          {/* Sidebar (1/3 width) */}
          <div className="space-y-4">
            {/* File Upload remains here */}
            <Card className="border-border bg-card p-6">
              <h3 className="mb-4 font-semibold text-foreground">
                Upload Documents
              </h3>

              {/* HIDDEN FILE INPUT */}
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                multiple
                className="hidden"
                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
              />

              {/* VISIBLE DROP ZONE/TRIGGER */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className="rounded-md border-2 border-dashed border-border bg-card/50 p-6 text-center cursor-pointer hover:border-accent transition-colors"
              >
                <Upload className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  Click to select or drag files here
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  PDF, DOC, images up to 10MB
                </p>
              </div>

              {/* FILE LIST AND STATUS */}
              {uploadStatuses.length > 0 && (
                <div className="mt-4 max-h-40 overflow-y-auto space-y-2 pr-2">
                  {uploadStatuses.map((fileStatus) => (
                    <div
                      key={fileStatus.name}
                      className="flex items-center justify-between p-2 rounded-md bg-accent/10"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium truncate">
                          {fileStatus.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {fileStatus.isUploading
                            ? "Uploading..."
                            : fileStatus.error
                              ? `Error: ${fileStatus.error}`
                              : fileStatus.uploadProgress === 100
                                ? "Uploaded"
                                : "Ready"}
                        </p>
                        <Progress
                          value={fileStatus.uploadProgress}
                          className="h-1 mt-1"
                        />
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 ml-2 hover:bg-red-100"
                        onClick={() => handleRemoveFile(fileStatus.name)}
                        disabled={fileStatus.isUploading}
                      >
                        <X className="h-4 w-4 text-muted-foreground" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* Action Buttons */}
            <Button
              type="submit"
              className="w-full bg-accent hover:bg-accent/90 text-accent-foreground"
              disabled={uploadStatuses.some((s) => s.isUploading)}
            >
              Create Intervention
            </Button>
            <Button
              variant="outline"
              onClick={onClose}
              className="w-full border-border text-foreground hover:bg-card bg-transparent"
              disabled={uploadStatuses.some((s) => s.isUploading)}
            >
              Cancel
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
