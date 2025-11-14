import "~/styles/globals.css";
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';

import { type Metadata } from "next";
import { Geist } from "next/font/google";

import { TRPCReactProvider } from "~/trpc/react";

import { ColorSchemeScript, MantineProvider, mantineHtmlProps } from '@mantine/core';
import { Notifications } from '@mantine/notifications';

export const metadata: Metadata = {
  title: "EDU Změna Formuláře",
  description: "Formuláře EDU Změna",
  icons: [{ rel: "icon", url: "/favicon.ico" }],
};

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist-sans",
});

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="cs" className={`${geist.variable}`} {...mantineHtmlProps}>
      <head>
        <ColorSchemeScript />
      </head>
      <body>
        <MantineProvider>
          <Notifications />
          <TRPCReactProvider>{children}</TRPCReactProvider>
        </MantineProvider>
      </body>
    </html>
  );
}
