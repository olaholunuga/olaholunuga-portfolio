import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
//
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import StreamDemo from "./pages/StreamDemo";
// ... other imports

function App() {
  return (
    <Router>
      <Routes>
        {/* ...your other routes */}
        <Route path="/stream-demo" element={<StreamDemo />} />
      </Routes>
    </Router>
  );
}

export default App;