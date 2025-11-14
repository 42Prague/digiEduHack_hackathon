import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GraphSpec } from '../../models/graph-spec';

@Component({
	selector: 'app-chart-view',
	standalone: true,
	imports: [CommonModule],
	templateUrl: './chart-view.component.html',
	styleUrls: ['./chart-view.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class ChartViewComponent {
	// #region Public Properties
	@Input() public spec!: GraphSpec;
	// #endregion

	// #region Public Methods
	public isHistogram(): boolean {
		return this.spec?.type === 'histogram';
	}
	public isPie(): boolean {
		return this.spec?.type === 'pie';
	}
	public isLine(): boolean {
		return this.spec?.type === 'line';
	}

	// Histogram helpers
	public histogramBars(): { label: string; value: number }[] {
		if (this.spec?.type !== 'histogram') return [];
		const xs = this.spec.x_values || [];
		const ys = this.spec.y_values || [];
		const n = Math.min(xs.length, ys.length);
		const arr: { label: string; value: number }[] = [];
		for (let i = 0; i < n; i++) arr.push({ label: xs[i], value: ys[i] });
		return arr;
	}
	public histogramMax(): number {
		const bars = this.histogramBars();
		return bars.length ? Math.max(...bars.map(b => b.value)) : 1;
	}
	public histogramCount(): number {
		return this.histogramBars().length;
	}
	public barWidth(): number {
		const n = this.histogramCount();
		return n > 0 ? (296 / n) - 12 : 0;
	}
	public barX(index: number): number {
		const n = this.histogramCount();
		return n > 0 ? (index * (296 / n)) + 6 : 0;
	}
	public barHeight(value: number): number {
		const max = Math.max(1, this.histogramMax());
		const scaled = (value / max) * (144 - 24);
		return Math.max(2, scaled);
	}
	public barColor(index: number): string {
		const palette = ['#2563eb', '#16a34a', '#f59e0b', '#ef4444', '#7c3aed', '#0891b2', '#d946ef'];
		return palette[index % palette.length];
	}
	public histogramXTicks(): { label: string; x: number }[] {
		return this.histogramBars().map((b, i) => ({
			label: b.label,
			x: this.barX(i) + this.barWidth() / 2
		}));
	}
	public histogramYTicks(): { value: number; y: number }[] {
		const max = Math.max(1, this.histogramMax());
		const steps = 4;
		const ticks: { value: number; y: number }[] = [];
		for (let i = 0; i <= steps; i++) {
			const v = (max / steps) * i;
			const y = 144 - (v / max) * (144 - 24);
			ticks.push({ value: Math.round(v), y });
		}
		return ticks;
	}

	// Pie helpers
	public pieSegments(): { label: string; value: number; length: number; offset: number; color: string }[] {
		if (this.spec?.type !== 'pie') return [];
		const labels = this.spec.labels || [];
		const values = this.spec.values || [];
		const total = values.reduce((a, b) => a + (isFinite(b) ? Math.max(0, b) : 0), 0) || 1;
		const circ = 2 * Math.PI * 48;
		let acc = 0;
		const palette = ['#2563eb', '#16a34a', '#f59e0b', '#ef4444', '#7c3aed', '#0891b2', '#d946ef'];
		return values.map((v, i) => {
			const len = circ * (Math.max(0, v) / total);
			const seg = { label: labels[i] || `S${i+1}`, value: v, length: len, offset: acc, color: palette[i % palette.length] };
			acc += len;
			return seg;
		});
	}

	// Line helpers
	public lineAllValues(): number[] {
		if (this.spec?.type !== 'line') return [];
		const series = this.spec.y_series || [];
		return series.flatMap(s => s.values || []);
	}
	public lineMin(): number {
		const vals = this.lineAllValues();
		return vals.length ? Math.min(...vals) : 0;
	}
	public lineMax(): number {
		const vals = this.lineAllValues();
		return vals.length ? Math.max(...vals) : 1;
	}
	public linePaths(): { name: string; d: string; color: string }[] {
		if (this.spec?.type !== 'line') return [];
		const width = 296;
		const height = 144;
		const padding = 8;
		const series = this.spec.y_series || [];
		const xCount = Math.max(...series.map(s => (s.values || []).length), 1);
		const min = this.lineMin();
		const max = this.lineMax();
		const span = Math.max(1e-9, max - min);
		const dx = (width - 2 * padding) / Math.max(1, xCount - 1);
		const palette = ['#2563eb', '#16a34a', '#f59e0b', '#ef4444', '#7c3aed', '#0891b2', '#d946ef'];

		return series.map((s, idx) => {
			const vs = s.values || [];
			const parts: string[] = [];
			for (let i = 0; i < vs.length; i++) {
				const x = padding + i * dx;
				const y = height - padding - ((vs[i] - min) / span) * (height - 2 * padding);
				parts.push(`${i === 0 ? 'M' : 'L'}${x},${y}`);
			}
			return { name: s.name || `Series ${idx+1}`, d: parts.join(' '), color: palette[idx % palette.length] };
		});
	}
	public lineXTicks(): { label: string; x: number }[] {
		if (this.spec?.type !== 'line') return [];
		const width = 296;
		const height = 144;
		const padding = 8;
		const labels = this.spec.x_values || [];
		const series = this.spec.y_series || [];
		const xCount = Math.max(...series.map(s => (s.values || []).length), labels.length, 1);
		const dx = (width - 2 * padding) / Math.max(1, xCount - 1);
		const maxTicks = 6;
		const step = Math.max(1, Math.ceil(xCount / maxTicks));
		const ticks: { label: string; x: number }[] = [];
		for (let i = 0; i < xCount; i += step) {
			const label = labels[i] ?? String(i + 1);
			ticks.push({ label, x: padding + i * dx });
		}
		return ticks;
	}
	public lineYTicks(): { value: number; y: number }[] {
		if (this.spec?.type !== 'line') return [];
		const height = 144;
		const padding = 8;
		const min = this.lineMin();
		const max = this.lineMax();
		const span = Math.max(1e-9, max - min);
		const steps = 4;
		const ticks: { value: number; y: number }[] = [];
		for (let i = 0; i <= steps; i++) {
			const v = min + (span / steps) * i;
			const y = height - padding - ((v - min) / span) * (height - 2 * padding);
			ticks.push({ value: Math.round(v), y });
		}
		return ticks;
	}
	// #endregion
}


