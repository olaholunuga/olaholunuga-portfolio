import React, { useEffect, useState, useRef } from "react";
import { io } from "socket.io-client";

export default function StreamDemo() {
  const [socket, setSocket] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [message, setMessage] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    const s = io(import.meta.env.VITE_WS_URL || "http://localhost:5000", {
      transports: ["websocket"],
    });

    s.on("connect", () => {
      console.log("WS connected:", s.id);
    });

    s.on("agent_response_start", ({ agent, request_id }) => {
      console.log("Start:", agent, request_id);
      setChunks([]); // reset display
    });

    s.on("agent_response_chunk", ({ chunk }) => {
      console.log("Chunk:", chunk);
      setChunks((prev) => [...prev, chunk]);
    });

    s.on("agent_response_end", ({ message, duration_ms }) => {
      console.log("End:", message, `(${duration_ms}ms)`);
    });

    s.on("agent_response_error", ({ error }) => {
      console.error("Error:", error);
    });

    setSocket(s);
    return () => {
      s.disconnect();
    };
  }, []);

  useEffect(() => {
    // scroll to end when chunks change
    if (endRef.current) {
      endRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chunks]);

  const sendMessage = () => {
    console.log("Sending:", { agent: "welcome", message, stream: true });
    if (!socket) return;
    socket.emit("chat_message", {
      agent: "welcome",
      message,
      stream: true,
    });
  };
//   const sendMessage = () => {
//   console.log("Sending:", { agent: "demo_stream", message, stream: true });
//   socket.emit("chat_message", { agent: "demo_stream", message, stream: true });
// };


  return (
    <div style={{ padding: "20px" }}>
      <h2>Streaming Demo Agent</h2>
      <div
        style={{
          border: "1px solid #ccc",
          padding: "10px",
          height: "200px",
          overflowY: "auto",
          marginBottom: "10px",
          fontFamily: "monospace",
        }}
      >
        {chunks.map((c, i) => (
          <span key={i}>{c}</span>
        ))}
        <div ref={endRef} />
      </div>
      <input
        type="text"
        placeholder="Type a message..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        style={{ marginRight: "5px" }}
      />
      <button onClick={sendMessage}>Send (Stream)</button>
    </div>
  );
}