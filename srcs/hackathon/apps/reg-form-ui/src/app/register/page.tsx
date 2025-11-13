"use client";

import { useState } from "react"; // Import useState
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import Container from "@mui/material/Container";
import Stack from "@mui/material/Stack";

// --- MODIFIED RegFormInput COMPONENT ---
// It now needs value and onChange props to be a controlled component.
interface RegFormTextInput {
  labelValue: string;
  textFieldId: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  helperTextValue?: string;
  type?: string;
}

function RegFormInput({
  labelValue,
  textFieldId,
  value,
  onChange,
  helperTextValue = "",
  type = "text",
}: RegFormTextInput) {
  return (
    <TextField
      required
      fullWidth
      id={textFieldId}
      name={textFieldId} // Add name attribute for easier handling
      label={labelValue}
      variant="outlined"
      value={value}
      onChange={onChange}
      helperText={helperTextValue}
      type={type}
    />
  );
}

// Button component remains the same, but it should have type="submit"
function SubmitButton() {
  return (
    <Button type="submit" variant="contained">
      Register
    </Button>
  );
}

export default function HomePage() {
  const [formData, setFormData] = useState({
    email: "",
    firstName: "",
    lastName: "",
    password: "",
    passwordRepeat: "",
  });

  // 2. INPUT HANDLER: Updates state when user types
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prevState) => ({
      ...prevState,
      [name]: value,
    }));
  };

  // 3. SUBMISSION HANDLER: Sends data to the backend
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (formData.password !== formData.passwordRepeat) {
      alert("Passwords do not match!");
      return;
    }

    try {
      const response = await fetch("/api/users", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: formData.email,
          firstName: formData.firstName,
          lastName: formData.lastName,
          password: formData.password,
        }),
      });

      const result = await response.json();

      // STEP 1: DEBUGGING - Log the actual response to see its structure
      console.log("Backend response:", result);

      if (response.ok) {
        // STEP 2: SAFE ACCESS - Check if result.user exists before using it
        if (result && result.user && result.user.email) {
          alert("Registration successful! User: " + result.user.email);
          // ... reset form state
          setFormData({
            email: "",
            firstName: "",
            lastName: "",
            password: "",
            passwordRepeat: "",
          });
        } else {
          // This will trigger if the response was "ok" but didn't have the user data
          alert("Registration successful, but couldn't get user details back.");
        }
      } else {
        throw new Error(result.message || "Something went wrong");
      }
    } catch (error) {
      console.error("Submission error:", error);
      alert("Failed to register. Please check the console for details.");
    }
  };

  return (
    <Container
      maxWidth="sm"
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Attach the handleSubmit function to the form's onSubmit event */}
      <form onSubmit={handleSubmit}>
        <Stack spacing={2}>
          <label>Registration Form</label>
          <RegFormInput
            labelValue={"Email"}
            textFieldId={"email"}
            value={formData.email}
            onChange={handleChange}
          />
          <RegFormInput
            labelValue={"First Name"}
            textFieldId={"firstName"}
            value={formData.firstName}
            onChange={handleChange}
          />
          <RegFormInput
            labelValue={"Last Name"}
            textFieldId={"lastName"}
            value={formData.lastName}
            onChange={handleChange}
          />
          <RegFormInput
            labelValue={"Password"}
            textFieldId={"password"}
            type={"password"}
            value={formData.password}
            onChange={handleChange}
          />
          <RegFormInput
            labelValue={"Repeat Password"}
            textFieldId={"passwordRepeat"}
            type={"password"}
            value={formData.passwordRepeat}
            onChange={handleChange}
          />
          <SubmitButton />
        </Stack>
      </form>
    </Container>
  );
}
