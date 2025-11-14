import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { AccessLevel } from '../../models/access-level';
import { UserService } from '../../services/user.service';
import { User } from '../../models/user';
import { TranslateModule } from '@ngx-translate/core';

@Component({
	selector: 'app-login-page',
	standalone: true,
	imports: [CommonModule, FormsModule, RouterLink, TranslateModule],
	templateUrl: './login-page.component.html',
	styleUrls: ['./login-page.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class LoginPageComponent implements OnInit {
	// #region Public Properties
	public email: string = 'global@demo.local';
	public password: string = '';
	public name: string = 'Demo';
	public surname: string = 'User';
	public access: AccessLevel = AccessLevel.Global;
	public auth: AuthService = inject(AuthService);
	public users: User[] = [];
	// #endregion

	// #region Private Properties
	private readonly userService: UserService = inject(UserService);
	// #endregion

	// #region Public Methods
	public ngOnInit(): void {
		this.userService.list().subscribe(users => {
			this.users = users;
			// If no email set, default to first user for convenience
			if (!this.email && users.length > 0) {
				this.email = users[0].email;
			}
		});
	}

	// #region Public Methods
	public login(): void {
		const selected = this.users.find(u => u.email === this.email);
		if (selected) {
			this.auth.login({
				email: selected.email,
				name: selected.name,
				surname: selected.surname,
				accessLevel: selected.accessLevel,
				regionId: selected.regionId,
				schoolId: selected.schoolId
			});
			return;
		}
		// Fallback: manual entry (kept for flexibility)
		this.auth.login({ email: this.email, name: this.name, surname: this.surname, accessLevel: this.access });
	}
	// #endregion
}

