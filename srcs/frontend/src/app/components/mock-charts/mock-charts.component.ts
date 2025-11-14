import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';

@Component({
	selector: 'app-mock-charts',
	standalone: true,
	imports: [CommonModule, FormsModule, TranslateModule],
	templateUrl: './mock-charts.component.html',
	styleUrls: ['./mock-charts.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class MockChartsComponent {
	// #region Public Properties
	@Input() public context: 'global' | 'region' | 'school' = 'global';
	public range: '7d' | '30d' | '12mo' = '30d';
	// #endregion

	// #region Public Methods
	public onRangeChange(next: '7d' | '30d' | '12mo'): void {
		this.range = next;
	}
	public areaPath(): string {
		const points = this.generateSeries();
		// simple path builder
		const width = 300;
		const height = 120;
		const max = Math.max(...points);
		const min = Math.min(...points);
		const span = Math.max(1, max - min);
		const dx = width / (points.length - 1);
		const coords = points.map((v, i) => {
			const x = i * dx;
			const y = height - ((v - min) / span) * height;
			return `${x},${y}`;
		});
		return `M0,${height} L${coords.join(' L ')} L${width},${height} Z`;
	}
	public bars(): number[] {
		return this.generateSeries();
	}
	public donutValue(): number {
		// a mock KPI in percent
		const arr = this.generateSeries();
		const last = arr[arr.length - 1] || 50;
		return Math.round(50 + (last % 40));
	}
	// #endregion

	// #region Private Methods
	private generateSeries(): number[] {
		const seeds: Record<'7d' | '30d' | '12mo', number> = { '7d': 8, '30d': 16, '12mo': 12 };
		const len = seeds[this.range];
		const base = this.hashToNumber(this.context) % 50;
		const series: number[] = [];
		let v = 40 + base;
		for (let i = 0; i < len; i++) {
			// deterministic pseudo-variation
			v = 0.8 * v + (13 * ((i + base) % 7)) + (this.range === '12mo' ? 5 : 0);
			series.push(Math.max(10, Math.min(100, Math.round(v % 100))));
		}
		return series;
	}
	private hashToNumber(input: string): number {
		let h = 0;
		for (let i = 0; i < input.length; i++) {
			h = (h << 5) - h + input.charCodeAt(i);
			h |= 0;
		}
		return Math.abs(h);
	}
	// #endregion
}


