
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Ensure we have a valid DOM node
const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Failed to find the root element");
}

// Use the createRoot API instead of ReactDOM.render
const root = createRoot(rootElement);
root.render(<App />);
