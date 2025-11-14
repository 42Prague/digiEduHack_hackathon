import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
	name: 'markdown',
	standalone: true
})
export class MarkdownPipe implements PipeTransform {
	public transform(input: string | null | undefined): string {
		if (!input) return '';
		let text = input;

		// Escape HTML
		text = text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;');

		// Code blocks ```lang? ... ```
		text = text.replace(/```(\w+)?\s*([\s\S]*?)```/g, (_m, lang: string, code: string) => {
			const c = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
			const klass = lang ? ` class="lang-${lang}"` : '';
			return `<pre><code>${c}</code></pre>`;
		});

		// Inline code `code`
		text = text.replace(/`([^`]+?)`/g, (_m, code: string) => `<code>${code}</code>`);

		// Bold **text**
		text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

		// Italic *text* or _text_
		text = text.replace(/(^|[\s(])\*(?!\*)([^*]+?)\*(?=[\s).,;:!?]|$)/g, '$1<em>$2</em>');
		text = text.replace(/(^|[\s(])_(.+?)_(?=[\s).,;:!?]|$)/g, '$1<em>$2</em>');

		// Links [text](https://...)
		text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

		// Simple lists, headings, hr, tables, paragraphs
		const lines = text.split(/\r?\n/);
		const html: string[] = [];
		let inUl = false;
		for (let i = 0; i < lines.length; i++) {
			const line = lines[i];
			// headings
			const h = line.match(/^\s*(#{1,6})\s+(.*)$/);
			if (h) {
				if (inUl) { inUl = false; html.push('</ul>'); }
				const level = Math.min(6, h[1].length);
				html.push(`<h${level}>${h[2]}</h${level}>`);
				continue;
			}
			// horizontal rule
			if (/^\s*-{3,}\s*$/.test(line)) {
				if (inUl) { inUl = false; html.push('</ul>'); }
				html.push('<hr/>');
				continue;
			}
			// tables (GitHub-style): header | header
			// separator: | --- | :---: | ---:
			const isTableHeader = /^\s*\|?.*\|.*\|?\s*$/.test(line) && (i + 1 < lines.length) && /^\s*\|?\s*[:\-| ]+\s*\|?\s*$/.test(lines[i + 1]);
			if (isTableHeader) {
				if (inUl) { inUl = false; html.push('</ul>'); }
				// parse header
				const headerCells = line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim());
				// parse alignment
				const alignLine = lines[i + 1].trim().replace(/^\|/, '').replace(/\|$/, '');
				const alignTokens = alignLine.split('|').map(c => c.trim());
				const aligns = alignTokens.map(tok => {
					const left = tok.startsWith(':');
					const right = tok.endsWith(':');
					if (left && right) return 'center';
					if (right) return 'right';
					if (left) return 'left';
					return 'left';
				});
				i += 2; // skip header + separator
				const rows: string[][] = [];
				while (i < lines.length) {
					const rowLine = lines[i];
					if (!/^\s*\|?.*\|.*\|?\s*$/.test(rowLine)) { i--; break; }
					const cells = rowLine.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim());
					if (cells.length === 1 && cells[0] === '') { i--; break; }
					rows.push(cells);
					i++;
				}
				// build table HTML
				html.push('<table class="md-table"><thead><tr>');
				for (let ci = 0; ci < headerCells.length; ci++) {
					const a = aligns[ci] || 'left';
					html.push(`<th style="text-align:${a}">${headerCells[ci]}</th>`);
				}
				html.push('</tr></thead><tbody>');
				for (const r of rows) {
					html.push('<tr>');
					for (let ci = 0; ci < headerCells.length; ci++) {
						const a = aligns[ci] || 'left';
						const v = (r[ci] ?? '').trim();
						html.push(`<td style="text-align:${a}">${v}</td>`);
					}
					html.push('</tr>');
				}
				html.push('</tbody></table>');
				continue;
			}
			const li = line.match(/^\s*[-*]\s+(.*)$/);
			if (li) {
				if (!inUl) {
					inUl = true;
					html.push('<ul>');
				}
				html.push(`<li>${li[1]}</li>`);
			} else {
				if (inUl) {
					inUl = false;
					html.push('</ul>');
				}
				if (line.trim().length === 0) {
					html.push('<br/>');
				} else {
					html.push(`<p>${line}</p>`);
				}
			}
		}
		if (inUl) html.push('</ul>');

		return html.join('');
	}
}


