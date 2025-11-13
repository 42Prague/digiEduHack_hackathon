import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from './core/auth.service';
import { AccessLevel } from './models/access-level';
import { animate, group, query, style, transition, trigger } from '@angular/animations';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

@Component({
	selector: 'app-root',
	standalone: true,
	imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, TranslateModule],
	templateUrl: './app.component.html',
	styleUrls: ['./app.component.css'],
	changeDetection: ChangeDetectionStrategy.OnPush,
	animations: [
		trigger('routeAnimations', [
			transition('* <=> *', [
				// set up stacking context to smoothly cross-fade
				query(':leave', [
					style({ position: 'absolute', left: 0, right: 0, width: '100%' })
				], { optional: true }),
				group([
					query(':leave', [
						animate('150ms ease', style({ opacity: 0 }))
					], { optional: true }),
					query(':enter', [
						style({ opacity: 0 }),
						animate('250ms ease', style({ opacity: 1 }))
					], { optional: true })
				])
			])
		])
	]
})
export class AppComponent {
	// #region Public Properties
	public title: string = 'DigiEdu Admin';
	public auth: AuthService = inject(AuthService);
	// #endregion
	// #region Private Properties
	private readonly translate: TranslateService = inject(TranslateService);
	// #endregion

	// #region Public Methods
	public getRouteAnimationState(outlet: RouterOutlet): string {
		if (!outlet || !outlet.isActivated) {
			return '';
		}
		const route = outlet.activatedRoute;
		return route.snapshot?.routeConfig?.path || '';
	}
	public isGlobal(): boolean {
		return this.auth.currentUser()?.accessLevel === AccessLevel.Global;
	}
	public isRegion(): boolean {
		return this.auth.currentUser()?.accessLevel === AccessLevel.Region;
	}
	public isSchool(): boolean {
		return this.auth.currentUser()?.accessLevel === AccessLevel.School;
	}
	public isViewAs(): boolean {
		return this.auth.isViewAs();
	}
	public exitViewAs(): void {
		this.auth.exitViewAs();
	}
	public logout(): void {
		this.auth.logout();
	}
	public setLanguage(lang: string): void {
		const normalized = lang === 'cs' ? 'cs' : 'en';
		localStorage.setItem('lang', normalized);
		this.translate.use(normalized).subscribe();
	}
	public currentLang(): string {
		return (this.translate.currentLang || this.translate.getDefaultLang() || 'en').toLowerCase();
	}
	// #endregion
}

