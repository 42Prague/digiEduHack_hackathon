import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function Card({ className, title, children, href, }) {
    return (_jsxs("a", { className: className, href: `${href}?utm_source=create-turbo&utm_medium=basic&utm_campaign=create-turbo"`, rel: "noopener noreferrer", target: "_blank", children: [_jsxs("h2", { children: [title, " ", _jsx("span", { children: "->" })] }), _jsx("p", { children: children })] }));
}
