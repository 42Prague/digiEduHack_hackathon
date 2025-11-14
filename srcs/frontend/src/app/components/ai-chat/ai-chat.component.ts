import { ChangeDetectionStrategy, Component, ChangeDetectorRef, ElementRef, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { AgentService, AnalysisResponse } from '../../services/agent.service';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { ChartViewComponent } from '../chart-view/chart-view.component';
import { MarkdownPipe } from '../../core/markdown.pipe';
import { GraphSpec } from '../../models/graph-spec';

type MessagePart =
	| { kind: 'text'; text: string }
	| { kind: 'graph'; graph: GraphSpec };

interface ChatMessage {
	role: 'user' | 'assistant';
	timestamp: Date;
	parts: MessagePart[];
}

@Component({
	selector: 'app-ai-chat',
	standalone: true,
	imports: [CommonModule, FormsModule, HttpClientModule, TranslateModule, ChartViewComponent, MarkdownPipe],
	templateUrl: './ai-chat.component.html',
	styleUrls: ['./ai-chat.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class AiChatComponent {
	// #region Public Properties
	public messages: ChatMessage[] = [];
	public draft: string = '';
	public isThinking: boolean = false;
	public isFullscreen: boolean = false;
	// #endregion

	// #region Private Properties
	@ViewChild('chatWindow') private chatWindow?: ElementRef<HTMLDivElement>;
	private sessionId: string | null = null;
	private readonly translate: TranslateService = inject(TranslateService);
	private readonly cdr: ChangeDetectorRef = inject(ChangeDetectorRef);
	// #endregion

	constructor(private readonly agent: AgentService) {
		const greeting = this.translate.instant('ai.greeting');
		this.messages = [{ role: 'assistant', timestamp: new Date(), parts: [{ kind: 'text', text: greeting }] }];
	}

	// #region Public Methods
	public toggleFullscreen(): void {
		this.isFullscreen = !this.isFullscreen;
		this.cdr.markForCheck();
		setTimeout(() => this.scrollToBottom(), 0);
	}
	public exportMessagePdf(index: number): void {
		try {
			const el = document.getElementById(`msg-${index}`);
			if (!el) return;
			const clone = el.cloneNode(true) as HTMLElement;
			clone.querySelectorAll('.export-btn').forEach(n => n.parentElement?.removeChild(n));
			const html = clone.innerHTML;
			const win = window.open('', '_blank', 'width=900,height=1200');
			if (!win) return;
			const styles = `
				<style>
					* { box-sizing: border-box; }
					body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"; color: #0f172a; margin: 24px; }
					.bubble { border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px; }
					.text { white-space: normal; }
					.text pre { background: #0f172a; color: #e2e8f0; padding: 10px; border-radius: 8px; overflow: auto; }
					.text code { background: #f1f5f9; padding: 2px 4px; border-radius: 4px; }
					.plot-wrap { margin-top: 10px; border: 1px solid #e2e8f0; border-radius: 12px; padding: 8px; background: #f8fafc; }
					.chart-card { border: 1px solid #e2e8f0; border-radius: 12px; background: #fff; padding: 8px; }
					.chart-title { font-weight: 700; margin-bottom: 6px; }
					.legend { list-style: none; margin: 8px 0 0 0; padding: 0; font-size: 12px; color: #64748b; }
					.legend li { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
					.legend .swatch { width: 10px; height: 10px; border-radius: 2px; border: 1px solid rgba(0,0,0,0.06); display: inline-block; }
					table { width: 100%; border-collapse: collapse; margin: 8px 0; }
					th, td { border: 1px solid #e2e8f0; padding: 6px 8px; font-size: 13px; }
					thead th { background: #f8fafc; }
					.export-btn { display: none !important; }
					@page { size: A4; margin: 16mm; }
				</style>
			`;
			win.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>Message</title>${styles}</head><body><div class="bubble">${html}</div></body></html>`);
			win.document.close();
			win.focus();
			setTimeout(() => {
				try { win.print(); } catch {}
				setTimeout(() => { try { win.close(); } catch {} }, 300);
			}, 300);
		} catch {}
	}
	public send(): void {
		const text = this.draft.trim();
		if (!text || this.isThinking) return;
		this.messages = [...this.messages, { role: 'user', timestamp: new Date(), parts: [{ kind: 'text', text }] }];
		this.draft = '';
		this.isThinking = true;
		this.cdr.markForCheck();
		setTimeout(() => this.scrollToBottom(), 0);
		this.agent.analyze({
			query: text,
			language: (this.translate.currentLang || this.translate.getDefaultLang() || 'en').slice(0,2),
			session_id: this.sessionId
		}).subscribe({
			next: (res: AnalysisResponse) => {
				this.sessionId = res.session_id;
				const parts = this.extractParts(res.answer);
				this.messages = [...this.messages, { role: 'assistant', timestamp: new Date(), parts }];
				this.isThinking = false;
				this.cdr.markForCheck();
				setTimeout(() => this.scrollToBottom(), 0);
			},
			error: () => {
				const err = this.translate.instant('common.errorTryAgain');
				this.messages = [...this.messages, { role: 'assistant', timestamp: new Date(), parts: [{ kind: 'text', text: err }] }];
				this.isThinking = false;
				this.cdr.markForCheck();
				setTimeout(() => this.scrollToBottom(), 0);
			}
		});
	}
	// #endregion

	// #region Private Methods
	private extractParts(answer: string): MessagePart[] {
		const parts: MessagePart[] = [];
		let cursor = 0;
		const text = answer;
		while (cursor < text.length) {
			const slice = text.slice(cursor);
			const m1 = /<GRAPH>\s*([\s\S]*?)\s*<\/GRAPH>/i.exec(slice);
			const m2 = /```json\s*([\s\S]*?)```/i.exec(slice);
			const m3 = /(?:^|\n)\s*json\s*\n\s*({[\s\S]*?})/i.exec(slice);

			// pick earliest match
			const candidates = [m1, m2, m3].filter(Boolean) as RegExpExecArray[];
			if (candidates.length === 0) {
				const remaining = text.slice(cursor);
				if (remaining) parts.push({ kind: 'text', text: remaining });
				break;
			}
			let next = candidates[0];
			for (const m of candidates) {
				if (m.index < next.index) next = m;
			}
			const before = slice.slice(0, next.index);
			if (before) parts.push({ kind: 'text', text: before });
			const matched = next[0];
			const jsonBody = next[1];
			try {
				const g = JSON.parse(jsonBody) as GraphSpec;
				parts.push({ kind: 'graph', graph: g });
			} catch {
				// if JSON invalid, keep the raw matched as text
				parts.push({ kind: 'text', text: matched });
			}
			cursor += next.index + matched.length;
		}
		return parts;
	}
	private scrollToBottom(): void {
		try {
			const el = this.chatWindow?.nativeElement;
			if (!el) return;
			el.scrollTop = el.scrollHeight;
		} catch {}
	}
	// #endregion
}

