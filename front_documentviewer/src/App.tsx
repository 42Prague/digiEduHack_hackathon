import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from './components/ui/select';
import { BarChart3, Map, Database, MessageSquare, Send } from 'lucide-react';

export default function App() {
  const [chatMessage, setChatMessage] = useState('');
  const [messages, setMessages] = useState([]); // chat bubbles
  const [region, setRegion] = useState('prague');

  const handleSendMessage = async () => {
    if (!chatMessage.trim()) return;

    const userMessage = {
      role: 'user',
      text: chatMessage
    };

    setMessages(prev => [...prev, userMessage]);

    const payload = {
      query: chatMessage,
      regions: [region],
      top_k: 2
    };

    setChatMessage('');

    try {
      const res = await fetch('http://127.0.0.1:5000/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      const botMessage = {
        role: 'assistant',
        text: data.answer || 'No response received.'
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      const errorMessage = {
        role: 'assistant',
        text: 'Error reaching backend API.'
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex flex-col">
        {/* Top Metric Cards */}
        <div className="grid grid-cols-4 gap-0 border-b">
          <Card className="rounded-none border-r border-t-0 border-l-0 border-b-0">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2">
                <Database className="w-5 h-5 text-blue-600" />
                Total Records
              </CardTitle>
            </CardHeader>
            <CardContent>
            </CardContent>
          </Card>

          <Card className="rounded-none border-r border-t-0 border-l-0 border-b-0">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2">
                <Map className="w-5 h-5 text-green-600" />
                Map Views
              </CardTitle>
            </CardHeader>
            <CardContent>

            </CardContent>
          </Card>

          <Card className="rounded-none border-r border-t-0 border-l-0 border-b-0">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-purple-600" />
                Chat Sessions
              </CardTitle>
            </CardHeader>
            <CardContent>

            </CardContent>
          </Card>

          <Card className="rounded-none border-t-0 border-l-0 border-b-0 border-r-0">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-orange-600" />
                Raw Data
              </CardTitle>
            </CardHeader>
            <CardContent>

            </CardContent>
          </Card>
        </div>

        {/* Middle - Chat Bubbles */}
        <div className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-4xl mx-auto flex flex-col gap-4">
            {messages.map((msg, idx) => (
                <div
                    key={idx}
                    className={`p-4 rounded-2xl shadow-md max-w-xl whitespace-pre-wrap text-lg font-medium ${
                        msg.role === 'user'
                            ? 'bg-blue-100 self-end'
                            : 'bg-slate-200 self-start'
                    }`}
                >
                  {msg.text}
                </div>
            ))}
          </div>
        </div>

        {/* Bottom Chat + Region Dropdown */}
        <div className="border-t bg-white p-6">
          <div className="max-w-4xl mx-auto flex flex-col gap-4">
            <div className="flex items-center gap-4">
              <Select value={region} onValueChange={setRegion}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Select region" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="prague">Prague</SelectItem>
                  <SelectItem value="brno">Brno</SelectItem>
                  <SelectItem value="ostrava">Ostrava</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-3 items-center">
              <Input
                  placeholder="Chat with AI about your data..."
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') handleSendMessage();
                  }}
                  className="flex-1"
              />
              <Button onClick={handleSendMessage} className="flex items-center gap-2">
                <Send className="w-4 h-4" />
                Send
              </Button>
            </div>
          </div>
        </div>
      </div>
  );
}
