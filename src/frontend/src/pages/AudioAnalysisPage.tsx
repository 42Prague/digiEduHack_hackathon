import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { 
  Play, 
  Pause,
  Volume2,
  FileAudio,
  MessageSquare,
  TrendingUp,
  Target,
  Sparkles
} from 'lucide-react';

const audioFiles = [
  { id: 1, name: 'Interview - Teacher Workshop Nov', school: 'Gymnasium Brandýs', duration: '12:34', date: '2025-11-10' },
  { id: 2, name: 'Student Focus Group Session', school: 'ZŠ Kolín', duration: '18:42', date: '2025-11-08' },
  { id: 3, name: 'Principal Discussion Q4', school: 'ZŠ Černošice', duration: '15:28', date: '2025-11-05' },
];

const themes = [
  { label: 'Student Engagement', confidence: 92 },
  { label: 'Teaching Methods', confidence: 87 },
  { label: 'Classroom Environment', confidence: 84 },
  { label: 'Parental Involvement', confidence: 78 },
  { label: 'Resource Availability', confidence: 73 },
];

export function AudioAnalysisPage() {
  const [selectedAudio, setSelectedAudio] = useState(audioFiles[0].id.toString());
  const [isPlaying, setIsPlaying] = useState(false);

  const currentAudio = audioFiles.find(a => a.id.toString() === selectedAudio);

  return (
    <div className="space-y-6">
      <div>
        <h1>Audio & Transcript Analysis</h1>
        <p className="text-slate-600 mt-1">Analyze audio recordings and extract insights</p>
      </div>

      {/* Audio Selection */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Select value={selectedAudio} onValueChange={setSelectedAudio}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {audioFiles.map((audio) => (
                    <SelectItem key={audio.id} value={audio.id.toString()}>
                      {audio.name} - {audio.school}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline">
              <FileAudio className="w-4 h-4 mr-2" />
              Upload New Audio
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Audio Player */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{currentAudio?.name}</CardTitle>
              <p className="text-sm text-slate-600 mt-1">
                {currentAudio?.school} • {currentAudio?.date}
              </p>
            </div>
            <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
              Processed
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Waveform Visualization */}
          <div className="bg-slate-50 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Volume2 className="w-4 h-4 text-slate-600" />
              <span className="text-sm text-slate-600">Audio Waveform</span>
            </div>
            <div className="h-24 flex items-end justify-between gap-1">
              {Array.from({ length: 80 }).map((_, i) => {
                const height = Math.sin(i / 5) * 30 + Math.random() * 40 + 20;
                return (
                  <div
                    key={i}
                    className="flex-1 bg-blue-400 rounded-t"
                    style={{ height: `${height}%` }}
                  />
                );
              })}
            </div>
          </div>

          {/* Player Controls */}
          <div className="flex items-center gap-4">
            <Button
              size="icon"
              onClick={() => setIsPlaying(!isPlaying)}
            >
              {isPlaying ? (
                <Pause className="w-4 h-4" />
              ) : (
                <Play className="w-4 h-4" />
              )}
            </Button>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs text-slate-600">2:34</span>
                <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-600 rounded-full" style={{ width: '20%' }}></div>
                </div>
                <span className="text-xs text-slate-600">{currentAudio?.duration}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Transcripts & Analysis */}
      <Tabs defaultValue="transcripts" className="space-y-6">
        <TabsList>
          <TabsTrigger value="transcripts">Transcripts</TabsTrigger>
          <TabsTrigger value="themes">Key Themes</TabsTrigger>
          <TabsTrigger value="sentiment">Sentiment Analysis</TabsTrigger>
          <TabsTrigger value="comparison">Compare</TabsTrigger>
        </TabsList>

        <TabsContent value="transcripts" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Original Transcript</CardTitle>
                <p className="text-sm text-slate-600">Raw automated transcription</p>
              </CardHeader>
              <CardContent>
                <div className="bg-slate-50 rounded-lg p-4 max-h-96 overflow-y-auto space-y-3">
                  <p className="text-sm">
                    <span className="text-slate-500">[00:00]</span> um hello everyone thank you for uh joining today's workshop session um as we discussed in the previous meeting um we want to focus on improving student engagement especially in mathematics and sciences...
                  </p>
                  <p className="text-sm">
                    <span className="text-slate-500">[00:34]</span> so uh the main challenge we're facing is that students seem disconnected during lectures and um they're not really participating actively in class discussions which is concerning...
                  </p>
                  <p className="text-sm">
                    <span className="text-slate-500">[01:12]</span> one approach that has shown promise in other schools is the uh implementation of project-based learning where students work on real-world problems in small groups...
                  </p>
                  <p className="text-sm">
                    <span className="text-slate-500">[01:45]</span> we've also noticed that when we incorporate technology like um interactive simulations and educational games the engagement levels increase significantly...
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Cleaned Transcript</CardTitle>
                    <p className="text-sm text-slate-600">Processed and refined</p>
                  </div>
                  <Sparkles className="w-5 h-5 text-blue-600" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="bg-blue-50 rounded-lg p-4 max-h-96 overflow-y-auto space-y-3">
                  <p className="text-sm">
                    <span className="text-slate-500">[00:00]</span> Hello everyone, thank you for joining today's workshop session. As we discussed in the previous meeting, we want to focus on improving student engagement, especially in mathematics and sciences.
                  </p>
                  <p className="text-sm">
                    <span className="text-slate-500">[00:34]</span> The main challenge we're facing is that students seem disconnected during lectures and they're not really participating actively in class discussions, which is concerning.
                  </p>
                  <p className="text-sm">
                    <span className="text-slate-500">[01:12]</span> One approach that has shown promise in other schools is the implementation of project-based learning, where students work on real-world problems in small groups.
                  </p>
                  <p className="text-sm">
                    <span className="text-slate-500">[01:45]</span> We've also noticed that when we incorporate technology like interactive simulations and educational games, the engagement levels increase significantly.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="themes" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Extracted Themes</CardTitle>
                <p className="text-sm text-slate-600">Key topics identified with confidence scores</p>
              </CardHeader>
              <CardContent className="space-y-4">
                {themes.map((theme, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Badge variant="outline">{theme.label}</Badge>
                      <span className="text-sm">{theme.confidence}%</span>
                    </div>
                    <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-600 rounded-full transition-all"
                        style={{ width: `${theme.confidence}%` }}
                      />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Theme Tags</CardTitle>
                <p className="text-sm text-slate-600">Quick reference</p>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  <Badge>Student Engagement</Badge>
                  <Badge variant="outline">Teaching Methods</Badge>
                  <Badge variant="outline">Classroom Environment</Badge>
                  <Badge variant="outline">Technology Integration</Badge>
                  <Badge variant="outline">Project-Based Learning</Badge>
                  <Badge variant="outline">Active Learning</Badge>
                  <Badge variant="outline">Group Work</Badge>
                  <Badge variant="outline">Educational Games</Badge>
                  <Badge variant="outline">Mathematics</Badge>
                  <Badge variant="outline">Sciences</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="sentiment" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <TrendingUp className="w-10 h-10 text-green-600" />
                  </div>
                  <h3>Overall Sentiment</h3>
                  <p className="text-3xl mt-2 text-green-600">Positive</p>
                  <p className="text-sm text-slate-600 mt-2">82% confidence</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <MessageSquare className="w-10 h-10 text-blue-600" />
                  </div>
                  <h3>Engagement Level</h3>
                  <p className="text-3xl mt-2 text-blue-600">High</p>
                  <p className="text-sm text-slate-600 mt-2">Active discussion</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Target className="w-10 h-10 text-purple-600" />
                  </div>
                  <h3>Objective Achievement</h3>
                  <p className="text-3xl mt-2 text-purple-600">88%</p>
                  <p className="text-sm text-slate-600 mt-2">Goals met</p>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Sentiment Timeline</CardTitle>
              <p className="text-sm text-slate-600">How sentiment evolved during the conversation</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-4">
                  <span className="text-sm text-slate-500 w-16">0:00</span>
                  <div className="flex-1 h-8 bg-green-100 rounded flex items-center px-3">
                    <span className="text-sm text-green-700">Positive - Introduction and welcome</span>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-slate-500 w-16">2:15</span>
                  <div className="flex-1 h-8 bg-orange-100 rounded flex items-center px-3">
                    <span className="text-sm text-orange-700">Neutral - Discussing challenges</span>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-slate-500 w-16">5:30</span>
                  <div className="flex-1 h-8 bg-green-100 rounded flex items-center px-3">
                    <span className="text-sm text-green-700">Positive - Solutions and strategies</span>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-slate-500 w-16">9:45</span>
                  <div className="flex-1 h-8 bg-blue-100 rounded flex items-center px-3">
                    <span className="text-sm text-blue-700">Very Positive - Success stories and results</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="comparison" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Compare Transcripts</CardTitle>
              <p className="text-sm text-slate-600">Side-by-side analysis of two recordings</p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-6 mb-6">
                <Select defaultValue="1">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {audioFiles.map((audio) => (
                      <SelectItem key={audio.id} value={audio.id.toString()}>
                        {audio.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select defaultValue="2">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {audioFiles.map((audio) => (
                      <SelectItem key={audio.id} value={audio.id.toString()}>
                        {audio.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-3">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm mb-1">Sentiment</p>
                    <p className="text-green-600">Positive (82%)</p>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm mb-1">Key Themes</p>
                    <p>Student Engagement, Teaching Methods</p>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm mb-1">Objective Achievement</p>
                    <p className="text-purple-600">88%</p>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <p className="text-sm mb-1">Sentiment</p>
                    <p className="text-orange-600">Neutral (65%)</p>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <p className="text-sm mb-1">Key Themes</p>
                    <p>Resource Availability, Challenges</p>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <p className="text-sm mb-1">Objective Achievement</p>
                    <p className="text-purple-600">72%</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
