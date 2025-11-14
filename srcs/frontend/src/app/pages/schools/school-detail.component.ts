import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { SchoolService } from '../../services/school.service';
import { School } from '../../models/school';
import { AuthService } from '../../core/auth.service';
import { AccessLevel } from '../../models/access-level';
import { TranslateModule } from '@ngx-translate/core';

@Component({
	selector: 'app-school-detail',
	standalone: true,
	imports: [CommonModule, RouterLink, ReactiveFormsModule, TranslateModule],
	templateUrl: './school-detail.component.html',
	styleUrls: ['./school-detail.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class SchoolDetailComponent implements OnInit {
	// #region Public Properties
	public school?: School;
	public isLoading: boolean = true;
	public error?: string;
	public isEditing: boolean = false;
	public form?: FormGroup;
	public isSaving: boolean = false;
	// #endregion

	// #region Private Properties
	private readonly route: ActivatedRoute = inject(ActivatedRoute);
	private readonly schoolService: SchoolService = inject(SchoolService);
	private readonly auth: AuthService = inject(AuthService);
	private readonly fb: FormBuilder = inject(FormBuilder);
	// #endregion

	// #region Public Methods
	public ngOnInit(): void {
		const id = this.route.snapshot.paramMap.get('id') as string;
		this.schoolService.getById(id).subscribe({
			next: (s: School | undefined) => {
				this.school = s;
				this.isLoading = false;
				if (!s) this.error = 'School not found';
				if (s) this.buildForm(s);
			},
			error: () => {
				this.error = 'Failed to load school';
				this.isLoading = false;
			}
		});
	}
	public isGlobal(): boolean {
		return this.auth.currentUser()?.accessLevel === AccessLevel.Global;
	}
	public viewAsSchool(): void {
		if (!this.school || !this.isGlobal()) return;
		this.auth.enterViewAsSchool(this.school.id);
	}
	public enableEditing(): void {
		if (!this.school) return;
		this.isEditing = true;
	}
	public cancelEditing(): void {
		if (!this.school) return;
		this.isEditing = false;
		this.buildForm(this.school);
	}
	public save(): void {
		if (!this.school || !this.form || this.form.invalid) return;
		this.isSaving = true;
		const values = this.form.value as Partial<School>;
		this.schoolService.update(this.school.id, values).subscribe({
			next: (updated: School | undefined) => {
				if (updated) {
					this.school = { ...updated };
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
	private buildForm(s: School): void {
		this.form = this.fb.group({
			name: [s.name, [Validators.required, Validators.maxLength(120)]],
			address: [s.address, [Validators.required, Validators.maxLength(160)]],
			headmasterName: [s.headmasterName ?? '', [Validators.maxLength(120)]],
			contactEmail: [s.contactEmail ?? '', [Validators.email, Validators.maxLength(160)]],
			contactPhone: [s.contactPhone ?? '', [Validators.maxLength(40)]],
		});
	}
	// #endregion
}

