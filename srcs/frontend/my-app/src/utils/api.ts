import axios from "axios";

const BACKEND_BASE_URL = "http://127.0.0.1:8000";

const apiClient = axios.create({
  baseURL: BACKEND_BASE_URL,
});

export interface UploadPayload {
  region: string;
  school: string;
  activity: string;
  files: File[];
}

export async function uploadDocuments({
  region,
  school,
  activity,
  files,
}: UploadPayload): Promise<void> {
  const formData = new FormData();
  formData.append("region", region);
  formData.append("school", school);
  formData.append("activity", activity);

  files.forEach((file) => {
    formData.append("files", file);
  });

  await apiClient.post("/upload_document_files", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
}
