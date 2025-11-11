import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import "./App.css";
import logo from "./logo.png"; // put logo.png inside /src

const App = () => {
  const [chats, setChats] = useState([{ id: Date.now(), messages: [] }]);
  const [activeChat, setActiveChat] = useState(chats[0].id);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const chatEndRef = useRef(null);
  const currentChat = chats.find((c) => c.id === activeChat);

  // Auto scroll to bottom when messages update
  useEffect(() => {
    if (currentChat?.messages.length > 0) {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [currentChat?.messages, isLoading]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { sender: "user", text: input.trim() };

    setChats((prev) =>
      prev.map((c) =>
        c.id === activeChat
          ? { ...c, messages: [...c.messages, userMessage] }
          : c
      )
    );

    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:5000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.text }),
      });

      if (!response.ok) throw new Error("Network error");

      const data = await response.json();

      // Create placeholder message for streaming
      setChats((prev) =>
        prev.map((c) =>
          c.id === activeChat
            ? { ...c, messages: [...c.messages, { sender: "llm", text: "" }] }
            : c
        )
      );

      // Streaming effect: add lines one by one
      const llmText = data.response.split("\n");
      let currentText = "";
      llmText.forEach((line, i) => {
        setTimeout(() => {
          currentText += line + "\n";
          setChats((prev) =>
            prev.map((c) =>
              c.id === activeChat
                ? {
                    ...c,
                    messages: [
                      ...c.messages.slice(0, -1),
                      { sender: "llm", text: currentText },
                    ],
                  }
                : c
            )
          );
        }, i * 200); // ⏳ slower streaming (200ms per line)
      });
    } catch (err) {
      setChats((prev) =>
        prev.map((c) =>
          c.id === activeChat
            ? {
                ...c,
                messages: [
                  ...c.messages,
                  { sender: "llm", text: "⚠️ Something went wrong. Try again." },
                ],
              }
            : c
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = (code) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleNewChat = () => {
    const newChat = { id: Date.now(), messages: [] };
    setChats((prev) => [...prev, newChat]);
    setActiveChat(newChat.id);
  };

  const renderers = {
    code({ inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || "");
      const codeText = String(children).replace(/\n$/, "");
      return !inline && match ? (
        <div className="code-block">
          <button className="copy-btn" onClick={() => handleCopy(codeText)}>
            {copied ? "Copied!" : "Copy"}
          </button>
          <SyntaxHighlighter
            style={oneLight}
            language={match[1]}
            PreTag="div"
            {...props}
          >
            {codeText}
          </SyntaxHighlighter>
        </div>
      ) : (
        <code className={className}>{children}</code>
      );
    },
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <img src={logo} alt="Logo" className="sidebar-logo" />
          <h2 className="sidebar-title">Chat History</h2>
        </div>
        <button className="new-chat-btn" onClick={handleNewChat}>
          + New Chat
        </button>
        <div className="history-list">
          {chats.map((chat) => (
            <div
              key={chat.id}
              className={`history-item ${
                chat.id === activeChat ? "active" : ""
              }`}
              onClick={() => setActiveChat(chat.id)}
            >
              <span>
                {chat.messages[0]
                  ? chat.messages[0].text.slice(0, 40) + "..."
                  : "Untitled Chat"}
              </span>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="app-container">
        {/* Title Bar */}
        <header className="chat-header">
          <img src={logo} alt="Logo" className="chat-header-logo" />
          <h1 className="chat-title">ChatDPT</h1>
        </header>

        {/* Messages */}
        <div
          className={`chat-window ${
            currentChat?.messages.length === 0 ? "centered" : ""
          }`}
        >
          {currentChat?.messages.length === 0 ? (
            <div className="welcome-text">👋 Start a new conversation</div>
          ) : (
            <>
              {currentChat?.messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`chat-row ${
                    msg.sender === "user" ? "row-user" : "row-llm"
                  }`}
                >
                  <div
                    className={`chat-message ${
                      msg.sender === "user" ? "user" : "llm"
                    }`}
                  >
                    {msg.sender === "llm" ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={renderers}
                      >
                        {msg.text}
                      </ReactMarkdown>
                    ) : (
                      msg.text
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="chat-row row-llm">
                  <div className="chat-message llm">
                    <span className="dot-pulse"></span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <form onSubmit={handleSendMessage} className="chat-form">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="chat-input"
            placeholder="Ask anything..."
            disabled={isLoading}
            rows={1}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage(e);
              }
            }}
          ></textarea>
          <button type="submit" className="send-btn" disabled={isLoading}>
            ➤
          </button>
        </form>
      </div>
    </div>
  );
};

export default App;
