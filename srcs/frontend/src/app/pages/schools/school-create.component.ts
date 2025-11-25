import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { SchoolService } from '../../services/school.service';
import { RegionService } from '../../services/region.service';
import { School } from '../../models/school';
import { Region } from '../../models/region';
import { AuthService } from '../../core/auth.service';
import { AccessLevel } from '../../models/access-level';
import { TranslateModule } from '@ngx-translate/core';

@Component({
	selector: 'app-school-create',
	standalone: true,
	imports: [CommonModule, FormsModule, RouterLink, TranslateModule],
	templateUrl: './school-create.component.html',
	styleUrls: ['./school-create.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class SchoolCreateComponent implements OnInit {
	// #region Public Properties
	public name: string = '';
	public address: string = '';
	public headmasterName?: string;
	public contactEmail?: string;
	public contactPhone?: string;
	public regionId?: string;
	public regions: Region[] = [];
	public allowRegionSelect: boolean = false;
	public isSaving: boolean = false;
	public isLoadingRegions: boolean = true;
	public error?: string;
	// #endregion

	// #region Private Properties
	private readonly schoolService: SchoolService = inject(SchoolService);
	private readonly regionService: RegionService = inject(RegionService);
	private readonly auth: AuthService = inject(AuthService);
	private readonly router: Router = inject(Router);
	// #endregion

	// #region Public Methods
	public ngOnInit(): void {
		const current = this.auth.currentUser();
		const level = current?.accessLevel;
		if (level === AccessLevel.Region && current?.regionId) {
			this.regionId = current.regionId;
			this.allowRegionSelect = false;
			this.isLoadingRegions = false;
		} else {
			this.allowRegionSelect = true;
			this.regionService.list().subscribe({
				next: (items: Region[]) => {
					this.regions = items;
					this.isLoadingRegions = false;
				},
				error: () => {
					this.error = 'Failed to load regions';
					this.isLoadingRegions = false;
				}
			});
		}
	}

	public create(): void {
		if (!this.name.trim() || !this.address.trim() || !this.regionId || this.isSaving) {
			return;
		}
		this.isSaving = true;
		this.schoolService.create({
			name: this.name.trim(),
			address: this.address.trim(),
			headmasterName: this.headmasterName?.trim() || undefined,
			contactEmail: this.contactEmail?.trim() || undefined,
			contactPhone: this.contactPhone?.trim() || undefined,
			regionId: this.regionId
		}).subscribe({
			next: (created: School) => {
				this.isSaving = false;
				void this.router.navigate(['/schools', created.id]);
			},
			error: () => {
				this.error = 'Failed to create school';
				this.isSaving = false;
			}
		});
	}
	// #endregion
}


