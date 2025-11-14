import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { RegionService } from '../../services/region.service';
import { Region } from '../../models/region';
import { TranslateModule } from '@ngx-translate/core';

@Component({
	selector: 'app-region-edit',
	standalone: true,
	imports: [CommonModule, FormsModule, RouterLink, TranslateModule],
	templateUrl: './region-edit.component.html',
	styleUrls: ['./region-edit.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class RegionEditComponent implements OnInit {
	// #region Public Properties
	public regionId!: string;
	public name: string = '';
	public address: string = '';
	public contactEmail?: string;
	public contactPhone?: string;
	public isSaving: boolean = false;
	public isLoading: boolean = true;
	public error?: string;
	// #endregion

	// #region Private Properties
	private readonly route: ActivatedRoute = inject(ActivatedRoute);
	private readonly router: Router = inject(Router);
	private readonly regionService: RegionService = inject(RegionService);
	// #endregion

	// #region Public Methods
	public ngOnInit(): void {
		this.regionId = this.route.snapshot.paramMap.get('id') as string;
		this.regionService.getById(this.regionId).subscribe({
			next: (r: Region | undefined) => {
				if (!r) {
					this.error = 'Region not found';
				} else {
					this.name = r.name;
					this.address = r.address;
					this.contactEmail = r.contactEmail;
					this.contactPhone = r.contactPhone;
				}
				this.isLoading = false;
			},
			error: () => {
				this.error = 'Failed to load region';
				this.isLoading = false;
			}
		});
	}

	public save(): void {
		if (!this.name.trim() || !this.address.trim() || this.isSaving) {
			return;
		}
		this.isSaving = true;
		this.regionService.update(this.regionId, {
			name: this.name.trim(),
			address: this.address.trim(),
			contactEmail: this.contactEmail?.trim() || undefined,
			contactPhone: this.contactPhone?.trim() || undefined
		}).subscribe({
			next: (updated: Region | undefined) => {
				this.isSaving = false;
				if (updated) {
					void this.router.navigate(['/regions', updated.id]);
				} else {
					this.error = 'Failed to update region';
				}
			},
			error: () => {
				this.error = 'Failed to update region';
				this.isSaving = false;
			}
		});
	}
	// #endregion
}


