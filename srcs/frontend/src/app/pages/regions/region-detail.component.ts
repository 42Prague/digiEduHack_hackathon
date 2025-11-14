import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { RegionService } from '../../services/region.service';
import { Region } from '../../models/region';
import { AuthService } from '../../core/auth.service';
import { AccessLevel } from '../../models/access-level';
import { TranslateModule } from '@ngx-translate/core';

@Component({
	selector: 'app-region-detail',
	standalone: true,
	imports: [CommonModule, RouterLink, ReactiveFormsModule, TranslateModule],
	templateUrl: './region-detail.component.html',
	styleUrls: ['./region-detail.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class RegionDetailComponent implements OnInit {
	// #region Public Properties
	public region?: Region;
	public isLoading: boolean = true;
	public error?: string;
	public isEditing: boolean = false;
	public form?: FormGroup;
	public isSaving: boolean = false;
	// #endregion

	// #region Private Properties
	private readonly route: ActivatedRoute = inject(ActivatedRoute);
	private readonly regionService: RegionService = inject(RegionService);
	private readonly auth: AuthService = inject(AuthService);
	private readonly fb: FormBuilder = inject(FormBuilder);
	// #endregion

	// #region Public Methods
	public ngOnInit(): void {
		const id = this.route.snapshot.paramMap.get('id') as string;
		this.regionService.getById(id).subscribe({
			next: (r: Region | undefined) => {
				this.region = r;
				this.isLoading = false;
				if (!r) {
					this.error = 'Region not found';
				} else {
					this.buildForm(r);
				}
			},
			error: () => {
				this.error = 'Failed to load region';
				this.isLoading = false;
			}
		});
	}
	public isGlobal(): boolean {
		return this.auth.currentUser()?.accessLevel === AccessLevel.Global;
	}
	public viewAsRegion(): void {
		if (!this.region || !this.isGlobal()) return;
		this.auth.enterViewAsRegion(this.region.id);
	}
	public enableEditing(): void {
		if (!this.region) return;
		this.isEditing = true;
	}
	public cancelEditing(): void {
		if (!this.region) return;
		this.isEditing = false;
		this.buildForm(this.region);
	}
	public save(): void {
		if (!this.region || !this.form || this.form.invalid) return;
		this.isSaving = true;
		const values = this.form.value as Partial<Region>;
		this.regionService.update(this.region.id, values).subscribe({
			next: (updated: Region | undefined) => {
				if (updated) {
					this.region = { ...updated };
					this.isEditing = false;
				} else {
					this.error = 'Failed to save changes';
				}
				this.isSaving = false;
			},
			error: () => {
				this.error = 'Failed to save changes';
				this.isSaving = false;
			}
		});
	}
	// #endregion

	// #region Private Methods
	private buildForm(r: Region): void {
		this.form = this.fb.group({
			name: [r.name, [Validators.required, Validators.maxLength(120)]],
			address: [r.address, [Validators.required, Validators.maxLength(160)]],
			contactEmail: [r.contactEmail ?? '', [Validators.email, Validators.maxLength(160)]],
			contactPhone: [r.contactPhone ?? '', [Validators.maxLength(40)]],
		});
	}
	// #endregion
}

