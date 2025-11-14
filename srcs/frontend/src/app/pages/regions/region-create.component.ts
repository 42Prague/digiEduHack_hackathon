import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { RegionService } from '../../services/region.service';
import { Region } from '../../models/region';
import { TranslateModule } from '@ngx-translate/core';

@Component({
	selector: 'app-region-create',
	standalone: true,
	imports: [CommonModule, FormsModule, RouterLink, TranslateModule],
	templateUrl: './region-create.component.html',
	styleUrls: ['./region-create.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class RegionCreateComponent {
	// #region Public Properties
	public name: string = '';
	public address: string = '';
	public contactEmail?: string;
	public contactPhone?: string;
	public isSaving: boolean = false;
	public error?: string;
	// #endregion

	// #region Private Properties
	private readonly regionService: RegionService = inject(RegionService);
	private readonly router: Router = inject(Router);
	// #endregion

	// #region Public Methods
	public create(): void {
		if (!this.name.trim() || !this.address.trim() || this.isSaving) {
			return;
		}
		this.isSaving = true;
		this.regionService.create({
			name: this.name.trim(),
			address: this.address.trim(),
			contactEmail: this.contactEmail?.trim() || undefined,
			contactPhone: this.contactPhone?.trim() || undefined
		}).subscribe({
			next: () => {
				this.isSaving = false;
				void this.router.navigate(['/regions']);
			},
			error: () => {
				this.error = 'Failed to create region';
				// Best-effort console visibility for debugging
				// eslint-disable-next-line no-console
				console.error('Region creation failed');
				this.isSaving = false;
			}
		});
	}
	// #endregion
}


