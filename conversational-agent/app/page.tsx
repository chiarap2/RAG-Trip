"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Send, Bot, User } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"

interface Message {
  id: string
  content: string
  sender: "user" | "agent"
  timestamp: Date
  mapHtml?: string
}

export default function ConversationalAgent() {
  const [expandedMessages, setExpandedMessages] = useState<{ [id: string]: boolean }>({});
  const MAX_LENGTH = 300;

  const isTruncated = (text: string) => text.length > MAX_LENGTH;
  const getDisplayText = (text: string, expanded: boolean) =>
    expanded || !isTruncated(text) ? text : text.slice(0, MAX_LENGTH) + '...';

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: "Hi there! 👋 Welcome to RAGTrip, your intelligent travel assistant. I’ll help you plan a personalized route, suggest interesting places along the way, and answer your questions with reliable, real-world info. Ready to start your journey?",
      sender: "agent",
      timestamp: new Date(),
    },
  ])
  const [inputValue, setInputValue] = useState("")
  const [isRag, setIsRag] = useState(true);
  const [isTyping, setIsTyping] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]")
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now().toString(),
      content: inputValue,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          query: inputValue,
          rag: isRag  // Include the RAG toggle state in the request
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const agentMessage = {
        id: Date.now().toString(),
        content: data.response,
        mapHtml: data.map_html,  // Store the map HTML
        sender: "agent",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsTyping(false);
    }
  };


  // const handleSendMessage = () => {
  //   if (!inputValue.trim()) return

  //   const userMessage: Message = {
  //     id: Date.now().toString(),
  //     content: inputValue,
  //     sender: "user",
  //     timestamp: new Date(),
  //   }

  //   setMessages((prev) => [...prev, userMessage])
  //   simulateAgentResponse(inputValue)
  //   setInputValue("")
  // }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  }
  const scrollAnchorRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (scrollAnchorRef.current) {
      scrollAnchorRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-5xl mx-auto">
        <Card className="w-full max-w-5xl h-[90vh] flex flex-col overflow-hidden relative">
          <CardHeader className="border-b">
            <CardTitle className="flex items-center gap-2">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-blue-500 text-white">
                  <Bot className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              RAGTrip
              <div className="ml-auto flex items-center gap-2">
                <span className="text-sm text-muted-foreground">{"RAG"}</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={isRag}
                    onChange={() => {
                      setIsRag((prev) => {
                        const newValue = !prev;
                        setMessages([
                          {
                            id: "1",
                            content: `Hi there! 👋 Welcome to RAGTrip, your intelligent travel assistant.
                                    I’ll help you plan a personalized route, suggest interesting places along the way, and answer your questions with reliable, real-world info. 
                                    Ready to start your journey?`,
                            sender: "agent",
                            timestamp: new Date(),
                          }
                        ]);
                        return newValue;
                      });
                    }}
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:bg-green-500 transition-colors"></div>
                  <div className="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow-md transform peer-checked:translate-x-5 transition-transform"></div>
                </label>
              </div>
            </CardTitle>
          </CardHeader>



          <CardContent className="flex-1 overflow-y-auto p-4" ref={scrollAreaRef}>
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex items-start gap-3 ${message.sender === "user" ? "flex-row-reverse" : ""}`}
                  >
                    <Avatar className="h-8 w-8 flex-shrink-0">
                      {message.sender === "user" ? (
                        <AvatarFallback className="bg-gray-500 text-white">
                          <User className="h-4 w-4" />
                        </AvatarFallback>
                      ) : (
                        <AvatarFallback className="bg-blue-500 text-white">
                          <Bot className="h-4 w-4" />
                        </AvatarFallback>
                      )}
                    </Avatar>

                    <div
                      className={`flex flex-col max-w-[80%] ${message.sender === "user" ? "items-end" : "items-start"}`}
                    >
                      <div
                        className={`rounded-lg px-3 py-2 text-sm ${
                          message.sender === "user" ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-900"
                        }`}
                      >
                        <div>
                          {getDisplayText(message.content, expandedMessages[message.id])}
                          {isTruncated(message.content) && (
                            <button
                              className="text-blue-500 text-xs ml-2"
                              onClick={() =>
                                setExpandedMessages((prev) => ({
                                  ...prev,
                                  [message.id]: !prev[message.id],
                                }))
                              }
                            >
                              {expandedMessages[message.id] ? 'Show less' : 'Show more'}
                            </button>
                          )}
                        </div>
                      </div>
                      <span className="text-xs text-muted-foreground mt-1">{formatTime(message.timestamp)}</span>
                      {(message.mapHtml ?? '').trim() && (
                        <div
                          className="mt-2 w-full overflow-hidden rounded-lg border shadow"
                          dangerouslySetInnerHTML={{ __html: message.mapHtml }}
                        />
                      )}
                    </div>
                  </div>
                ))}


                <div ref={scrollAnchorRef} />
                

                {isTyping && (
                  <div className="flex items-start gap-3">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="bg-blue-500 text-white">
                        <Bot className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                    <div className="bg-gray-100 rounded-lg px-3 py-2">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "0.1s" }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "0.2s" }}
                        ></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
           
          </CardContent>

          <CardFooter className="border-t p-4 bg-white sticky bottom-0 z-10">
            <div className="flex w-full gap-2">
              <Input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="flex-1"
                disabled={isTyping}
              />
              <Button onClick={handleSendMessage} disabled={!inputValue.trim() || isTyping} size="icon">
                <Send className="h-4 w-4" />
                <span className="sr-only">Send message</span>
              </Button>
            </div>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
