"use client";

import type React from "react";
import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Upload, X } from "lucide-react";
import Modal from "@/components/ui/modal";
import { Progress } from "@/components/ui/progress"; // Assuming you have a Progress component

interface NewInterventionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// --- NEW INTERFACE FOR UPLOADED FILE STATUS ---
interface UploadedFile {
    name: string;
    size: number;
    isUploading: boolean;
    uploadProgress: number;
    error: string | null;
}

export default function NewInterventionModal({
  isOpen,
  onClose,
}: NewInterventionModalProps) {
  const [formData, setFormData] = useState({
    schoolName: "",
    interventionType: "",
    studentCount: "",
    duration: "",
    focus: "",
    description: "",
  });
  // State to hold the actual File objects selected by the user
  const [filesToUpload, setFilesToUpload] = useState<File[]>([]);
  // State to track upload status for display
  const [uploadStatuses, setUploadStatuses] = useState<UploadedFile[]>([]);
  
  // Ref to trigger the hidden file input
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // --- NEW FILE HANDLERS ---
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setFilesToUpload((prev) => [...prev, ...newFiles]);

      // Initialize status for new files
      const newStatuses: UploadedFile[] = newFiles.map(file => ({
          name: file.name,
          size: file.size,
          isUploading: false,
          uploadProgress: 0,
          error: null
      }));
      setUploadStatuses(prev => [...prev, ...newStatuses]);

      // Reset the input value to allow selecting the same file again
      e.target.value = '';
    }
  };

  const handleRemoveFile = (fileName: string) => {
      setFilesToUpload(prev => prev.filter(f => f.name !== fileName));
      setUploadStatuses(prev => prev.filter(s => s.name !== fileName));
  };
  
  const uploadFiles = async () => {
      if (filesToUpload.length === 0) return [];
      
      const uploadedFileNames: string[] = [];
      const uploadPromises = filesToUpload.map((file) => {
          return new Promise<void>(async (resolve) => {
              const fileStatusIndex = uploadStatuses.findIndex(s => s.name === file.name);
              if (fileStatusIndex === -1) return resolve();
              
              setUploadStatuses(prev => {
                  const newStatuses = [...prev];
                  newStatuses[fileStatusIndex] = { ...newStatuses[fileStatusIndex], isUploading: true };
                  return newStatuses;
              });

              // --- SIMULATED UPLOAD TO YOUR API ENDPOINT ---
              // You must create a Next.js API route (e.g., /api/upload) 
              // that uses your GcsFileManager to handle the file buffer.
              try {
                  const data = new FormData();
                  data.append('file', file);
                  // Optional: Add folder prefix, e.g., using the school name
                  data.append('folder', formData.schoolName || 'interventions'); 

                  const response = await fetch('/api/upload', { 
                      method: 'POST',
                      body: data,
                      // For progress tracking, you'd need a custom XHR/fetch implementation,
                      // but standard fetch doesn't expose progress easily.
                      // For simplicity, we'll update progress instantly upon success.
                  });

                  if (!response.ok) {
                      throw new Error('Upload failed on server.');
                  }

                  const result = await response.json();

                  setUploadStatuses(prev => {
                      const newStatuses = [...prev];
                      newStatuses[fileStatusIndex] = { 
                          ...newStatuses[fileStatusIndex], 
                          isUploading: false, 
                          uploadProgress: 100,
                          error: null
                      };
                      return newStatuses;
                  });
                  
                  uploadedFileNames.push(result.blob_name); // Assuming your API returns the GCS blob name
              } catch (error) {
                  console.error(`Error uploading ${file.name}:`, error);
                  setUploadStatuses(prev => {
                      const newStatuses = [...prev];
                      newStatuses[fileStatusIndex] = { 
                          ...newStatuses[fileStatusIndex], 
                          isUploading: false, 
                          error: 'Upload failed',
                          uploadProgress: 0
                      };
                      return newStatuses;
                  });
              } finally {
                  resolve();
              }
          });
      });

      await Promise.all(uploadPromises);
      return uploadedFileNames;
  };
  // --- END NEW FILE HANDLERS ---


  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 1. Upload files first
    const uploadedBlobNames = await uploadFiles();

    // 2. Now submit the form data along with the uploaded file references
    const finalData = {
        ...formData,
        // Include the references to the files successfully uploaded to GCS
        attachedDocuments: uploadedBlobNames, 
    };
    
    console.log("Submitting intervention with attachments:", finalData);
    // Add logic to save finalData to your database/API here

    // Reset and close on success
    // setFilesToUpload([]); 
    // setUploadStatuses([]);
    // setFormData(...)
    // onClose(); 
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
        {/* ... (Existing form fields remain here) ... */}

        <div className="grid gap-8 lg:grid-cols-3">
            {/* ... (Main Form Content) ... */}
            <div className="lg:col-span-2 space-y-6">
                {/* ... (School, Intervention Type, Count fields) ... */}
                <div>
                    <label className="block text-sm font-medium text-foreground">
                        School
                    </label>
                    <select
                        name="schoolName" // Corrected name
                        value={formData.schoolName}
                        onChange={handleInputChange}
                        className="mt-2 w-full rounded-md border border-input bg-card px-4 py-2 text-foreground focus:border-accent focus:outline-none"
                    >
                        <option value="">Select school</option>
                        <option value="capek">ZŠ Karla Čpaka</option>
                        <option value="jarov">Scio škola Praha Jarov</option>
                        <option value="hostinska">Základní škola Hostýnská</option>
                    </select>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
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

                <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                        <label className="block text-sm font-medium text-foreground">
                            Number of Participants
                        </label>
                        <input
                            type="number"
                            name="studentCount"
                            value={formData.studentCount}
                            onChange={handleInputChange}
                            placeholder="0"
                            className="mt-2 w-full rounded-md border border-input bg-card px-4 py-2 text-foreground placeholder:text-muted-foreground focus:border-accent focus:outline-none"
                        />
                    </div>
                </div>
            </div>

            {/* Sidebar */}
            <div className="space-y-4">
                {/* File Upload */}
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
                                        <p className="text-sm font-medium truncate">{fileStatus.name}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {fileStatus.isUploading ? 'Uploading...' : 
                                            fileStatus.error ? `Error: ${fileStatus.error}` :
                                            fileStatus.uploadProgress === 100 ? 'Uploaded' : 'Ready'}
                                        </p>
                                        <Progress value={fileStatus.uploadProgress} className="h-1 mt-1" />
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
                    disabled={uploadStatuses.some(s => s.isUploading)} // Disable while uploading
                >
                    Create Intervention
                </Button>
                <Button
                    variant="outline"
                    onClick={onClose}
                    className="w-full border-border text-foreground hover:bg-card bg-transparent"
                    disabled={uploadStatuses.some(s => s.isUploading)}
                >
                    Cancel
                </Button>
            </div>
        </div>
      </form>
    </Modal>
  );
}