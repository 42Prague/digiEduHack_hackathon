import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { UserService } from '../../services/user.service';
import { User } from '../../models/user';
import { AccessLevel } from '../../models/access-level';
import { TranslateModule } from '@ngx-translate/core';

@Component({
	selector: 'app-user-detail',
	standalone: true,
	imports: [CommonModule, RouterLink, ReactiveFormsModule, TranslateModule],
	templateUrl: './user-detail.component.html',
	styleUrls: ['./user-detail.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class UserDetailComponent implements OnInit {
	// #region Public Properties
	public user?: User;
	public isLoading: boolean = true;
	public error?: string;
	public isEditing: boolean = false;
	public isSaving: boolean = false;
	public form?: FormGroup;
	// #endregion

	// #region Private Properties
	private readonly route: ActivatedRoute = inject(ActivatedRoute);
	private readonly userService: UserService = inject(UserService);
	private readonly fb: FormBuilder = inject(FormBuilder);
	// #endregion

	// #region Public Methods
	public ngOnInit(): void {
		const id = this.route.snapshot.paramMap.get('id') as string;
		this.userService.getById(id).subscribe({
			next: (u: User | undefined) => {
				this.user = u;
				this.isLoading = false;
				if (!u) {
					this.error = 'User not found';
				} else {
					this.buildForm(u);
				}
			},
			error: () => {
				this.error = 'Failed to load user';
				this.isLoading = false;
			}
		});
	}
	public enableEditing(): void {
		if (!this.user) return;
		this.isEditing = true;
	}
	public cancelEditing(): void {
		if (!this.user) return;
		this.isEditing = false;
		this.buildForm(this.user);
	}
	public save(): void {
		if (!this.user || !this.form || this.form.invalid) return;
		this.isSaving = true;
		const values = this.form.value as Partial<User>;
		this.userService.update(this.user.id, values).subscribe({
			next: (updated: User | undefined) => {
				if (updated) {
					this.user = { ...updated };
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
	private buildForm(u: User): void {
		this.form = this.fb.group({
			name: [u.name, [Validators.required, Validators.maxLength(120)]],
			surname: [u.surname, [Validators.required, Validators.maxLength(120)]],
			email: [u.email, [Validators.required, Validators.email, Validators.maxLength(160)]],
			accessLevel: [u.accessLevel, [Validators.required]],
			regionId: [u.regionId ?? '', [Validators.maxLength(64)]],
			schoolId: [u.schoolId ?? '', [Validators.maxLength(64)]],
		});
	}
	// #endregion
}

