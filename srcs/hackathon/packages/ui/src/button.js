"use client";
import { jsx as _jsx } from "react/jsx-runtime";
export const Button = ({ children, className, appName }) => {
    return (_jsx("button", { className: className, onClick: () => alert(`Hello from your ${appName} app!`), children: children }));
};
