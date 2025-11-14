import { ChangeDetectionStrategy, Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { UserService } from '../../services/user.service';
import { User } from '../../models/user';
import { TranslateModule } from '@ngx-translate/core';

@Component({
	selector: 'app-user-list',
	standalone: true,
	imports: [CommonModule, RouterLink, TranslateModule],
	templateUrl: './user-list.component.html',
	styleUrls: ['./user-list.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class UserListComponent implements OnInit {
	// #region Public Properties
	public users: User[] = [];
	public isLoading: boolean = true;
	public error?: string;
	// #endregion

	// #region Private Properties
	private readonly userService: UserService = inject(UserService);
	private readonly cdr: ChangeDetectorRef = inject(ChangeDetectorRef);
	// #endregion

	// #region Public Methods
	public ngOnInit(): void {
		this.userService.list().subscribe({
			next: (res: User[]) => {
				this.users = res;
				this.isLoading = false;
				this.cdr.markForCheck();
			},
			error: () => {
				this.error = 'Failed to load users';
				this.isLoading = false;
				this.cdr.markForCheck();
			}
		});
	}
	// #endregion
}

