import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/tokens.css";
// The rare/dashboard design system. Loaded HERE rather than per route, because it defines
// custom properties and a missing custom property does not fail — the declaration using it
// is silently dropped. Four routes imported it individually and a fifth (cancer) did not get
// it: Vite emitted it as its own CSS chunk that the new route's chunk never linked, so
// `background: var(--r-brand)` resolved to transparent and every filled dumbbell end was
// invisible. Nothing errored, and nothing looked broken enough to notice. A token file that
// can be absent is a class of bug, not an instance.
import "./design/rare-tokens.css";
import "./styles/app.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
