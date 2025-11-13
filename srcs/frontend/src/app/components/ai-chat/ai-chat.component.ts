import { ChangeDetectionStrategy, Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { AgentService, AnalysisResponse } from '../../services/agent.service';

interface ChatMessage {
	role: 'user' | 'assistant';
	text: string;
	timestamp: Date;
}

@Component({
	selector: 'app-ai-chat',
	standalone: true,
	imports: [CommonModule, FormsModule, HttpClientModule],
	templateUrl: './ai-chat.component.html',
	styleUrls: ['./ai-chat.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class AiChatComponent {
	// #region Public Properties
	public messages: ChatMessage[] = [
		{ role: 'assistant', text: 'Hi! I am your AI BI Agent. Ask me about trends, KPIs, or comparisons.', timestamp: new Date() }
	];
	public draft: string = '';
	public isThinking: boolean = false;
	// #endregion

	// #region Private Properties
	private sessionId: string | null = null;
	// #endregion

	constructor(private readonly agent: AgentService) {}

	// #region Public Methods
	public send(): void {
		const text = this.draft.trim();
		if (!text || this.isThinking) return;
		this.messages = [...this.messages, { role: 'user', text, timestamp: new Date() }];
		this.draft = '';
		this.isThinking = true;
		this.agent.analyze({
			query: text,
			language: 'en',
			session_id: this.sessionId
		}).subscribe({
			next: (res: AnalysisResponse) => {
				this.sessionId = res.session_id;
				this.messages = [...this.messages, { role: 'assistant', text: res.answer, timestamp: new Date() }];
				this.isThinking = false;
			},
			error: () => {
				this.messages = [...this.messages, { role: 'assistant', text: 'Sorry, something went wrong. Please try again.', timestamp: new Date() }];
				this.isThinking = false;
			}
		});
	}
	// #endregion

	// #region Private Methods
	// (no private methods currently)
	// #endregion
}


