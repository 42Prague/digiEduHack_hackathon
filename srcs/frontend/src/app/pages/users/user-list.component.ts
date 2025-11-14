import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
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
	// #endregion

	// #region Private Properties
	private readonly userService: UserService = inject(UserService);
	// #endregion

	// #region Public Methods
	public ngOnInit(): void {
		this.userService.list().subscribe((res: User[]) => {
			this.users = res;
			this.isLoading = false;
		});
	}
	// #endregion
}

