import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot, UrlTree } from '@angular/router';
import { AuthService } from './auth.service';
import { AccessLevel } from '../models/access-level';

@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
	// #region Public Methods
	public constructor(private auth: AuthService, private router: Router) {}

	public canActivate(route: ActivatedRouteSnapshot, _state: RouterStateSnapshot): boolean | UrlTree {
		if (!this.auth.isLoggedIn()) {
			return this.router.parseUrl('/login');
		}
		const allowedRoles = (route.data?.['roles'] as string[] | undefined) ?? undefined;
		if (!allowedRoles) {
			return true;
		}
		const current = this.auth.currentUser();
		if (!current) {
			return this.router.parseUrl('/login');
		}
		const role = current.accessLevel as AccessLevel;
		return allowedRoles.includes(role) ? true : this.router.parseUrl('/login');
	}
	// #endregion
}

