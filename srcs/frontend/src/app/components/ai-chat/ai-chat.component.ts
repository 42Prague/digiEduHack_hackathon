import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { AgentService, AnalysisResponse } from '../../services/agent.service';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

interface ChatMessage {
	role: 'user' | 'assistant';
	text: string;
	timestamp: Date;
}

@Component({
	selector: 'app-ai-chat',
	standalone: true,
	imports: [CommonModule, FormsModule, HttpClientModule, TranslateModule],
	templateUrl: './ai-chat.component.html',
	styleUrls: ['./ai-chat.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class AiChatComponent {
	// #region Public Properties
	public messages: ChatMessage[] = [];
	public draft: string = '';
	public isThinking: boolean = false;
	// #endregion

	// #region Private Properties
	private sessionId: string | null = null;
	private readonly translate: TranslateService = inject(TranslateService);
	// #endregion

	constructor(private readonly agent: AgentService) {
		const greeting = this.translate.instant('ai.greeting');
		this.messages = [{ role: 'assistant', text: greeting, timestamp: new Date() }];
	}

	// #region Public Methods
	public send(): void {
		const text = this.draft.trim();
		if (!text || this.isThinking) return;
		this.messages = [...this.messages, { role: 'user', text, timestamp: new Date() }];
		this.draft = '';
		this.isThinking = true;
		this.agent.analyze({
			query: text,
			language: (this.translate.currentLang || this.translate.getDefaultLang() || 'en').slice(0,2),
			session_id: this.sessionId
		}).subscribe({
			next: (res: AnalysisResponse) => {
				this.sessionId = res.session_id;
				this.messages = [...this.messages, { role: 'assistant', text: res.answer, timestamp: new Date() }];
				this.isThinking = false;
			},
			error: () => {
				const err = this.translate.instant('common.errorTryAgain');
				this.messages = [...this.messages, { role: 'assistant', text: err, timestamp: new Date() }];
				this.isThinking = false;
			}
		});
	}
	// #endregion

	// #region Private Methods
	// (no private methods currently)
	// #endregion
}


