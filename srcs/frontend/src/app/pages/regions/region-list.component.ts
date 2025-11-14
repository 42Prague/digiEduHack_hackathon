import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { RegionService } from '../../services/region.service';
import { Region } from '../../models/region';
import { AuthService } from '../../core/auth.service';
import { AccessLevel } from '../../models/access-level';

@Component({
	selector: 'app-region-list',
	standalone: true,
	imports: [CommonModule, FormsModule, RouterLink, TranslateModule],
	templateUrl: './region-list.component.html',
	styleUrls: ['./region-list.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class RegionListComponent implements OnInit {
	// #region Public Properties
	public regions: Region[] = [];
	public filteredRegions: Region[] = [];
	public isLoading: boolean = true;
	public error?: string;
	public searchTerm: string = '';
	public sort: 'nameAsc' | 'nameDesc' = 'nameAsc';
	// #endregion

	// #region Private Properties
	private readonly regionService: RegionService = inject(RegionService);
	private readonly auth: AuthService = inject(AuthService);
	// #endregion

	// #region Public Methods
	public ngOnInit(): void {
		this.regionService.list().subscribe({
			next: (items: Region[]) => {
				this.regions = items;
				this.applyFilters();
				this.isLoading = false;
			},
			error: () => {
				this.error = 'Failed to load regions';
				this.isLoading = false;
			}
		});
	}
	public isGlobal(): boolean {
		return this.auth.currentUser()?.accessLevel === AccessLevel.Global;
	}
	public viewAsRegion(region: Region): void {
		if (!this.isGlobal()) return;
		this.auth.enterViewAsRegion(region.id);
	}
	public onSearchTerm(term: string): void {
		this.searchTerm = term;
		this.applyFilters();
	}
	public onSortChange(value: 'nameAsc' | 'nameDesc'): void {
		this.sort = value;
		this.applyFilters();
	}
	// #endregion

	// #region Private Methods
	private applyFilters(): void {
		const term = this.searchTerm.trim().toLowerCase();
		let next = [...this.regions];
		if (term) {
			next = next.filter((r: Region) => {
				const name = r.name?.toLowerCase() || '';
				const address = r.address?.toLowerCase() || '';
				return name.includes(term) || address.includes(term);
			});
		}
		next.sort((a: Region, b: Region) => {
			const an = a.name?.toLowerCase() || '';
			const bn = b.name?.toLowerCase() || '';
			const cmp = an.localeCompare(bn);
			return this.sort === 'nameAsc' ? cmp : -cmp;
		});
		this.filteredRegions = next;
	}
	// #endregion
}

