// src/theme.ts
"use client";
import { createTheme } from "@mui/material/styles";

// This is the theme configuration for your app
const theme = createTheme({
  typography: {
    // This tells MUI to use the CSS variable for the font
    fontFamily: "var(--font-roboto)",
  },
  // You can add your own custom colors, etc. here
  palette: {
    mode: "dark",
    primary: {
      main: "#c9d6e1",
    },
  },
});

export default theme;
