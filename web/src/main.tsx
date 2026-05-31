import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import "./styles.css";

const testSpeed = new URLSearchParams(window.location.search).get("testSpeed");
if (testSpeed === "1.5") {
  document.documentElement.dataset.testSpeed = "1.5";
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
