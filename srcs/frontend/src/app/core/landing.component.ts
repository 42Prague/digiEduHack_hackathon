import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from './auth.service';
import { AccessLevel } from '../models/access-level';
import { TranslateModule } from '@ngx-translate/core';

@Component({
	selector: 'app-landing',
	standalone: true,
	imports: [CommonModule, TranslateModule],
	template: '<div>{{ "common.redirecting" | translate }}</div>',
	changeDetection: ChangeDetectionStrategy.OnPush
})
export class LandingComponent implements OnInit {
	// #region Private Properties
	private readonly auth: AuthService = inject(AuthService);
	private readonly router: Router = inject(Router);
	// #endregion

	// #region Public Methods
	public ngOnInit(): void {
		const user = this.auth.currentUser();
		if (!user) {
			void this.router.navigateByUrl('/login');
			return;
		}
		if (user.accessLevel === AccessLevel.School) {
			void this.router.navigateByUrl('/overview/school');
			return;
		}
		if (user.accessLevel === AccessLevel.Region) {
			void this.router.navigateByUrl('/overview/region');
			return;
		}
		// Global → Global Overview
		void this.router.navigateByUrl('/overview/global');
	}
	// #endregion
}


