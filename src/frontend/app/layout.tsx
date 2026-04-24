import type { Metadata } from "next";
import React from "react";

export const metadata: Metadata = {
  title: "Tuoke Agent Frontend",
  description: "Lead report MVP frontend for Tuoke Agent",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
