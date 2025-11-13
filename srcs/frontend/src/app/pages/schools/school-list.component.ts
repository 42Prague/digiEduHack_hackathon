import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { SchoolService } from '../../services/school.service';
import { School } from '../../models/school';
import { AuthService } from '../../core/auth.service';
import { AccessLevel } from '../../models/access-level';
import { TranslateModule } from '@ngx-translate/core';

@Component({
	selector: 'app-school-list',
	standalone: true,
	imports: [CommonModule, FormsModule, RouterLink, TranslateModule],
	templateUrl: './school-list.component.html',
	styleUrls: ['./school-list.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class SchoolListComponent implements OnInit {
	// #region Public Properties
	public schools: School[] = [];
	public filteredSchools: School[] = [];
	public isLoading: boolean = true;
	public regionFilter?: string;
	public searchTerm: string = '';
	public sort: 'nameAsc' | 'nameDesc' = 'nameAsc';
	// #endregion

	// #region Private Properties
	private readonly schoolService: SchoolService = inject(SchoolService);
	private readonly auth: AuthService = inject(AuthService);
	// #endregion

	// #region Public Methods
	public ngOnInit(): void {
		const current = this.auth.currentUser();
		const regionId = current?.regionId;
		this.regionFilter = regionId || undefined;
		this.schoolService.list(regionId).subscribe((res: School[]) => {
			this.schools = res;
			this.applyFilters();
			this.isLoading = false;
		});
	}
	public isGlobal(): boolean {
		return this.auth.currentUser()?.accessLevel === AccessLevel.Global;
	}
	public isRegion(): boolean {
		return this.auth.currentUser()?.accessLevel === AccessLevel.Region;
	}
	public viewAsSchool(school: School): void {
		if (!this.isGlobal()) return;
		this.auth.enterViewAsSchool(school.id);
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
		let next = [...this.schools];
		// Region filter (if present)
		if (this.regionFilter) {
			next = next.filter((s: School) => s.regionId === this.regionFilter);
		}
		// Text search
		if (term) {
			next = next.filter((s: School) => {
				const name = s.name?.toLowerCase() || '';
				const address = s.address?.toLowerCase() || '';
				return name.includes(term) || address.includes(term);
			});
		}
		// Sort
		next.sort((a: School, b: School) => {
			const an = a.name?.toLowerCase() || '';
			const bn = b.name?.toLowerCase() || '';
			const cmp = an.localeCompare(bn);
			return this.sort === 'nameAsc' ? cmp : -cmp;
		});
		this.filteredSchools = next;
	}
	// #endregion
}

