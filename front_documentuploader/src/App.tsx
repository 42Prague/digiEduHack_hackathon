import { useState } from "react";
import type React from "react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import { Card, CardContent, CardHeader } from "./components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./components/ui/select";
import { ImageWithFallback } from "./components/figma/ImageWithFallback";
import { FileText, Send, CheckCircle, UploadCloud } from "lucide-react";
// @ts-ignore
import { toast } from "sonner@2.0.3";
import { Toaster } from "./components/ui/sonner";

// formats "01022025" -> "01/02/2025"
function formatDateInput(value: string) {
  const digits = value.replace(/\D/g, "").slice(0, 8);
  if (digits.length <= 2) return digits;
  if (digits.length <= 4) return `${digits.slice(0, 2)}/${digits.slice(2)}`;
  return `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`;
}

export default function App() {
  const [formData, setFormData] = useState({
    reportDate: "",
    region: "",
    submittedBy: "",
    email: "",
    description: "",
  });

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // Upload files first
    try {
      setUploading(true);
      for (const file of selectedFiles) {
        const form = new FormData();
        form.append("file", file);
        form.append("metadata", JSON.stringify({ regions: ["prague"] }));

        const res = await fetch("http://127.0.0.1:5000/api/ingest", {
          method: "POST",
          body: form,
        });

        if (!res.ok) {
          throw new Error(`Failed to upload ${file.name}`);
        }
      }

      toast.success("Report submitted successfully!", {
        description:
            "Your report has been received and files uploaded successfully.",
      });

      // Reset form
      setFormData({
        reportDate: "",
        region: "",
        submittedBy: "",
        email: "",
        description: "",
      });
      setSelectedFiles([]);
    } catch (err) {
      console.error(err);
      toast.error("Error uploading files");
    } finally {
      setUploading(false);
    }
  };

  const handleInputChange = (
      e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;

    if (name === "reportDate") {
      const formatted = formatDateInput(value);
      setFormData((prev) => ({ ...prev, reportDate: formatted }));
      return;
    }

    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <Toaster />

        {/* Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center gap-2">
                <FileText className="w-8 h-8 text-blue-600" />
                <span className="text-blue-600">ReportHub</span>
              </div>
              <div className="flex items-center gap-4">
                <Button variant="ghost">Dashboard</Button>
                <Button variant="ghost">History</Button>
                <Button variant="outline">Help</Button>
              </div>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Form */}
            <div className="lg:col-span-2">
              <Card className="shadow-lg">
                <CardHeader className="border-b border-gray-100 pb-6">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <FileText className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <h1 className="text-blue-900">Submit Report</h1>
                      <p className="text-gray-600">
                        Fill out the form below to submit your report
                      </p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Basic Information */}
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="region">Region *</Label>
                          <Select
                              value={formData.region}
                              onValueChange={(value) =>
                                  setFormData((prev) => ({ ...prev, region: value }))
                              }
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select region" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="praha">Praha</SelectItem>
                              <SelectItem value="stredocesky">
                                Středočeský kraj
                              </SelectItem>
                              <SelectItem value="jihocesky">
                                Jihočeský kraj
                              </SelectItem>
                              <SelectItem value="plzensky">
                                Plzeňský kraj
                              </SelectItem>
                              <SelectItem value="karlovarsky">
                                Karlovarský kraj
                              </SelectItem>
                              <SelectItem value="ustecky">Ústecký kraj</SelectItem>
                              <SelectItem value="liberecky">Liberecký kraj</SelectItem>
                              <SelectItem value="kralovehradecky">
                                Královéhradecký kraj
                              </SelectItem>
                              <SelectItem value="pardubicky">Pardubický kraj</SelectItem>
                              <SelectItem value="vysocina">Kraj Vysočina</SelectItem>
                              <SelectItem value="jihomoravsky">
                                Jihomoravský kraj
                              </SelectItem>
                              <SelectItem value="olomoucky">Olomoucký kraj</SelectItem>
                              <SelectItem value="zlinsky">Zlínský kraj</SelectItem>
                              <SelectItem value="moravskoslezsky">
                                Moravskoslezský kraj
                              </SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    </div>

                    {/* Report Details */}
                    <div className="space-y-4">
                      <h3 className="text-gray-900">Report Details</h3>

                      <div className="space-y-2">
                        <Label htmlFor="description">Description *</Label>
                        <Textarea
                            id="description"
                            name="description"
                            placeholder="Provide a detailed description of your report..."
                            value={formData.description}
                            onChange={handleInputChange}
                            rows={6}
                            required
                            className="resize-none"
                        />
                        <p className="text-xs text-gray-500">
                          Minimum 50 characters required
                        </p>
                      </div>
                    </div>

                    {/* File Attachments */}
                    <div className="space-y-4">
                      <h3 className="text-gray-900">Attachments</h3>
                      <p className="text-sm text-gray-600">
                        Upload supporting documents, audio files, or other relevant
                        materials
                      </p>

                      <div className="flex flex-col gap-2">
                        <label className="flex items-center gap-2 cursor-pointer text-blue-600">
                          <UploadCloud className="w-5 h-5" />
                          <span>Select Files</span>
                          <Input
                              type="file"
                              multiple
                              className="hidden"
                              onChange={handleFileChange}
                              accept=".pdf,.docx,.md,.mp3"
                          />
                        </label>

                        {selectedFiles.length > 0 && (
                            <ul className="text-sm text-gray-700 space-y-1">
                              {selectedFiles.map((file) => (
                                  <li key={file.name}>{file.name}</li>
                              ))}
                            </ul>
                        )}
                      </div>
                    </div>

                    {/* Submit Button */}
                    <div className="flex gap-3 pt-4">
                      <Button
                          type="submit"
                          className="flex-1"
                          size="lg"
                          disabled={uploading}
                      >
                        <Send className="w-4 h-4 mr-2" />
                        {uploading ? "Uploading..." : "Submit Report"}
                      </Button>
                      <Button type="button" variant="outline" size="lg">
                        Save Draft
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Team Images */}
              <Card className="overflow-hidden shadow-lg">
                <CardContent className="p-0">
                  <div className="relative h-48">
                    <ImageWithFallback
                        src="https://images.unsplash.com/photo-1709715357441-da1ec3d0bd4a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxidXNpbmVzcyUyMHBlb3BsZSUyMHdvcmtpbmd8ZW58MXx8fHwxNzYzMDMxNzQ2fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
                        alt="Business people working"
                        className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                    <div className="absolute bottom-4 left-4 right-4">
                      <h3 className="text-white mb-1">Our Team</h3>
                      <p className="text-white/90 text-sm">
                        Working together to support you
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="overflow-hidden shadow-lg">
                <CardContent className="p-0">
                  <div className="relative h-48">
                    <ImageWithFallback
                        src="https://images.unsplash.com/photo-1568992687947-868a62a9f521?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxvZmZpY2UlMjB0ZWFtd29ya3xlbnwxfHx8fDE3NjMwMTM2OTN8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
                        alt="Office teamwork"
                        className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                    <div className="absolute bottom-4 left-4 right-4">
                      <h3 className="text-white mb-1">Collaboration</h3>
                      <p className="text-white/90 text-sm">
                        Your input helps us improve
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Guidelines */}
              <Card className="shadow-lg">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <h3 className="text-gray-900">Submission Guidelines</h3>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3 text-sm text-gray-600">
                    <li className="flex gap-2">
                      <span className="text-blue-600 flex-shrink-0">•</span>
                      <span>Fill out all required fields marked with *</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="text-blue-600 flex-shrink-0">•</span>
                      <span>Provide detailed and accurate information</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="text-blue-600 flex-shrink-0">•</span>
                      <span>Upload relevant supporting documents</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="text-blue-600 flex-shrink-0">•</span>
                      <span>Maximum file size: 10MB per file</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="text-blue-600 flex-shrink-0">•</span>
                      <span>You will receive a confirmation email</span>
                    </li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
  );
}
