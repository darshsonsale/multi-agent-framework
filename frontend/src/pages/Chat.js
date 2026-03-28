import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./Chat.css";

// JSON syntax highlight
function highlightJson(json) {
  return json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    (match) => {
      let cls = "num";
      if (/^"/.test(match)) cls = /:$/.test(match) ? "key" : "str";
      else if (/true|false/.test(match)) cls = "bool";
      else if (/null/.test(match)) cls = "null";
      return `<span class="${cls}">${match}</span>`;
    }
  );
}

function Chat() {
  const navigate = useNavigate();

  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Welcome to the eFIR System. Please describe the incident in detail so I can assist you in filing your First Information Report.",
    },
  ]);
  const [input, setInput] = useState("");
  const [firData, setFirData] = useState({});
  const [state, setState] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const chatBottomRef = useRef(null);
  const inputRef = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        await sendAudioToBackend(audioBlob);
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsListening(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Microphone access denied or not supported.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isListening) {
      mediaRecorderRef.current.stop();
      setIsListening(false);
    }
  };

  const sendAudioToBackend = async (blob) => {
    setIsProcessing(true);
    const formData = new FormData();
    formData.append("file", blob, "voice.wav");

    try {
      const res = await fetch("http://127.0.0.1:8000/voice-to-text", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to transcribe audio");
      }

      const data = await res.json();
      if (data.transcript) {
        // Append transcribed text
        setInput((prev) => (prev ? `${prev} ${data.transcript}` : data.transcript));
      }
    } catch (err) {
      console.error("Transcription error:", err);
      alert(`Error transcribing: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleListening = () => {
    if (isListening) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input, state }),
      });

      if (!res.ok) throw new Error("Server error");

      const data = await res.json();
      setFirData(data.fir || {});
      setState(data.state || null);
      if (data.is_complete !== undefined) setIsComplete(data.is_complete);

      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: data.reply || "No response." },
      ]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "⚠ Could not reach the server. Please ensure the backend is running.",
        },
      ]);
    }

    setIsTyping(false);
    inputRef.current?.focus();
  };

  const handleSubmitForm = async () => {
    try {
      const res = await fetch("http://localhost:8000/submit", {
        method: "POST",
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Submission failed");

      alert(`🎉 ${data.message}`);
      // Optional: navigate away or reset
    } catch (err) {
      console.error(err);
      alert(`❌ Submission Error: ${err.message}`);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const fieldCount = Object.keys(firData).length;
  const jsonString = JSON.stringify(firData, null, 2);

  const handleGeneratePdf = async () => {
    try {
      const resp = await fetch("http://localhost:8000/generate-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      if (resp.ok) {
        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", "FIR_Report.pdf");
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
        
        // End conversation
        setMessages(prev => [...prev, { 
          sender: "bot", 
          text: "📄 The NCRB I.I.F.-I PDF has been generated successfully. This conversation is now concluded. If you need any further assistance, please start a new session." 
        }]);
        setIsComplete(false); // Hide the buttons
      } else {
        const err = await resp.json();
        alert(`❌ PDF Error: ${err.detail}`);
      }
    } catch (err) {
      alert("❌ Failed to connect to backend for PDF generation.");
    }
  };

  return (
    <div className="chat-page">

      {/* HEADER */}
      <header className="chat-header">
        <button className="back-home" onClick={() => navigate("/")}>
          ← eFIR
        </button>
        <div className="chat-header-center">
          <span className="chat-header-title">eFIR Assistant</span>
          <span className="chat-header-sub">Electronic First Information Report</span>
        </div>
        <div className="status-pill">
          <span className="status-dot" /> Live
        </div>
      </header>

      {/* BODY */}
      <div className="chat-body">

        {/* LEFT: Chat */}
        <section className="chat-col">
          <div className="messages-wrap">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`msg-row ${msg.sender}`}
                style={{ animationDelay: `${i * 0.04}s` }}
              >
                <div className="msg-label">
                  {msg.sender === "user" ? "You" : "eFIR Assistant"}
                </div>
                <div className={`msg-bubble ${msg.sender}`}>
                  {msg.text}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="msg-row bot">
                <div className="msg-label">eFIR Assistant</div>
                <div className="msg-bubble bot typing">
                  <span /><span /><span />
                </div>
              </div>
            )}

            <div ref={chatBottomRef} />
          </div>

          {/* SUBMIT BUTTON OPTION */}
          {isComplete && (
            <div className="submit-form-area animated-up">
              <div className="fir-complete-actions">
                <button className="submit-form-btn primary" onClick={handleSubmitForm}>
                  🚀 Submit FIR Form
                </button>
                <button className="submit-form-btn secondary" onClick={handleGeneratePdf}>
                  📄 Generate Complaint Form PDF
                </button>
              </div>
              <p className="submit-hint">All incident details captured. What would you like to do next?</p>
            </div>
          )}
          {/* Input Area */}
          <div className="chat-input-area">
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Describe the incident in detail…"
            />
            <button
              className={`mic-btn ${isListening ? "active" : ""} ${isProcessing ? "processing" : ""}`}
              onClick={toggleListening}
              disabled={isProcessing}
              title={isListening ? "Stop listening" : isProcessing ? "Processing..." : "Start voice typing (Sarvam AI)"}
            >
              <span className="mic-icon">
                {isProcessing ? "⏳" : isListening ? "🛑" : "🎤"}
              </span>
            </button>
            <button
              className="send-btn"
              onClick={sendMessage}
              disabled={!input.trim() || isTyping}
            >
              Send ↑
            </button>
          </div>
        </section>

        {/* DIVIDER */}
        <div className="col-divider" />

        {/* RIGHT: FIR Preview */}
        <section className="fir-col">
          <div className="fir-header">
            <span className="fir-icon">📋</span>
            <h3>FIR Report Data</h3>
            {fieldCount > 0 && (
              <span className="fir-count">
                {fieldCount} field{fieldCount !== 1 ? "s" : ""}
              </span>
            )}
            <span className="fir-live-tag">Live Preview</span>
          </div>

          <div className="fir-panel">
            {fieldCount === 0 ? (
              <div className="fir-empty">
                <div className="fir-empty-icon">🗂</div>
                <p>FIR fields will populate as you describe the incident</p>
              </div>
            ) : (
              <pre
                dangerouslySetInnerHTML={{ __html: highlightJson(jsonString) }}
              />
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

export default Chat;